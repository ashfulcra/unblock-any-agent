import concurrent.futures
import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
import uuid
from unittest.mock import patch
from unblock.client import private_read,private_write
from unblock.store import DomainError
try:
    from unblock.native_renewal import Renewal,replace_private
except ImportError:
    Renewal=None;replace_private=None

try:
    from unblock.native_renewal import prepare_operator
except ImportError:
    prepare_operator=None

ANCHOR='11111111-1111-4111-8111-111111111111'

class OwnerFixture:
    url='https://fixture.invalid'
    def __init__(self):
        self.clock=1000;self.owner_id='owner';self.lose=False;self.offline=False;self.calls=[];self.accepted=[];self.block=None
        self.grants=[{'grant_id':ANCHOR,'record_id':'anchor-record','agent_id':'alpha','name':'Alpha','kind':'agent','environment':'here','agent_ids':['alpha'],'expires_at':1005,'revoked':False}]
    def publish(self):self.grants.extend(g for g in self.accepted if not any(v['record_id']==g['record_id'] for v in self.grants))
    def call(self,operation,data=None):
        if self.offline:raise DomainError('unavailable',503)
        if operation=='identity':return {'kind':'owner','id':self.owner_id}
        if operation=='attention':return {'source':'checked','principal':{'kind':'owner','id':self.owner_id},'grants':copy.deepcopy(self.grants)}
        if operation=='prepare_enrollment':return {'expires_at':self.clock+3600}
        if operation!='enroll':raise AssertionError('Unexpected owner operation')
        if data['expires_at']<=self.clock:raise DomainError('expired_body',400)
        self.calls.append(copy.deepcopy(data))
        if self.block:self.block[0].set();self.block[1].wait(3)
        gid=str(uuid.uuid5(uuid.NAMESPACE_URL,data['agent_id']+data['intent_id']));rid=str(uuid.uuid5(uuid.NAMESPACE_URL,json.dumps(data,sort_keys=True)))
        grant={**data,'record_id':rid,'grant_id':gid,'revoked':False}
        if not any(g['record_id']==rid for g in self.accepted):self.accepted.append(grant)
        if self.lose:self.lose=False;raise DomainError('response_lost',503)
        return {**grant,'credential':'sealed-'+gid,'visibility':'visible' if any(g['record_id']==rid for g in self.grants) else 'pending'}

class NativeRenewalTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Renewal,'Bounded renewal operator is missing')
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name);self.config=self.root/'operator.json';self.state=self.root/'state.json';self.profile=self.root/'agent.json';self.owner=OwnerFixture()
        private_write(self.profile,{'transport':'fulcra-native','url':self.owner.url,'token':'original'})
        private_write(self.config,{'url':self.owner.url,'enrollments':[{'anchor_grant_id':ANCHOR,'profile':str(self.profile)}]})
    def renewal(self):return Renewal(self.owner,self.config,self.state,lease_seconds=60,renew_before=30,now=lambda:self.owner.clock)
    def make_visible(self):self.renewal().tick();self.owner.publish();return self.renewal().tick()

    def test_pending_and_lost_response_retries_keep_one_intent_expiry_and_original_profile(self):
        self.owner.lose=True;result=self.renewal().tick();self.assertFalse(result['checked']);self.assertEqual(private_read(self.profile)['token'],'original')
        first=self.owner.calls[0];self.owner.clock+=7
        self.assertEqual(self.renewal().tick()['pending'],1);self.assertEqual(self.owner.calls[-1],first);self.assertEqual(len(self.owner.accepted),1)
        self.owner.publish();result=self.renewal().tick();self.assertEqual(result['renewed'],1)
        profile=private_read(self.profile);self.assertTrue(profile['token'].startswith('sealed-'));self.assertEqual(profile['expires_at'],first['expires_at'])
        self.assertEqual(self.renewal().tick()['renewed'],0)
        self.owner.offline=True;result=self.renewal().tick();self.assertFalse(result['checked']);self.assertEqual(private_read(self.profile),profile)

    def test_preparation_uses_verified_connection_grants_without_manual_internal_ids(self):
        self.assertIsNotNone(prepare_operator,'Operator preparation helper missing')
        identity={'id':'alpha','kind':'agent','environment':'here','agent_ids':['alpha'],'grant_id':ANCHOR,'expires_at':1005}
        destination=self.root/'prepared.json'
        with patch('unblock.native_client.NativeClient.call',return_value=identity) as lookup:
            result=prepare_operator(self.owner,[self.profile],destination)
            lookup.assert_called_once_with('enrollment')
        self.assertTrue(result['prepared']);self.assertFalse(result['operator_started'])
        self.assertEqual(private_read(destination),{'url':self.owner.url,'owner_id':'owner','enrollments':[{'anchor_grant_id':ANCHOR,'profile':str(self.profile)}]});self.assertEqual(self.owner.calls,[])
        denied=self.root/'denied.json'
        with patch('unblock.native_client.NativeClient.call',return_value={**identity,'id':'neighbor'}):
            with self.assertRaises(DomainError):prepare_operator(self.owner,[self.profile],denied)
        self.assertFalse(denied.exists())

    def test_expired_pending_readback_is_reconciled_before_a_new_intent(self):
        self.owner.lose=True;self.renewal().tick();first=self.owner.calls[0];self.owner.clock+=70
        pending=self.renewal().tick();self.assertTrue(pending['checked']);self.assertEqual(pending['pending'],1);self.assertTrue(pending['errors']);self.assertEqual(len(self.owner.calls),1)
        self.owner.publish();reconciled=self.renewal().tick();self.assertTrue(reconciled['checked']);self.assertEqual(private_read(self.profile)['token'],'original')
        retry=self.renewal().tick();self.assertTrue(retry['checked']);self.assertNotEqual(self.owner.calls[-1]['intent_id'],first['intent_id']);self.assertGreater(self.owner.calls[-1]['expires_at'],self.owner.clock)
        state=private_read(self.state);self.assertEqual(state['entries'][ANCHOR]['expired_visible'][0]['body'],first)

    def test_expired_visible_renewal_remains_the_predecessor_and_revocation_stops_it(self):
        self.owner.lose=True;self.renewal().tick();self.owner.publish();self.owner.clock+=70
        self.assertTrue(self.renewal().tick()['checked'])
        preceding=self.owner.accepted[0]
        self.assertEqual(private_read(self.state)['entries'][ANCHOR]['latest']['grant_id'],preceding['grant_id'])
        self.renewal().tick()
        self.assertEqual(self.owner.calls[-1]['renewal_of'],preceding['grant_id'])
        preceding['revoked']=True
        before=len(self.owner.calls);self.assertFalse(self.renewal().tick()['checked']);self.assertEqual(len(self.owner.calls),before)

    def test_expired_restart_after_profile_publication_reconciles_without_rewriting(self):
        self.renewal().tick();self.owner.publish()
        def interrupted(path,value):
            replace_private(path,value)
            if Path(path)==self.profile:raise OSError('Simulated process loss after atomic profile publication')
        with patch('unblock.native_renewal.replace_private',side_effect=interrupted):self.assertFalse(self.renewal().tick()['checked'])
        profile=private_read(self.profile);stamp=self.profile.stat().st_mtime_ns;self.owner.clock+=70
        self.assertTrue(self.renewal().tick()['checked'])
        self.assertEqual(private_read(self.profile),profile);self.assertEqual(self.profile.stat().st_mtime_ns,stamp)
        result=self.renewal().tick();self.assertTrue(result['checked']);self.assertEqual(result['pending'],1)
        self.assertEqual(self.owner.calls[-1]['renewal_of'],profile['grant_id'])
        self.owner.publish();self.assertEqual(self.renewal().tick()['renewed'],1)

    def test_revoked_connection_preserves_pending_without_starving_healthy_connection(self):
        second='22222222-2222-4222-8222-222222222222';other=self.root/'beta.json'
        private_write(other,{'transport':'fulcra-native','url':self.owner.url,'token':'beta-original'})
        self.owner.grants.append({**self.owner.grants[0],'grant_id':second,'record_id':'beta-anchor','agent_id':'beta','name':'Beta','agent_ids':['beta']})
        self.config.write_text(json.dumps({'url':self.owner.url,'enrollments':[{'anchor_grant_id':ANCHOR,'profile':str(self.profile)},{'anchor_grant_id':second,'profile':str(other)}]}))
        self.renewal().tick();pending=private_read(self.state)['entries'][ANCHOR]['pending'];self.owner.publish();self.owner.grants[0]['revoked']=True
        result=self.renewal().tick()
        self.assertFalse(result['checked']);self.assertEqual(result['renewed'],1);self.assertTrue(result['errors'])
        self.assertEqual(private_read(self.profile)['token'],'original');self.assertNotEqual(private_read(other)['token'],'beta-original')
        self.assertEqual(private_read(self.state)['entries'][ANCHOR]['pending'],pending)
        self.owner.clock+=40;self.owner.offline=True;before=len(self.owner.calls)
        self.assertFalse(self.renewal().tick()['checked']);self.assertEqual(len(self.owner.calls),before)

    def test_anchor_or_latest_revocation_stops_renewal_without_reenrolling(self):
        self.owner.grants[0]['revoked']=True;self.assertFalse(self.renewal().tick()['checked']);self.assertEqual(self.owner.calls,[])
        self.owner.grants[0]['revoked']=False;self.make_visible();profile=private_read(self.profile);before=len(self.owner.calls)
        next(g for g in self.owner.grants if g['grant_id']==profile['grant_id'])['revoked']=True;self.owner.clock+=40
        self.assertFalse(self.renewal().tick()['checked']);self.assertEqual(len(self.owner.calls),before);self.assertEqual(private_read(self.profile),profile)

    def test_owner_scope_and_target_changes_preserve_pending_instead_of_overwriting(self):
        self.renewal().tick();body=self.owner.calls[0];self.owner.publish();self.owner.grants[0]['environment']='neighbor'
        self.assertFalse(self.renewal().tick()['checked']);self.assertEqual(private_read(self.profile)['token'],'original')
        self.owner.grants[0]['environment']='here';self.owner.owner_id='different'
        self.assertFalse(self.renewal().tick()['checked'])
        self.owner.owner_id='owner';self.profile.write_text(json.dumps({'transport':'fulcra-native','url':self.owner.url,'token':'manually-replaced'}))
        self.assertFalse(self.renewal().tick()['checked']);self.assertEqual(private_read(self.profile)['token'],'manually-replaced');self.assertEqual(self.owner.calls[0],body)

    def test_unowned_or_symlink_profile_is_rejected_before_enrollment(self):
        self.profile.chmod(0o644)
        with self.assertRaises(ValueError):self.renewal().tick()
        self.profile.chmod(0o600);target=self.root/'target';self.profile.rename(target);self.profile.symlink_to(target)
        with self.assertRaises(ValueError):self.renewal().tick()
        self.assertEqual(self.owner.calls,[]);self.assertEqual(private_read(target)['token'],'original')

    def test_profile_aliases_cannot_overlap_another_profile_or_operator_state(self):
        duplicate={'url':self.owner.url,'enrollments':[{'anchor_grant_id':ANCHOR,'profile':str(self.profile)},{'anchor_grant_id':'22222222-2222-4222-8222-222222222222','profile':str(self.root/'sub'/ '..'/'agent.json')}]}
        (self.root/'sub').mkdir();self.config.write_text(json.dumps(duplicate))
        with self.assertRaises(ValueError):self.renewal()
        duplicate['enrollments']=[{'anchor_grant_id':ANCHOR,'profile':str(self.root/'sub'/'..'/'state.json')}];self.config.write_text(json.dumps(duplicate))
        with self.assertRaises(ValueError):self.renewal()

    def test_concurrent_operators_share_exclusive_state(self):
        started=threading.Event();release=threading.Event();self.owner.block=(started,release)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(self.renewal().tick);self.assertTrue(started.wait(2))
            try:second=self.renewal().tick()
            finally:release.set()
            first.result(timeout=4)
        self.assertFalse(second['checked']);self.assertEqual(second['error'],'operator_active');self.assertEqual(len(self.owner.calls),1)

    def test_crash_after_profile_replace_reconciles_without_overwriting_again(self):
        self.renewal().tick();self.owner.publish()
        def interrupted(path,value):
            replace_private(path,value)
            if Path(path)==self.profile:raise OSError('Simulated process loss after atomic profile publication')
        with patch('unblock.native_renewal.replace_private',side_effect=interrupted):self.assertFalse(self.renewal().tick()['checked'])
        profile=private_read(self.profile);stamp=self.profile.stat().st_mtime_ns
        result=self.renewal().tick();self.assertEqual(result['renewed'],1);self.assertEqual(private_read(self.profile),profile);self.assertEqual(self.profile.stat().st_mtime_ns,stamp);self.assertEqual(len(self.owner.accepted),1)

if __name__=='__main__':unittest.main()
