import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from unblock.client import private_write
from unblock.human_inbox import HumanInbox
from unblock.store import DomainError


class HumanProfileShapeTests(unittest.TestCase):
    project = '11111111-1111-4111-a111-111111111111'
    owner = '22222222-2222-4222-a222-222222222222'

    def malformed(self, journal):
        values = [[], None, 'not a human profile', 7, True]
        for state in ([], {}, None, 7, True):
            values.append({'transport': 'fulcra-human', 'project_id': self.project,
                           'owner_id': self.owner, 'state_path': state})
        values.append({'transport': 'fulcra-human', 'project_id': self.project,
                       'owner_id': self.owner, 'state_path': str(journal), 'token': 'unwanted'})
        return values

    def test_malformed_human_profile_cannot_create_a_journal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = root / 'never-created.db'
            for index, value in enumerate(self.malformed(journal)):
                config = root / f'profile-{index}.json'
                private_write(config, value)
                with self.subTest(value=value):
                    with self.assertRaises((ValueError, DomainError)):
                        HumanInbox.from_file(config)
                    self.assertFalse(journal.exists())

    @unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install requirements-mcp.txt for MCP integration tests')
    def test_malformed_human_startup_does_not_authenticate_or_change_worker_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / 'auth-called'
            executable = root / 'fulcra-api'
            executable.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 91\n')
            executable.chmod(0o700)
            worker = root / 'worker.json'
            private_write(worker, {'transport': 'fulcra-native', 'url': 'https://example.invalid', 'token': 'fixture'})
            original = worker.read_bytes()
            journal = root / 'never-created.db'
            for index, value in enumerate(self.malformed(journal)):
                config = root / f'profile-{index}.json'
                private_write(config, value)
                result = subprocess.run(
                    [sys.executable, 'scripts/run_inbox_mcp.py'],
                    env={**os.environ, 'UNBLOCK_HUMAN_CONFIG': str(config),
                         'UNBLOCK_AGENT_CONFIG': str(worker),
                         'PATH': str(root) + os.pathsep + os.environ.get('PATH', '')},
                    capture_output=True, text=True, timeout=10,
                )
                with self.subTest(value=value):
                    self.assertEqual(result.returncode, 1)
                    self.assertEqual(result.stdout, '')
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(json.loads(result.stderr), {'error': 'human_inbox_setup_required_worker_profile_unchanged'})
                    self.assertEqual(worker.read_bytes(), original)
                    self.assertFalse(marker.exists())
                    self.assertFalse(journal.exists())

    def test_valid_profile_retains_bound_private_journal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = root / 'human.db'
            config = root / 'human.json'
            private_write(config, {'transport': 'fulcra-human', 'project_id': self.project,
                                   'owner_id': self.owner, 'state_path': str(journal)})
            inbox = HumanInbox.from_file(config)
            self.assertEqual((inbox.project_id, inbox.owner_id), (self.project, self.owner))
            self.assertEqual(journal.stat().st_mode & 0o777, 0o600)
            with inbox.db() as database:
                binding = json.loads(database.execute("SELECT value FROM meta WHERE key='binding'").fetchone()[0])
            self.assertEqual(binding, {'project_id': self.project, 'owner_id': self.owner})


if __name__ == '__main__':
    unittest.main()
