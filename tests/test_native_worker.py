import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unblock.client import private_write
try:
    from unblock.native_worker import run_worker,APPROVAL
except ImportError:
    run_worker=None;APPROVAL='APPROVE SYNTHETIC BLUE MARKER'

class WorkerClient:
    def __init__(self):
        self.row={'id':'00000000-0000-4000-8000-000000000001','agent_id':'alpha','revisions':[{'id':'revision','payload':{'need_key':'native-manifest-continuity-pilot-1','context':'Synthetic proof only'}}],'answers':[{'id':'answer','payload':{'answer':APPROVAL}}],'actions':[],'settlements':[],'uncertain_actions':[],'progress':[],'progress_history':[]}
        self.calls=[];self.pending=False
    def call(self,operation,data=None):
        if operation=='identity':return {'kind':'agent','id':'alpha'}
        if operation=='recover':return {'source':'checked','requests':[copy.deepcopy(self.row)]}
        self.calls.append((operation,data));record={'id':hashlib.sha256(data['intent_id'].encode()).hexdigest(),'intent_id':data['intent_id'],'payload':data}
        field={'action':'actions','settle':'settlements','progress':'progress'}[operation]
        if not self.pending and not any(r['id']==record['id'] for r in self.row[field]):self.row[field].append(record)
        if operation=='progress' and not self.pending:self.row['progress_history'].append(record)
        return {'record_id':record['id'],'visibility':'pending' if self.pending else 'visible'}

class NativeWorkerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(run_worker,'Native synthetic worker is missing')
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name);self.client=WorkerClient();self.rid=self.client.row['id']
    def test_artifact_is_verified_before_progress_and_replacement_does_not_repeat(self):
        result=run_worker(self.client,self.rid,self.root,poll_attempts=1)
        self.assertEqual(result['stage'],'resumed');artifact=next(self.root.glob('*.json'));before=artifact.stat().st_mtime_ns
        again=run_worker(self.client,self.rid,self.root,poll_attempts=1)
        self.assertEqual(artifact.stat().st_mtime_ns,before);self.assertEqual(again['sha256'],result['sha256'])
        operations=[op for op,_ in self.client.calls];self.assertLess(operations.index('action'),operations.index('settle'))
        self.assertEqual(self.client.calls[-1][1]['stage'],'resumed')
    def test_conflict_unapproved_or_unrelated_action_never_writes(self):
        for mutate in (lambda r:r['answers'].append({'id':'neighbor','payload':{'answer':APPROVAL}}),lambda r:r['answers'][0]['payload'].update(answer='run anything'),lambda r:r['uncertain_actions'].append({'id':'foreign'})):
            client=WorkerClient();mutate(client.row)
            with self.assertRaises(ValueError):run_worker(client,self.rid,self.root,poll_attempts=1)
            self.assertEqual(list(self.root.iterdir()),[])
    def test_pending_action_has_no_effect_and_bad_existing_artifact_is_not_overwritten(self):
        self.client.pending=True
        with self.assertRaises(ValueError):run_worker(self.client,self.rid,self.root,poll_attempts=1)
        self.assertEqual(list(self.root.iterdir()),[])
        self.client.pending=False
        run_worker(self.client,self.rid,self.root,poll_attempts=1)
        artifact=next(self.root.glob('*.json'));artifact.write_text('{"unrelated":true}')
        with self.assertRaises(ValueError):run_worker(self.client,self.rid,self.root,poll_attempts=1)
        self.assertEqual(artifact.read_text(),'{"unrelated":true}')

if __name__=='__main__':unittest.main()
