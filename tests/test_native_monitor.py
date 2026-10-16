import copy
import concurrent.futures
import datetime
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sqlite3
import uuid
import sys
import tempfile
import threading
import time
import unittest
from unblock.client import private_write
from unblock.store import DomainError
try:
    from unblock.native_monitor import NativeMonitor
except ImportError:NativeMonitor=None

WID='11111111-1111-4111-a111-111111111111'
REV='22222222-2222-4222-a222-222222222222'
OBS='33333333-3333-4333-a333-333333333333'

class FixtureClient:
    url='https://dashboard.invalid'
    def __init__(self):
        self.now=1000;self.deadline=1010;self.fail=False;self.status=503;self.mode='visible';self.calls=[];self.accepted=[];self.visible=[];self.foreign=False
        self.me={'kind':'listener','id':'monitor','environment':'here','agent_ids':['alpha']}
    def observation(self):
        return {'id':OBS,'agent_id':'alpha','kind':'overdue','expectation_id':WID,'payload':{'revision':REV,'next_update_at':self.deadline,'observer':'monitor','observer_kind':'listener','environment':'here','condition':'expected_update_missing'}}
    def call(self,op,data=None):
        if self.fail:raise DomainError('source unavailable',self.status)
        if op=='identity':return copy.deepcopy(self.me)
        if op=='attention':
            revision={'id':REV,'payload':{'status':'working','next_update_at':self.deadline,'environment':'here','parents':[]}}
            row={'id':WID,'agent_id':'beta' if self.foreign else 'alpha','environment':'here','history':[revision],'revisions':[revision],'observations':copy.deepcopy(self.visible),'current_observations':copy.deepcopy(self.visible),'state':'investigate' if self.visible else 'due' if self.deadline<=self.now else 'working'}
            return {'source':'checked','principal':copy.deepcopy(self.me),'requests':[],'expectations':[row],'checked_at':datetime.datetime.fromtimestamp(self.now,datetime.timezone.utc).isoformat()}
        if op=='observe_due':
            self.calls.append(copy.deepcopy(data))
            if self.mode=='reject':raise DomainError('native_operation_rejected',400)
            self.accepted=[self.observation()]
            if self.mode=='fail_after_write':self.fail=True;raise DomainError('lost source after ingest',503)
            if self.mode=='visible':self.publish()
            return {'record_id':OBS,'expectation_id':WID,'visibility':'visible' if self.visible else 'pending'}
        raise AssertionError(op)
    def publish(self):self.visible=copy.deepcopy(self.accepted)

class NativeMonitorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(NativeMonitor,'Independent native monitor is missing')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.state=self.root/'monitor.db';self.client=FixtureClient()
    def monitor(self):return NativeMonitor(self.client,'here',self.state)

    def test_due_item_is_observed_once_and_replacement_reconciles_the_same_receipt(self):
        self.assertEqual(self.monitor().tick()['persisted'],0);self.assertEqual(self.client.calls,[])
        self.client.now=1011;found=self.monitor().tick();self.assertTrue(found['checked']);self.assertEqual(found['persisted'],1)
        self.assertEqual(self.client.calls,[{'expectation_id':WID,'revision':REV}])
        self.assertEqual(self.monitor().tick()['persisted'],1);self.assertEqual(len(self.client.calls),1)
        self.assertEqual(self.state.stat().st_mode&0o777,0o600)

    def test_pending_then_source_loss_preserves_earlier_known_work_and_body(self):
        self.client.now=1011;self.client.mode='pending';first=self.monitor().tick();self.assertEqual(first['pending_receipts'],1)
        body=copy.deepcopy(self.client.calls[0]);self.client.fail=True
        unknown=self.monitor().tick();self.assertFalse(unknown['checked']);self.assertEqual(unknown['pending_known'],1);self.assertEqual(unknown['pending_receipts'],1)
        self.client.fail=False;self.client.publish();result=self.monitor().tick();self.assertEqual(result['persisted'],1);self.assertEqual(result['pending_receipts'],0);self.assertEqual(self.client.calls,[body])

    def test_lost_write_reply_is_reconciled_from_actual_history_without_duplicate_post(self):
        self.client.now=1011;self.client.mode='fail_after_write';self.assertFalse(self.monitor().tick()['checked'])
        self.client.fail=False;self.client.mode='visible';self.client.publish()
        result=self.monitor().tick();self.assertTrue(result['checked']);self.assertEqual(result['persisted'],1);self.assertEqual(len(self.client.calls),1)

    def test_confirmed_evidence_disappearing_makes_source_unknown_without_forgetting_it(self):
        self.client.now=1011;self.assertEqual(self.monitor().tick()['persisted'],1);self.client.visible=[]
        result=self.monitor().tick();self.assertFalse(result['checked']);self.assertEqual(result['persisted'],1);self.assertEqual(result['pending_known'],1);self.assertEqual(len(self.client.calls),1)

    def test_rejected_retry_keeps_prior_uncertainty_and_can_later_read_back(self):
        self.client.now=1011;self.client.mode='pending';self.monitor().tick();original=copy.deepcopy(self.client.calls[0]);self.client.mode='reject'
        result=self.monitor().tick();self.assertEqual(result['receipt_errors'][0]['uncertain'],True);self.assertEqual(self.client.calls,[original,original])
        self.assertEqual(self.monitor().tick()['receipt_errors'][0]['uncertain'],True);self.assertEqual(len(self.client.calls),2)
        self.client.publish();result=self.monitor().tick();self.assertEqual(result['persisted'],1);self.assertEqual(result['receipt_errors'],[]);self.assertEqual(len(self.client.calls),2)

    def test_concurrent_late_rejection_cannot_erase_another_accepted_attempt(self):
        self.monitor().tick();self.client.now=1011;self.client.mode='pending';original=self.client.call;arrived=threading.Event();lock=threading.Lock();calls=[]
        def call(op,data=None):
            if op!='observe_due':return original(op,data)
            with lock:index=len(calls);calls.append(copy.deepcopy(data))
            if index==0:
                if not arrived.wait(5):raise AssertionError('Second monitor did not start')
                raise DomainError('late rejection',400)
            self.client.accepted=[self.client.observation()];arrived.set()
            return {'record_id':OBS,'expectation_id':WID,'visibility':'pending'}
        self.client.call=call
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(self.monitor().tick) for _ in range(2)]
            for future in futures:future.result(timeout=8)
        result=self.monitor().tick();self.assertTrue(result['receipt_errors'][0]['uncertain']);self.assertEqual(calls,[{'expectation_id':WID,'revision':REV}]*2)
        self.client.publish();self.assertEqual(self.monitor().tick()['persisted'],1)

    def test_concurrent_late_success_retains_receipt_after_rejection_and_restart(self):
        self.monitor().tick();self.client.now=1011;original=self.client.call;arrived=threading.Event();lock=threading.Lock();calls=[]
        def call(op,data=None):
            if op!='observe_due':return original(op,data)
            with lock:index=len(calls);calls.append(copy.deepcopy(data))
            if index==0:
                if not arrived.wait(5):raise AssertionError('Second attempt missing')
                raise DomainError('early rejection',400)
            arrived.set();deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                with sqlite3.connect(self.state) as db:status=db.execute('SELECT status FROM observation_journal').fetchone()[0]
                if status=='rejected':break
                time.sleep(.01)
            if status!='rejected':raise AssertionError('First attempt not rejected')
            self.client.accepted=[self.client.observation()]
            return {'record_id':OBS,'expectation_id':WID,'visibility':'pending'}
        self.client.call=call
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            futures=[pool.submit(self.monitor().tick) for _ in range(2)]
            for future in futures:future.result(timeout=8)
        with sqlite3.connect(self.state) as db:
            receipt,status,attempts,uncertain=db.execute('SELECT record_id,status,attempts,uncertain FROM observation_journal').fetchone()
        self.assertEqual(receipt,OBS);self.assertEqual(status,'rejected');self.assertEqual(attempts,2);self.assertTrue(uncertain)
        self.client.visible=[{**self.client.accepted[0],'id':'44444444-4444-4444-a444-444444444444'}]
        self.assertFalse(self.monitor().tick()['checked'])
        self.client.publish();self.assertEqual(self.monitor().tick()['persisted'],1)

    def test_pending_queue_rotates_so_later_due_items_receive_a_first_attempt(self):
        class ManyClient(FixtureClient):
            def call(self,op,data=None):
                if op=='attention':
                    result=super().call(op,data);template=result['expectations'][0];rows=[]
                    for i in range(65):
                        row=copy.deepcopy(template);row['id']=str(uuid.UUID(int=i+1));rows.append(row)
                    result['expectations']=rows;return result
                if op=='observe_due':
                    self.calls.append(copy.deepcopy(data))
                    return {'record_id':str(uuid.uuid5(uuid.NAMESPACE_URL,data['expectation_id'])),'expectation_id':data['expectation_id'],'visibility':'pending'}
                return super().call(op,data)
        client=ManyClient();client.now=1011
        for i in range(3):
            before=len(client.calls);result=NativeMonitor(client,'here',self.state).tick();self.assertTrue(result['checked']);self.assertLessEqual(len(client.calls)-before,32)
        self.assertEqual(len({c['expectation_id'] for c in client.calls}),65);self.assertEqual(result['pending_receipts'],65)
        before=copy.deepcopy(client.calls);NativeMonitor(client,'here',self.state).tick()
        self.assertTrue(all(c in before for c in client.calls[len(before):]))

    def test_overlapping_older_snapshot_cannot_forget_newly_known_work(self):
        self.monitor().tick();original=self.client.call;two=False;arrived=threading.Event();release=threading.Event()
        def call(op,data=None):
            result=original(op,data)
            if op=='attention' and two:
                second=copy.deepcopy(result['expectations'][0]);second['id']='55555555-5555-4555-a555-555555555555';result['expectations'].append(second)
            return result
        self.client.call=call
        class OlderMonitor(NativeMonitor):
            def _reconcile(inner,rows,me):
                arrived.set()
                if not release.wait(5):raise AssertionError('Newer snapshot missing')
                return super()._reconcile(rows,me)
        with concurrent.futures.ThreadPoolExecutor(1) as pool:
            old=pool.submit(OlderMonitor(self.client,'here',self.state).tick);self.assertTrue(arrived.wait(5));two=True
            self.assertEqual(self.monitor().tick()['pending_known'],2);two=False;release.set();result=old.result(timeout=8)
        self.assertFalse(result['checked']);self.assertEqual(result['pending_known'],2)
        self.assertFalse(self.monitor().tick()['checked'])

    def test_revocation_foreign_source_and_rebinding_never_erase_known_work(self):
        self.monitor().tick();self.client.fail=True;self.client.status=401
        result=self.monitor().tick();self.assertFalse(result['checked']);self.assertEqual(result['pending_known'],1)
        self.client.fail=False;self.client.foreign=True;self.assertFalse(self.monitor().tick()['checked'])
        self.client.foreign=False;self.client.url='https://another.invalid'
        with self.assertRaises(ValueError):self.monitor().tick()
        self.client.url='https://dashboard.invalid';self.client.me['agent_ids']=['beta']
        with self.assertRaises(ValueError):self.monitor().tick()
        self.client.me['agent_ids']=['alpha'];self.client.me['environment']='elsewhere'
        with self.assertRaises(ValueError):self.monitor().tick()

    def test_untrusted_ledger_is_rejected_without_changing_its_target(self):
        victim=self.root/'victim';victim.write_bytes(b'leave this file intact');victim.chmod(0o600);self.state.symlink_to(victim)
        with self.assertRaises(ValueError):self.monitor()
        self.assertEqual(victim.read_bytes(),b'leave this file intact');self.state.unlink();self.state.write_bytes(b'public');self.state.chmod(0o644)
        with self.assertRaises(ValueError):self.monitor()
        self.assertEqual(self.state.read_bytes(),b'public')

    def test_separate_real_process_checks_a_later_deadline_without_any_worker_session(self):
        fixture=self.client;fixture.now=time.time();fixture.deadline=int(time.time())+2
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def send(self,data,status=200):
                body=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def do_GET(self):
                fixture.now=time.time()
                if self.headers.get('Authorization')!='Bearer fixture-listener':self.send({},401);return
                self.send(fixture.call(self.path.rsplit('/',1)[-1]))
            def do_POST(self):
                fixture.now=time.time();data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));self.send(fixture.call(self.path.rsplit('/',1)[-1],data))
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        profile=self.root/'listener.json';private_write(profile,{'transport':'fulcra-native','url':f'http://127.0.0.1:{server.server_port}','token':'fixture-listener'})
        result=subprocess.run([sys.executable,'-m','unblock.native_monitor','--config',str(profile),'--environment','here','--state',str(self.state),'--interval','1','--duration','4'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);rows=[json.loads(x) for x in result.stdout.splitlines() if x];self.assertEqual(rows[0]['persisted'],0);self.assertEqual(rows[-1]['persisted'],1);self.assertEqual(len(fixture.calls),1)

if __name__=='__main__':unittest.main()
