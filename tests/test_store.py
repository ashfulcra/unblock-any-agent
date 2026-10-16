import concurrent.futures
import tempfile
import unittest
from pathlib import Path
try:
    from unblock.store import Store, DomainError
except ImportError:
    Store, DomainError = None, Exception

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Store, 'Authenticated durable work store is missing')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'work.db'
        self.store = Store(self.path)
        self.owner = self.store.authenticate(self.store.bootstrap_owner('Human')['token'])
        self.workspace = self.store.create_workspace(self.owner, 'Team')['id']
        self.grant = self.store.enroll(self.owner, self.workspace, 'Worker', 'agent', 'local')
        self.agent = self.store.authenticate(self.grant['token'])
        self.request = self.ask()

    def ask(self, **changes):
        return self.store.request_help(self.agent, **{'key':'review-1','need':'Which option?','context':{'goal':'Ship the change','next_action':'Apply the decision'}, **changes})

    def answer(self, answer='Use option A', **changes):
        return self.store.answer_request(self.owner, self.request['id'], **{'revision':self.request['revision'],'answer':answer,'key':'answer-1',**changes})

    def test_answer_is_not_progress_and_new_store_recovers(self):
        response = self.answer()
        restored = Store(self.path)
        work = restored.get_request(self.agent, self.request['id'])
        self.assertEqual(work['context']['goal'], 'Ship the change')
        self.assertEqual(work['status'], 'answered')
        self.assertEqual(work['responses'][0]['id'], response['id'])
        self.assertEqual(work['progress'], [])
        restored.report_progress(self.agent, work['id'], response['id'], 'resumed', 'Applied A and started the authorized build')
        self.assertEqual(restored.get_attention(self.agent), [])
        self.assertEqual(restored.get_request(self.owner, work['id'])['status'], 'resumed')

    def test_retry_has_one_logical_request_and_rejects_key_reuse(self):
        self.assertEqual(self.ask()['id'], self.request['id'])
        with self.assertRaises(DomainError): self.ask(need='Different need')

    def test_concurrent_requests_converge(self):
        def submit(_): return Store(self.path).request_help(self.agent,'same-concurrent','Need approval',{'goal':'One change'})['id']
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(submit,range(8)))
        self.assertEqual(len(set(ids)), 1)

    def test_other_account_and_neighbor_agent_cannot_read_or_progress(self):
        other = self.store.authenticate(self.store.bootstrap_owner('Other human')['token'])
        neighbor = self.store.authenticate(self.store.enroll(self.owner,self.workspace,'Neighbor','agent','local')['token'])
        for actor in (other,neighbor):
            with self.assertRaises(DomainError): self.store.get_request(actor,self.request['id'])
        response=self.answer()
        with self.assertRaises(DomainError): self.store.report_progress(neighbor,self.request['id'],response['id'],'resumed','I claim this work')
        with self.assertRaises(DomainError): self.store.answer_request(neighbor,self.request['id'],self.request['revision'],'Yes','neighbor')

    def test_revocation_is_checked_on_existing_actor(self):
        self.store.revoke(self.owner,self.agent.id)
        with self.assertRaises(DomainError): self.store.authenticate(self.grant['token'])
        with self.assertRaises(DomainError): self.ask(key='new')
        with self.assertRaises(DomainError): self.store.get_request(self.agent,self.request['id'])

    def test_stale_answer_retained_and_not_delivered(self):
        self.store.revise_request(self.agent,self.request['id'],'Updated question',{'goal':'Changed scope'})
        response=self.answer()
        work=self.store.get_request(self.owner,self.request['id'])
        self.assertTrue(work['responses'][0]['stale'])
        self.assertEqual(work['status'],'open')
        self.assertEqual(self.store.get_attention(self.agent),[])
        with self.assertRaises(DomainError): self.store.report_progress(self.agent,work['id'],response['id'],'resumed','Use obsolete answer')
        self.assertEqual(len(work['versions']),2)

    def test_incompatible_answers_remain_visible_and_attributed(self):
        one=self.answer(); two=self.answer('Use B',key='answer-2')
        work=self.store.get_request(self.agent,self.request['id'])
        self.assertTrue(work['conflicting_answers'])
        self.assertEqual({r['actor_id'] for r in work['responses']},{self.owner.id})
        self.assertEqual(len(work['responses']),2)
        self.store.report_progress(self.agent,work['id'],two['id'],'resumed','Reconciled both answers; the later human correction explicitly selects B')
        self.assertEqual(self.store.get_request(self.agent,work['id'])['progress'][-1]['response_id'],two['id'])

    def test_response_retry_is_idempotent_but_changed_payload_is_rejected(self):
        self.assertEqual(self.answer()['id'],self.answer()['id'])
        with self.assertRaises(DomainError): self.answer('Changed')

    def test_environment_listener_cannot_read_other_environments_or_claim_work(self):
        here=self.store.authenticate(self.store.enroll(self.owner,self.workspace,'Listener','listener','local')['token'])
        elsewhere=self.store.authenticate(self.store.enroll(self.owner,self.workspace,'Remote','listener','remote')['token'])
        self.answer()
        self.assertEqual(len(self.store.get_attention(here)),1)
        self.assertEqual(self.store.get_attention(elsewhere),[])
        with self.assertRaises(DomainError): self.store.get_request(elsewhere,self.request['id'])
        with self.assertRaises(DomainError): self.store.report_progress(here,self.request['id'],self.answer()['id'],'resumed','Listener impersonating agent')

    def test_interrupted_action_is_retained_and_cannot_be_completed_blindly(self):
        response=self.answer()
        action=self.store.declare_action(self.agent,self.request['id'],'deploy-1','Deploy approved change')
        restored=Store(self.path)
        work=restored.get_request(self.agent,self.request['id'])
        self.assertEqual(work['actions'][0]['status'],'uncertain')
        self.assertEqual(restored.declare_action(self.agent,work['id'],'deploy-1','Deploy approved change')['id'],action['id'])
        with self.assertRaises(DomainError): restored.report_progress(self.agent,work['id'],response['id'],'completed','Assume deploy succeeded')
        restored.settle_action(self.agent,work['id'],action['id'],'Verified deployment ID 123')
        restored.report_progress(self.agent,work['id'],response['id'],'completed','Deployment result verified')

if __name__=='__main__': unittest.main()
