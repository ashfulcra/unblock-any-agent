import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
try:
    from unblock import fulcra_setup
except ImportError:
    fulcra_setup=None

OWNER='11111111-1111-4111-8111-111111111111'
OTHER='22222222-2222-4222-8222-222222222222'
PROJECT='33333333-3333-4333-8333-333333333333'
HARNESS='44444444-4444-4444-8444-444444444444'
PRODUCT='55555555-5555-4555-8555-555555555555'

class SetupTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(fulcra_setup,'The verified per-user Fulcra setup command is missing')
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve()
        self.owner=OWNER
        self.project={'id':PROJECT,'domain':'fixture-unblock.my.fulcra.ai'}
        self.annotations=[{'id':i,'fulcra_userid':OWNER,'annotation_type':'moment','fulcra_source_id':'com.fulcradynamics.annotation.'+i,'deleted_at':None} for i in (HARNESS,PRODUCT)]
        self.state=self.root/'setup.json';self.env=self.root/'.env'

    def platform(self,token,path):
        self.assertEqual(token,'fixture-token')
        if path=='/user/v1alpha1/info':return {'userid':self.owner}
        if path=='/user/v1/deploy/project/'+PROJECT:return self.project
        if path=='/user/v1alpha1/annotation?fulcra_userid='+self.owner+'&annotation_type=moment':return self.annotations
        self.fail('Unexpected platform operation: '+path)

    def configure(self,**changes):
        args=dict(project_id=PROJECT,harness_annotation=HARNESS,product_annotation=PRODUCT,state_path=self.state,env_path=self.env,workspace='workspace/my-unblock',token_provider=lambda:'fixture-token',platform=self.platform)
        args.update(changes)
        return fulcra_setup.configure(**args)

    def test_account_owned_setup_writes_private_server_config_without_exposing_key(self):
        result=self.configure();saved=json.loads(self.state.read_text());text=self.env.read_text()
        self.assertEqual(result['origin'],'https://fixture-unblock.my.fulcra.ai')
        self.assertIn('OWNER_USER_ID="'+OWNER+'"',text)
        self.assertIn('PUBLIC_WORKSPACE_PATH="workspace/my-unblock"',text)
        self.assertIn('UNBLOCK_ANNOTATION_ID="MomentAnnotation/'+PRODUCT+'"',text)
        self.assertIn('PUBLIC_AUTH0_CLIENT_ID="whF3ymxsYHijh2QrGkGbgDkxqDDAA8KB"',text)
        self.assertEqual(len(saved['agent_key']),64)
        self.assertIn(saved['agent_key'],text)
        self.assertNotIn(saved['agent_key'],json.dumps(result))
        self.assertNotIn('fixture-token',self.state.read_text()+text+json.dumps(result))
        for p in (self.state,self.env):self.assertEqual(p.stat().st_mode&0o777,0o600)

    def test_retry_preserves_key_and_environment(self):
        self.configure();before=(self.state.read_bytes(),self.env.read_bytes())
        self.configure()
        self.assertEqual((self.state.read_bytes(),self.env.read_bytes()),before)

    def test_account_or_resource_change_does_not_reuse_previous_state(self):
        self.configure();before=self.state.read_bytes()
        self.owner=OTHER
        for annotation in self.annotations:annotation['fulcra_userid']=OTHER
        with self.assertRaises(ValueError):self.configure()
        self.assertEqual(self.state.read_bytes(),before)

    def test_foreign_shared_deleted_or_duplicate_annotations_are_rejected(self):
        for kind in ('foreign','deleted','duplicate','same'):
            with self.subTest(kind=kind):
                original=json.loads(json.dumps(self.annotations))
                if kind=='foreign':self.annotations[1]['fulcra_userid']=OTHER
                if kind=='deleted':self.annotations[1]['deleted_at']='2026-10-23T00:00:00Z'
                if kind=='duplicate':self.annotations.append(dict(self.annotations[1]))
                with self.assertRaises(ValueError):self.configure(product_annotation=HARNESS if kind=='same' else PRODUCT)
                self.assertFalse(self.state.exists());self.assertFalse(self.env.exists())
                self.annotations=original

    def test_wrong_project_or_untrusted_domain_is_rejected_before_writing(self):
        for key,value in [('id',OTHER),('domain','attacker.invalid'),('domain','other.my.fulcra.ai.attacker.invalid')]:
            old=self.project[key];self.project[key]=value
            with self.assertRaises(ValueError):self.configure()
            self.assertFalse(self.state.exists());self.project[key]=old

    def test_malformed_domain_fails_cleanly_without_configuration(self):
        for value in (None,42,[]):
            self.project['domain']=value
            try:self.configure()
            except Exception as error:self.assertIsInstance(error,ValueError)
            else:self.fail('Malformed project domain was accepted')
            self.assertFalse(self.state.exists());self.assertFalse(self.env.exists())

    def test_check_only_uses_live_ownership_without_creating_private_files(self):
        result=self.configure(check_only=True)
        self.assertEqual(result['origin'],'https://fixture-unblock.my.fulcra.ai')
        self.assertFalse(self.state.exists());self.assertFalse(self.env.exists())

    def test_existing_different_environment_is_never_overwritten(self):
        self.env.write_text('EXISTING="retain me"\n');self.env.chmod(0o600)
        with self.assertRaises(ValueError):self.configure()
        self.assertEqual(self.env.read_text(),'EXISTING="retain me"\n')

    def test_unsafe_or_symlinked_files_are_rejected(self):
        self.env.write_text('keep');self.env.chmod(0o644)
        with self.assertRaises(ValueError):self.configure()
        self.env.unlink();target=self.root/'target';target.write_text('keep')
        self.env.symlink_to(target)
        with self.assertRaises(ValueError):self.configure()
        self.assertEqual(target.read_text(),'keep')

    def test_state_symlink_and_changed_environment_path_are_rejected(self):
        self.configure();original=self.state.read_bytes()
        with self.assertRaises(ValueError):self.configure(env_path=self.root/'other.env')
        self.state.rename(self.root/'original');self.state.symlink_to(self.root/'original')
        with self.assertRaises(ValueError):self.configure()
        self.assertEqual((self.root/'original').read_bytes(),original)

    def test_partial_environment_failure_retains_key_for_safe_retry(self):
        with patch.object(fulcra_setup,'write_env',side_effect=OSError('fixture disk failure')):
            with self.assertRaises(OSError):self.configure()
        key=json.loads(self.state.read_text())['agent_key']
        self.configure()
        self.assertIn(key,self.env.read_text())

    def test_workspace_injection_is_rejected_without_writes(self):
        for workspace in ('workspace/a\nUNBLOCK_AGENT_KEY=bad','../elsewhere','workspace/../other'):
            with self.assertRaises(ValueError):self.configure(workspace=workspace)
            self.assertFalse(self.state.exists())

if __name__=='__main__':unittest.main()
