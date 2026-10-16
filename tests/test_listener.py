import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unblock.client import Client,private_write
from unblock.server import create_server
from unblock.store import Store
try:
    from unblock.listener import Listener
except ImportError:
    Listener=None

class ListenerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Listener,'Environment listener is missing')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.store=Store(self.root/'work.db');og=self.store.bootstrap_owner('Owner');self.owner=self.store.authenticate(og['token']);wid=self.store.create_workspace(self.owner,'Team')['id']
        self.agent_grant=self.store.enroll(self.owner,wid,'Worker','agent','here');self.agent=self.store.authenticate(self.agent_grant['token'])
        self.lg=self.store.enroll(self.owner,wid,'Listener','listener','here')
        self.server=create_server(self.store,port=0);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close_server)
        self.url=f'http://127.0.0.1:{self.server.server_port}';self.client=Client(self.url,self.lg['token'])
        self.config=self.root/'worker.json';private_write(self.config,{'url':self.url,**self.agent_grant})
        self.routes_path=self.root/'routes.json';self.output=self.root/'artifacts';self.state=self.root/'delivery.db'
        self.route={'argv':[sys.executable,'-m','unblock','--config',str(self.config),'demo-worker','--output',str(self.output)],'cwd':str(Path.cwd()),'timeout':10}
        self.routes={self.agent.id:self.route};private_write(self.routes_path,self.routes)
        self.work=self.store.request_help(self.agent,'listener-1','A or B?',{'goal':'Synthetic pickup proof','next_action':'Write the authorized local proof artifact'})

    def close_server(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def answer(self):return self.store.answer_request(self.owner,self.work['id'],self.work['revision'],'A','one')
    def listener(self,**kw):return Listener(self.client,'here',self.routes_path,self.state,**kw)
    def update_routes(self,value):self.routes_path.write_text(json.dumps(value));self.routes_path.chmod(0o600)

    def test_delayed_answer_routes_to_real_worker_and_is_not_redelivered(self):
        listener=self.listener();self.assertEqual(listener.tick()['attempts'],[])
        self.answer();tick=listener.tick()
        self.assertEqual(tick['attempts'][0]['result'],'resumed')
        work=self.store.get_request(self.agent,self.work['id']);self.assertEqual(work['status'],'resumed')
        self.assertEqual([p['state'] for p in work['progress']],['acknowledged','resumed'])
        self.assertEqual(len(list(self.output.iterdir())),1)
        self.assertEqual(self.listener().tick()['attempts'],[])

    def test_queued_delivery_is_not_worker_acknowledgment(self):
        self.update_routes({self.agent.id:{**self.route,'argv':[sys.executable,'-c','import sys; sys.stdin.read()']}})
        self.answer();tick=self.listener().tick()
        self.assertEqual(tick['attempts'][0]['result'],'queued')
        self.assertEqual(self.store.get_request(self.agent,self.work['id'])['progress'],[])
        self.assertEqual(self.listener().tick()['attempts'],[])
        self.assertEqual(self.listener(retry_after=0).tick()['attempts'][0]['result'],'queued')

    def test_failed_route_and_replacement_recover_after_restart(self):
        self.update_routes({self.agent.id:{**self.route,'argv':[sys.executable,'-c','raise SystemExit(7)']}})
        self.answer();self.assertEqual(self.listener().tick()['attempts'][0]['result'],'failed')
        self.assertEqual(self.store.get_request(self.agent,self.work['id'])['status'],'answered')
        self.update_routes(self.routes)
        self.assertEqual(self.listener().tick()['attempts'][0]['result'],'resumed')

    def test_other_environment_and_wrong_agent_are_not_dispatched(self):
        remote_grant=self.store.enroll(self.owner,self.agent.workspace_id,'Remote','agent','there');remote=self.store.authenticate(remote_grant['token'])
        work=self.store.request_help(remote,'remote','Private remote need',{})
        self.store.answer_request(self.owner,work['id'],work['revision'],'Yes','remote')
        self.assertEqual(self.listener().tick()['pending'],0)
        neighbor=self.store.enroll(self.owner,self.agent.workspace_id,'Neighbor','agent','here')
        neighbor_config=self.root/'neighbor.json';private_write(neighbor_config,{'url':self.url,**neighbor})
        wrong={**self.route,'argv':[sys.executable,'-m','unblock','--config',str(neighbor_config),'demo-worker','--output',str(self.output)]}
        self.update_routes({self.agent.id:wrong});self.answer()
        self.assertEqual(self.listener().tick()['attempts'][0]['result'],'failed')
        self.assertFalse(self.output.exists())
        self.assertEqual(self.store.get_request(self.agent,self.work['id'])['progress'],[])

    def test_failed_source_preserves_known_pending_and_cannot_claim_quiet(self):
        self.update_routes({});self.answer();self.listener().tick()
        self.store.revoke(self.owner,self.lg['id'])
        tick=self.listener().tick()
        self.assertFalse(tick['checked']);self.assertEqual(tick['pending_known'],1)
        self.assertEqual(tick['error'],'source_unavailable')

    def test_blocked_work_is_released_when_uncertain_action_is_settled(self):
        self.answer()
        action=self.store.declare_action(self.agent,self.work['id'],'pending','Verify external result')
        listener=self.listener(retry_after=0)
        self.assertEqual(listener.tick()['attempts'][0]['result'],'blocked')
        self.assertEqual(listener.tick()['attempts'],[])
        self.store.settle_action(self.agent,self.work['id'],action['id'],'Confirmed external result')
        attempts=listener.tick()['attempts']
        self.assertTrue(attempts,'Settling the prerequisite must release pickup')
        self.assertEqual(attempts[0]['result'],'resumed')

    def test_existing_invalid_artifact_cannot_prove_continuation(self):
        response=self.answer();self.output.mkdir(mode=0o700)
        artifact=self.output/f'{self.work["id"]}-{response["id"]}.json'
        for content in ('','{bad','{"synthetic":true,"decision":"wrong"}'):
            artifact.write_text(content);artifact.chmod(0o600)
            self.assertEqual(self.listener(retry_after=0).tick()['attempts'][0]['result'],'failed')
            self.assertEqual(self.store.get_request(self.agent,self.work['id'])['status'],'answered')

    def test_running_claim_blocks_second_listener_beyond_retry_interval(self):
        import concurrent.futures,time
        started=self.root/'started';release=self.root/'release'
        script='import pathlib,time; p=pathlib.Path('+repr(str(started))+'); p.write_text(p.read_text()+"x" if p.exists() else "x"); r=pathlib.Path('+repr(str(release))+'); end=time.monotonic()+5\nwhile not r.exists() and time.monotonic()<end: time.sleep(.02)'
        self.update_routes({self.agent.id:{**self.route,'argv':[sys.executable,'-c',script]}})
        self.answer()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(self.listener(retry_after=0).tick)
            deadline=time.monotonic()+3
            while not started.exists() and time.monotonic()<deadline:time.sleep(.01)
            self.assertTrue(started.exists())
            second=pool.submit(self.listener(retry_after=0).tick)
            time.sleep(.2)
            observed=started.read_text();release.touch()
            first.result(timeout=5);second.result(timeout=5)
        self.assertEqual(observed,'x','Second listener must not start an overlapping worker')

    def test_expired_dispatch_requires_reconciliation_before_retry(self):
        import time
        self.answer();listener=self.listener(retry_after=0)
        with listener.ledger() as db:
            db.execute('INSERT INTO claims VALUES (?,?,?)',(self.work['id'],'interrupted',time.time()-1))
        restarted=self.listener(retry_after=0)
        result=restarted.tick()
        self.assertEqual(result['attempts'],[])
        self.assertEqual(result['errors'][0]['code'],'dispatch_recovery_required')
        with self.assertRaises(ValueError):restarted.recover(self.work['id'],'')
        restarted.recover(self.work['id'],'Verified previous worker stopped; no artifact or external action occurred')
        self.assertEqual(restarted.tick()['attempts'][0]['result'],'resumed')
        with restarted.ledger() as db:
            self.assertEqual(db.execute('SELECT evidence FROM recoveries').fetchone()[0],'Verified previous worker stopped; no artifact or external action occurred')

    def test_active_claim_cannot_be_recovered_and_old_completion_cannot_clear_replacement(self):
        import time
        self.answer();listener=self.listener(retry_after=0)
        with listener.ledger() as db:
            db.execute('INSERT INTO claims VALUES (?,?,?)',(self.work['id'],'active',time.time()+60))
        with self.assertRaises(ValueError):listener.recover(self.work['id'],'Worker may still be alive')
        with listener.ledger() as db:db.execute('DELETE FROM claims')
        def replaced(route,payload):
            with listener.ledger() as db:
                db.execute('UPDATE claims SET claim_id=?',('replacement',))
            return 'queued'
        listener._run=replaced
        self.assertEqual(listener.tick()['attempts'][0]['result'],'claim_replaced_reconcile_required')
        with listener.ledger() as db:
            self.assertEqual(db.execute('SELECT claim_id FROM claims').fetchone()[0],'replacement')

    def test_tick_closes_delivery_database_connections(self):
        import gc, warnings
        self.answer()
        gc.collect()
        with warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter('always',ResourceWarning)
            self.listener().tick()
            gc.collect()
        self.assertEqual([str(w.message) for w in observed if issubclass(w.category,ResourceWarning)],[])

    def test_untrusted_route_file_and_bad_environment_rejected(self):
        self.routes_path.chmod(0o644)
        with self.assertRaises(ValueError):self.listener().tick()
        self.routes_path.chmod(0o600)
        with self.assertRaises(ValueError):Listener(self.client,'wrong',self.routes_path,self.state).tick()
        self.update_routes({self.agent.id:{**self.route,'shell':True}})
        with self.assertRaises(ValueError):self.listener().tick()

if __name__=='__main__':unittest.main()
