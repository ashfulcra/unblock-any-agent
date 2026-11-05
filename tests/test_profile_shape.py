import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from unblock.client import Client, private_read, private_write
from unblock.native_client import NativeClient


class ProfileShapeTests(unittest.TestCase):
    def test_non_object_agent_profiles_are_rejected_by_both_clients(self):
        with tempfile.TemporaryDirectory() as temporary:
            for index, value in enumerate(([], None, 'not a profile', 7, True)):
                path = Path(temporary) / f'profile-{index}.json'
                private_write(path, value)
                for client in (Client, NativeClient):
                    with self.subTest(value=value, client=client.__name__):
                        with self.assertRaises(ValueError):
                            client.from_file(path)

    def test_private_json_artifacts_can_still_contain_arrays(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'artifact.json'
            private_write(path, ['retained', {'action': 'unsettled'}])
            self.assertEqual(private_read(path), ['retained', {'action': 'unsettled'}])

    @unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install requirements-mcp.txt for MCP integration tests')
    def test_non_object_profile_returns_structured_mcp_setup_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            for index, value in enumerate(([], None, 'not a profile', 7, True)):
                path = Path(temporary) / f'profile-{index}.json'
                private_write(path, value)
                environment = {**os.environ, 'UNBLOCK_AGENT_CONFIG': str(path)}
                result = subprocess.run(
                    [sys.executable, 'scripts/run_mcp.py'],
                    env=environment, capture_output=True, text=True, timeout=10,
                )
                with self.subTest(value=value):
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, '')
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(json.loads(result.stderr), {'error': 'agent_setup_required'})


if __name__ == '__main__':
    unittest.main()
