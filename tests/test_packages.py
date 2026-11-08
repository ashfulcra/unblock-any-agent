import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class PackageTests(unittest.TestCase):
    def test_exports_carry_approved_publisher_license_and_retained_notices(self):
        from scripts.build_plugins import build
        with tempfile.TemporaryDirectory() as temporary:
            for platform,root in build(Path(temporary)/'exports').items():
                manifest=json.loads((root/('.claude-plugin/plugin.json' if platform=='claude' else 'plugin.json')).read_text())
                self.assertEqual(manifest['author']['name'],'Fulcra Dynamics')
                self.assertEqual(manifest['license'],'Apache-2.0')
                self.assertEqual((root/'LICENSE').read_bytes(),Path('LICENSE').read_bytes())
                self.assertEqual((root/'THIRD_PARTY_NOTICES').read_bytes(),Path('THIRD_PARTY_NOTICES').read_bytes())
                self.assertFalse((root/'unblock/fulcra_setup.py').exists())
                if platform=='openai':self.assertEqual(manifest['extensions']['com.openai']['interface']['developerName'],'Fulcra Dynamics')

    def test_exports_link_approved_fulcra_legal_without_invented_commerce(self):
        from scripts.build_plugins import build
        with tempfile.TemporaryDirectory() as temporary:
            root=build(Path(temporary)/'exports')['openai']
            metadata=json.loads((root/'plugin.json').read_text())['extensions']['com.openai']
            self.assertEqual(metadata['interface'].get('privacyPolicyURL'),'https://www.fulcra.ai/legal/privacy-policy')
            self.assertEqual(metadata['interface'].get('termsOfServiceURL'),'https://www.fulcra.ai/legal/terms-of-use')
            self.assertNotIn('countries',metadata['publication'])
            self.assertNotIn('commerce',metadata['review'])

    def test_portable_review_assets_are_real_contained_files(self):
        import struct
        from scripts.build_plugins import build
        with tempfile.TemporaryDirectory() as temporary:
            root=build(Path(temporary)/'exports')['openai']
            metadata=json.loads((root/'plugin.json').read_text())['extensions']['com.openai']
            interface=metadata['interface']
            for key,minimum in [('logo',256),('composerIcon',48)]:
                self.assertIn(key,interface,'Public listings need an actual packaged '+key)
                image=(root/interface[key]).resolve()
                self.assertTrue(image.is_relative_to(root.resolve()))
                data=image.read_bytes()
                self.assertEqual(data[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual(data[12:16],b'IHDR')
                width,height=struct.unpack('>II',data[16:24])
                self.assertEqual(width,height)
                self.assertGreaterEqual(width,minimum)
                self.assertLessEqual(len(data),5*1024*1024)
            cases=metadata['review']['test_cases']
            self.assertEqual(len(cases['positive']),5)
            self.assertEqual(len(cases['negative']),3)
            for case in cases['positive']:
                for field in ('description','prompt','tools_triggered','expected_behavior'):
                    self.assertTrue(isinstance(case[field],str) and case[field].strip())
            self.assertNotIn('demo_recording_url',metadata['review'])
            self.assertNotIn('countries',metadata['publication'])
            self.assertNotIn('commerce',metadata['review'])

    def test_review_metadata_rejects_symlinked_files_and_parents(self):
        from unittest.mock import patch
        from scripts.build_plugins import build
        for parent_link in (False,True):
            with self.subTest(parent_link=parent_link), tempfile.TemporaryDirectory(dir=Path.cwd(),prefix='.package-test-') as temporary:
                temporary=Path(temporary)
                fixture=build(temporary/'fixture')['openai']
                external=temporary/'outside'
                external.mkdir()
                (external/'openai-review.json').write_text('{"prompts":["synthetic external file"]}')
                if parent_link:
                    (fixture/'packaging').symlink_to(external,target_is_directory=True)
                else:
                    (fixture/'packaging').mkdir()
                    (fixture/'packaging/openai-review.json').symlink_to(external/'openai-review.json')
                with patch('scripts.build_plugins.SOURCE',fixture):
                    with self.assertRaisesRegex(ValueError,'contained regular files'):
                        build(temporary/'rejected')

    def test_exports_are_contained_portable_and_have_a_working_copied_runtime(self):
        from scripts.build_plugins import build
        with tempfile.TemporaryDirectory() as temporary:
            exports=build(Path(temporary)/'exports')
            for platform,root in exports.items():
                manifest=json.loads((root/('.claude-plugin/plugin.json' if platform=='claude' else 'plugin.json')).read_text())
                self.assertEqual(manifest['name'],'unblock');self.assertEqual(manifest['version'],'0.7.9')
                self.assertEqual((root/'skills/unblock/SKILL.md').read_bytes(),Path('skills/unblock/SKILL.md').read_bytes())
                self.assertTrue((root/'skills/unblock/references/setup.md').is_file())
                for file in root.rglob('*'):
                    self.assertFalse(file.is_symlink())
                    self.assertNotIn(file.name,('owner.json','agent.json','.env','work.db','delivery.db','__pycache__'))
                process=subprocess.run([sys.executable,'-m','unblock','--help'],cwd=root,capture_output=True,text=True)
                self.assertEqual(process.returncode,0,process.stderr)
                self.assertIn('ask',process.stdout)
                mcp=json.loads((root/('.mcp.json' if platform=='claude' else 'mcp.json')).read_text())
                server=mcp['mcpServers']['unblock']
                self.assertEqual(server['command'],'uv')
                self.assertNotIn('token',json.dumps(mcp).lower())
                self.assertTrue((root/'scripts/run_mcp.py').is_file())
                self.assertTrue((root/'scripts/run_inbox_mcp.py').is_file())
                self.assertTrue((root/'unblock/ui/inbox.html').is_file())
                self.assertTrue((root/'unblock/human_inbox.py').is_file())
                self.assertEqual(set(mcp['mcpServers']),{'unblock'})
                monitor=subprocess.run([sys.executable,'-m','unblock.native_monitor','--help'],cwd=root,capture_output=True,text=True)
                self.assertEqual(monitor.returncode,0,monitor.stderr);self.assertIn('--state',monitor.stdout)
                self.assertFalse((root/'unblock/native_owner.py').exists());self.assertFalse((root/'unblock/native_renewal.py').exists())
            portable=json.loads((exports['openai']/'plugin.json').read_text())
            self.assertEqual(portable['$schema'],'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json')
            self.assertLessEqual(len(portable['extensions']['com.openai']['interface']['shortDescription']),30)
            self.assertNotIn('hooks',json.dumps(portable))
            with self.assertRaises(FileExistsError):build(Path(temporary)/'exports')

if __name__=='__main__':unittest.main()
