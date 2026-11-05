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
    invalid_profiles = (
        [], None, 'not a profile', 7, True,
        {'url': {}, 'token': 'fixture'},
        {'url': 'http://127.0.0.1:1', 'token': ['fixture']},
        {'url': 'http://127.0.0.1:1', 'token': None},
    )

    def test_malformed_agent_profiles_are_rejected_by_both_clients(self):
        with tempfile.TemporaryDirectory() as temporary:
            for index, value in enumerate(self.invalid_profiles):
                if isinstance(value, dict):
                    value = {'transport': 'fulcra-native', **value}
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
    def test_malformed_profile_returns_structured_mcp_setup_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            for index, value in enumerate(self.invalid_profiles):
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

    def test_claude_route_rejects_non_object_config_before_launch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / 'profile.json'
            private_write(profile, [])
            executable = root / 'claude'
            marker = root / 'launched'
            executable.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 91\n')
            executable.chmod(0o700)
            result = subprocess.run(
                [sys.executable, '-m', 'unblock.claude_route', '--config', str(profile),
                 '--output', str(root / 'output'), '--session-id', '11111111-1111-4111-a111-111111111111'],
                input='{"agent_id":"11111111-1111-4111-a111-111111111111"}',
                env={**os.environ, 'PATH': str(root) + os.pathsep + os.environ.get('PATH', '')},
                capture_output=True, text=True, timeout=10,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, '')
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(json.loads(result.stderr), {'error': 'claude_route_failed'})
            self.assertFalse(marker.exists())


if __name__ == '__main__':
    unittest.main()
