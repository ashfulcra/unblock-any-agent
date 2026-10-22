import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

class PackageTests(unittest.TestCase):
    def test_exports_are_contained_portable_and_have_a_working_copied_runtime(self):
        from scripts.build_plugins import build
        with tempfile.TemporaryDirectory() as temporary:
            exports=build(Path(temporary)/'exports')
            for platform,root in exports.items():
                manifest=json.loads((root/('.claude-plugin/plugin.json' if platform=='claude' else 'plugin.json')).read_text())
                self.assertEqual(manifest['name'],'unblock');self.assertEqual(manifest['version'],'0.7.1')
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
