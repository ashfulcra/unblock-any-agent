import copy
import json
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from unblock.store import DomainError
from unblock.human_inbox import HumanInbox, request_json

OWNER='11111111-1111-4111-a111-111111111111'
PROJECT='22222222-2222-4222-a222-222222222222'
RID='33333333-3333-4333-a333-333333333333'
REV='44444444-4444-4444-a444-444444444444'


class HumanInboxTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.state=Path(self.temp.name)/'human.db';self.calls=[]
        self.owner=OWNER;self.project={'id':PROJECT,'domain':'example.my.fulcra.ai'}
        self.fail_read=False;self.lose_write=False;self.visible=True
        self.row={'id':RID,'agent_id':'alpha','state':'needs_you','created_at':'2026-10-16T12:00:00Z','revisions':[{'id':REV,'payload':{'need':'Choose the test label','context':'Relevant context for a human decision','recommendation':'Mint','next_action':'Apply only the private test marker'}}],'answers':[],'stale_answers':[],'history':[],'progress':[],'uncertain_actions':[]}

    def platform(self,token,path):
        self.assertEqual(token,'private-test-token')
        return {'userid':self.owner} if path=='/user/v1alpha1/info' else self.project

    def dashboard(self,origin,token,operation,data=None):
        self.assertEqual(origin,'https://example.my.fulcra.ai')
        self.calls.append((operation,copy.deepcopy(data)))
        if operation=='attention':
            if self.fail_read:raise DomainError('human_source_unavailable',503)
            return {'source':'checked','principal':{'kind':'owner','id':OWNER},'checked_at':'2026-10-19T12:00:00Z','requests':[copy.deepcopy(self.row)],'grants':[{'agent_id':'alpha','name':'Alpha designer','environment':'desktop'}]}
        self.assertEqual(operation,'answer')
        self.assertRegex(data['reviewed_snapshot'],r'^[a-f0-9]{64}$')
        if self.visible:
            self.row['answers'].append({'id':'55555555-5555-4555-a555-555555555555','intent_id':data['intent_id'],'payload':{'revision':data['revision'],'answer':data['answer'],'responder':OWNER}})
            self.row['state']='awaiting_pickup'
        if self.lose_write:raise DomainError('human_source_unavailable',503)
        return {'record_id':'55555555-5555-4555-a555-555555555555','visibility':'visible' if self.visible else 'pending'}

    def client(self):
        return HumanInbox(PROJECT,OWNER,self.state,token_provider=lambda:'private-test-token',platform=self.platform,dashboard=self.dashboard)

    def submit(self,c,decision=None,**changes):
        decision=decision or c.get_decision(RID)
        args={'request_id':RID,'revision':REV,'reviewed_snapshot':decision['reviewed_snapshot'],'answer':'Use mint for the synthetic check only.','intent_id':'stable-human-answer'}
        args.update(changes)
        return c.answer_decision(**args)

    def test_inbox_leads_with_agent_original_wait_question_and_context(self):
        result=self.client().inbox()
        self.assertEqual(result['source'],'checked')
        item=result['items'][0]
        self.assertEqual(item['agent_name'],'Alpha designer')
        self.assertEqual(item['created_at'],self.row['created_at'])
        self.assertEqual(item['decision'],'Choose the test label')
        self.assertIn('Relevant context',item['context'])
        self.assertNotIn('private-test-token',json.dumps(result))

    def test_full_decision_returns_current_review_snapshot_and_history(self):
        result=self.client().get_decision(RID)
        self.assertTrue(result['can_answer']);self.assertEqual(result['request'],self.row)
        self.assertRegex(result['reviewed_snapshot'],r'^[a-f0-9]{64}$')

    def test_withdrawn_request_is_reviewable_but_needs_no_human_answer(self):
        self.row['state']='withdrawn';c=self.client()
        self.assertEqual(c.inbox()['items'],[]);self.assertEqual(c.inbox()['counts']['done'],1)
        self.assertEqual(len(c.inbox(include_completed=True)['items']),1)
        detail=c.get_decision(RID);self.assertFalse(detail['can_answer'])
        with self.assertRaises(DomainError):self.submit(c,detail)

    def test_verified_deployment_cannot_change_origin_with_a_retained_journal(self):
        c=self.client();c.inbox();self.calls.clear();self.project['domain']='different.my.fulcra.ai'
        with self.assertRaises(DomainError):self.client().inbox()
        self.assertEqual(self.calls,[])

    def test_invalid_platform_response_retains_unknown_source_without_forwarding(self):
        c=HumanInbox(PROJECT,OWNER,self.state,token_provider=lambda:'private-test-token',platform=lambda *_:None,dashboard=self.dashboard)
        self.assertEqual(c.inbox()['source'],'unavailable');self.assertEqual(self.calls,[])

    def test_inbox_context_is_concise_while_full_decision_retains_all_context(self):
        self.row['revisions'][0]['payload']['context']='Full retained context. '*100
        c=self.client();self.assertLessEqual(len(c.inbox()['items'][0]['context']),281)
        self.assertEqual(c.get_decision(RID)['request']['revisions'][0]['payload']['context'],self.row['revisions'][0]['payload']['context'])

    def test_changed_account_or_project_denies_before_dashboard_forwarding(self):
        for change in ('owner','project','domain'):
            with self.subTest(change=change):
                self.owner=OWNER;self.project={'id':PROJECT,'domain':'example.my.fulcra.ai'};self.calls.clear()
                if change=='owner':self.owner='different-owner'
                if change=='project':self.project['id']='different-project'
                if change=='domain':self.project['domain']='evil.example/path'
                with self.assertRaises(DomainError):self.client().inbox()
                self.assertEqual(self.calls,[])

    def test_changed_question_or_answer_set_requires_review_without_writing(self):
        c=self.client();reviewed=c.get_decision(RID)
        for change in ('question','answers','uncertain'):
            with self.subTest(change=change):
                old=copy.deepcopy(self.row)
                if change=='question':self.row['revisions'][0]['id']='66666666-6666-4666-a666-666666666666'
                if change=='answers':self.row['answers'].append({'id':'new-answer','payload':{'answer':'New human answer'}})
                if change=='uncertain':self.row['uncertain_actions'].append({'id':'new-uncertain-action'})
                with self.assertRaises(DomainError):self.submit(c,reviewed)
                self.assertFalse(any(op=='answer' for op,_ in self.calls));self.row=old

    def test_lost_write_response_reconciles_exact_answer_after_restart(self):
        c=self.client();reviewed=c.get_decision(RID);self.lose_write=True
        result=self.submit(c,reviewed)
        self.assertEqual(result['visibility'],'pending')
        self.assertEqual(len(c.pending_answers()),1)
        self.lose_write=False
        result=self.submit(self.client(),reviewed)
        self.assertEqual(result['visibility'],'visible')
        self.assertEqual(result['progress'],'awaiting_pickup')
        self.assertEqual(sum(op=='answer' for op,_ in self.calls),1)
        self.assertEqual(self.client().pending_answers(),[])

    def test_uncertain_unseen_answer_keeps_original_intent_on_changed_question(self):
        c=self.client();reviewed=c.get_decision(RID);self.visible=False;self.lose_write=True
        self.assertEqual(self.submit(c,reviewed)['visibility'],'pending')
        self.row['revisions'][0]['id']='66666666-6666-4666-a666-666666666666';self.lose_write=False
        result=self.submit(self.client(),reviewed)
        self.assertEqual(result['visibility'],'pending')
        self.assertEqual(sum(op=='answer' for op,_ in self.calls),1)
        self.assertEqual(len(c.pending_answers()),1)

    def test_fresh_reviewed_question_can_be_answered_while_prior_intent_stays_uncertain(self):
        c=self.client();old=c.get_decision(RID);self.visible=False;self.lose_write=True
        self.assertEqual(self.submit(c,old)['visibility'],'pending')
        self.row['revisions'][0]['id']='66666666-6666-4666-a666-666666666666';self.lose_write=False;self.visible=True
        current=c.get_decision(RID)
        result=self.submit(c,current,revision=self.row['revisions'][0]['id'],intent_id='fresh-current-question')
        self.assertEqual(result['visibility'],'visible')
        pending=self.client().pending_answers();self.assertEqual(len(pending),1)
        self.assertEqual(pending[0]['intent_id'],'stable-human-answer')
        self.assertEqual(pending[0]['revision'],REV)

    def test_same_intent_cannot_change_answer_and_state_cannot_change_owner(self):
        c=self.client();reviewed=c.get_decision(RID);self.submit(c,reviewed)
        with self.assertRaises(DomainError):self.submit(c,reviewed,answer='A changed decision')
        with self.assertRaises((DomainError,ValueError)):
            HumanInbox(PROJECT,'77777777-7777-4777-a777-777777777777',self.state)

    def test_definite_first_rejection_keeps_history_but_allows_fresh_review(self):
        c=self.client();reviewed=c.get_decision(RID)
        def reject(*args):
            if args[2]=='attention':return self.dashboard(*args)
            failure=DomainError('decision_changed_review_again',409)
            failure.write_outcome='rejected';raise failure
        c.dashboard=reject
        result=self.submit(c,reviewed)
        self.assertEqual(result['visibility'],'rejected');self.assertEqual(c.pending_answers(),[])
        self.assertEqual(self.submit(c,reviewed)['visibility'],'rejected')
        with self.assertRaises(DomainError):self.submit(c,reviewed,answer='changed')
        c.dashboard=self.dashboard
        self.assertEqual(self.submit(c,c.get_decision(RID),intent_id='fresh-reviewed-intent')['visibility'],'visible')

    def test_rejection_after_uncertain_attempt_does_not_erase_uncertainty(self):
        c=self.client();reviewed=c.get_decision(RID);self.visible=False;self.lose_write=True
        self.assertEqual(self.submit(c,reviewed)['visibility'],'pending')
        def reject(*args):
            if args[2]=='attention':return self.dashboard(*args)
            failure=DomainError('decision_changed_review_again',409)
            failure.write_outcome='rejected';raise failure
        c.dashboard=reject
        self.assertEqual(self.submit(c,reviewed)['visibility'],'pending')
        self.assertEqual(len(c.pending_answers()),1)

    def test_native_http_rejected_outcome_is_distinct_from_uncertain_failure(self):
        for outcome in ('rejected','uncertain'):
            error=urllib.error.HTTPError('https://example.my.fulcra.ai',400,'bad',{},io.BytesIO(json.dumps({'outcome':outcome,'error':'Decision changed; review again'}).encode()))
            with patch('urllib.request.build_opener') as opener:
                opener.return_value.open.side_effect=error
                with self.assertRaises(DomainError) as caught:request_json('https://example.my.fulcra.ai',{}, {})
            self.assertEqual(getattr(caught.exception,'write_outcome',None),'rejected' if outcome=='rejected' else None)

    def test_read_failure_retains_known_work_with_unknown_source_and_counts(self):
        c=self.client();c.inbox();self.fail_read=True
        failed=self.client().inbox()
        self.assertEqual(failed['source'],'unavailable');self.assertEqual(len(failed['items']),1)
        self.assertIsNone(failed['counts']);self.assertTrue(failed['last_known'])
        with self.assertRaises(DomainError):self.submit(c,{'reviewed_snapshot':'0'*64})
        self.assertFalse(any(op=='answer' for op,_ in self.calls))

    def test_first_read_failure_is_unknown_not_empty_and_symlink_state_is_denied(self):
        self.fail_read=True
        result=self.client().inbox();self.assertEqual(result['source'],'unavailable');self.assertFalse(result['last_known']);self.assertIsNone(result['counts'])
        target=Path(self.temp.name)/'symlink.db';target.symlink_to(self.state)
        with self.assertRaises((DomainError,ValueError)):HumanInbox(PROJECT,OWNER,target)


if __name__=='__main__':unittest.main()
