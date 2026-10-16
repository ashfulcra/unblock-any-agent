import concurrent.futures
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unblock.client import private_write
from unblock.store import DomainError
try:
    from unblock.native_listener import NativeListener
except ImportError:
    NativeListener=None

RID='00000000-0000-4000-8000-000000000001'
REV='00000000-0000-4000-8000-000000000002'
ANSWER='00000000-0000-4000-8000-000000000003'

class FixtureClient:
    url="https://dashboard-a.invalid"
    def __init__(self,path):
        self.path=path;self.fail=False;self.receipts=[];self.fail_code=503;self.fail_receipt=False
        self.identity={'kind':'listener','id':'receiver','environment':'here','agent_ids':['alpha']}
    def call(self,operation,data=None):
        if self.fail:raise DomainError('source_unavailable',self.fail_code)
        if operation=='identity':return copy.deepcopy(self.identity)
        if operation=='delivery':
            if self.fail_receipt:
                self.fail=True;raise DomainError('revoked',self.fail_code)
            self.receipts.append(data);return {'record_id':'receipt','visibility':'visible'}
        rows=json.loads(self.path.read_text())
        if operation=='recover':rows=[r for r in rows if r['id']==data['request_id']]
        return {'principal':copy.deepcopy(self.identity),'source':'checked','requests':rows}

class NativeListenerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(NativeListener,'Native environment listener is missing')
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.source=self.root/'source.json';self.routes=self.root/'routes.json';self.state=self.root/'ledger.db'
        self.row={'id':RID,'agent_id':'alpha','state':'needs_you','revisions':[{'id':REV}],'answers':[], 'progress':[], 'actions':[], 'settlements':[]}
        self.save();self.client=FixtureClient(self.source)
        self.route={'argv':[sys.executable,'-c','import sys; sys.stdin.read()'],'cwd':str(Path.cwd()),'timeout':3}
        private_write(self.routes,{'alpha':self.route})
    def save(self):self.source.write_text(json.dumps([self.row]))
    def answer(self):self.row['answers']=[{'id':ANSWER}];self.row['state']='awaiting_pickup';self.save()
    def listener(self):return NativeListener(self.client,'here',self.routes,self.state,retry_after=0)

    def test_delayed_answer_runs_real_subprocess_and_replacement_observes_progress(self):
        self.assertEqual(self.listener().tick()['attempts'],[])
        script='import json,pathlib,sys; p=json.load(sys.stdin); f=pathlib.Path('+repr(str(self.source))+'); rows=json.loads(f.read_text()); rows[0]["progress"]=[{"id":"fresh","payload":{"stage":"resumed"}}]; rows[0]["state"]="resumed"; f.write_text(json.dumps(rows))'
        self.routes.write_text(json.dumps({'alpha':{**self.route,'argv':[sys.executable,'-c',script]}}))
        self.answer();tick=self.listener().tick()
        self.assertEqual(tick['attempts'][0]['result'],'resumed')
        self.assertEqual(self.client.receipts[-1]['disposition'],'queued')
        self.assertEqual(self.listener().tick()['attempts'],[])

    def test_queued_is_not_acknowledged_and_retries_are_bounded(self):
        self.answer();listener=self.listener()
        for _ in range(3):self.assertEqual(listener.tick()['attempts'][0]['result'],'queued')
        result=listener.tick();self.assertEqual(result['attempts'],[])
        self.assertEqual(result['errors'][0]['code'],'retry_limit_repair_route_or_reconcile')
        self.assertEqual(json.loads(self.source.read_text())[0]['progress'],[])
        self.client.fail=True;result=listener.tick()
        self.assertFalse(result['checked']);self.assertEqual(result['pending_known'],1)

    def test_multi_item_authorization_or_source_loss_stops_the_dispatch_batch(self):
        self.answer();neighbor=copy.deepcopy(self.row);neighbor['id']='00000000-0000-4000-8000-000000000009'
        self.source.write_text(json.dumps([self.row,neighbor]))
        for status in (401,503):
            for boundary in ('post_dispatch','receipt'):
                client=FixtureClient(self.source);client.fail_code=status
                listener=NativeListener(client,'here',self.routes,self.root/f'{status}-{boundary}.db',retry_after=0);launched=[]
                def run(route,payload):
                    launched.append(payload['request_id'])
                    if boundary=='post_dispatch':client.fail=True
                    else:client.fail_receipt=True
                    return 'queued'
                listener._run=run;result=listener.tick()
                self.assertEqual(launched,[RID],f'{status} at {boundary} must stop all subsequent launches')
                self.assertFalse(result['checked']);self.assertEqual(result['pending_known'],2)
                with listener.ledger() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM receipt_outbox').fetchone()[0],1)

    def test_source_origin_change_preserves_old_ledger_and_does_not_dispatch(self):
        self.answer();first=self.listener();first.tick()
        with first.ledger() as db:before=db.execute('SELECT * FROM attempts').fetchall()
        self.client.url='https://dashboard-b.invalid'
        with self.assertRaises(ValueError):self.listener().tick()
        with first.ledger() as db:self.assertEqual(db.execute('SELECT * FROM attempts').fetchall(),before)

    def test_rejected_receipt_is_retained_without_blocking_unrelated_work(self):
        self.answer();listener=self.listener();original=self.client.call;receipt_status=503
        def call(operation,data=None):
            if operation=='delivery' and data['intent_id']=='poisoned':raise DomainError('native_operation_rejected',receipt_status)
            return original(operation,data)
        self.client.call=call
        body={'intent_id':'poisoned','request_id':RID,'revision':REV,'answers':[ANSWER],'disposition':'queued','evidence':'A rejected receipt may have an earlier uncertain attempt'}
        with listener.ledger() as db:db.execute('INSERT INTO receipt_outbox VALUES (?,?)',('poisoned',json.dumps(body)))
        self.assertFalse(listener.tick()['checked'])
        receipt_status=400
        result=listener.tick();self.assertTrue(result['checked']);self.assertEqual(result['attempts'][0]['result'],'queued')
        self.assertEqual(result['receipts_rejected'],1);self.assertTrue(result['receipt_errors'])
        with listener.ledger() as db:self.assertEqual(json.loads(db.execute('SELECT body FROM receipt_rejected').fetchone()[0]),body)
        self.assertTrue(listener.tick()['checked'])

    def test_acknowledged_without_continuation_does_not_suppress_all_future_pickup(self):
        self.answer();listener=self.listener()
        def acknowledge(route,payload):
            self.row['state']='acknowledged';self.row['progress']=[{'id':'seen','payload':{'stage':'acknowledged'}}];self.save();return 'queued'
        listener._run=acknowledge
        self.assertEqual(listener.tick()['attempts'][0]['result'],'acknowledged')
        self.assertTrue(listener.tick()['attempts'],'Acknowledgment alone must not leave work waiting forever')

    def test_launcher_exit_stops_remaining_children_before_claim_release(self):
        self.answer();late=self.root/'late-effect'
        child='import time,pathlib; time.sleep(.4); pathlib.Path('+repr(str(late))+').touch()'
        script='import subprocess,sys; subprocess.Popen([sys.executable,"-c",'+repr(child)+'])'
        self.routes.write_text(json.dumps({'alpha':{**self.route,'argv':[sys.executable,'-c',script]}}))
        self.listener().tick();time.sleep(.6)
        self.assertFalse(late.exists(),'A launcher exit must not leave children running after claim release')

    def test_wrong_role_environment_and_foreign_source_fail_closed(self):
        for key,value in [('kind','agent'),('environment','elsewhere')]:
            old=self.client.identity[key];self.client.identity[key]=value
            with self.assertRaises(ValueError):self.listener().tick()
            self.client.identity[key]=old
        self.answer();self.listener().tick()
        self.row['agent_id']='neighbor';self.save()
        with self.assertRaises(ValueError):self.listener().tick()
        self.row['agent_id']='alpha';self.save();self.client.identity['agent_ids']=['alpha','neighbor']
        with self.assertRaises(ValueError):self.listener().tick()

    def test_active_and_expired_claims_need_reconciliation(self):
        self.answer();listener=self.listener()
        with listener.ledger() as db:db.execute('INSERT INTO claims VALUES (?,?,?)',(RID,'old',time.time()+60))
        with self.assertRaises(ValueError):listener.recover(RID,'Prior process might be running')
        with listener.ledger() as db:db.execute('UPDATE claims SET lease_until=?',(time.time()-1,))
        self.assertEqual(listener.tick()['errors'][0]['code'],'dispatch_recovery_required')
        with self.assertRaises(ValueError):listener.recover(RID,'')
        listener.recover(RID,'Verified process stopped and no uncertain effects remain')
        self.assertEqual(listener.tick()['attempts'][0]['result'],'queued')

    def test_simultaneous_checks_never_overlap_and_old_progress_is_not_fresh(self):
        self.answer();listener=self.listener();started=self.root/'started';release=self.root/'release'
        script='import pathlib,time; p=pathlib.Path('+repr(str(started))+'); p.touch(); r=pathlib.Path('+repr(str(release))+'); end=time.monotonic()+3\nwhile not r.exists() and time.monotonic()<end: time.sleep(.01)'
        self.routes.write_text(json.dumps({'alpha':{**self.route,'argv':[sys.executable,'-c',script]}}))
        self.row['progress']=[{'id':'old','payload':{'stage':'acknowledged'}}];self.save()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(listener.tick)
            deadline=time.monotonic()+2
            while not started.exists() and time.monotonic()<deadline:time.sleep(.01)
            self.assertTrue(started.exists())
            second=self.listener().tick();release.touch();result=first.result(timeout=4)
        self.assertEqual(second['attempts'],[]);self.assertEqual(second['errors'][0]['code'],'worker_active')
        self.assertEqual(result['attempts'][0]['result'],'queued')

if __name__=='__main__':unittest.main()
