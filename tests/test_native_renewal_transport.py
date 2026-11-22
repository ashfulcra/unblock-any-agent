"""A failed remote connection must not prevent a fresh check of later selections."""
import copy
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

from unblock.client import private_read, private_write
from unblock.native_renewal import Renewal
from unblock.store import DomainError
from test_native_renewal import ANCHOR, OwnerFixture

SECOND = '22222222-2222-4222-8222-222222222222'


class VisibleOwnerFixture(OwnerFixture):
    def call(self, operation, data=None):
        result = super().call(operation, data)
        if operation == 'enroll':
            self.publish()
        return result


class NativeRenewalTransportTests(unittest.TestCase):
    def setUp(self):
        self.fresh_operator()

    def fresh_operator(self, bootstrap=True):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config = self.root / 'operator.json'
        self.state = self.root / 'state.json'
        self.profiles = [self.root / 'alpha.json', self.root / 'beta.json']
        self.owner = VisibleOwnerFixture()
        self.owner.grants.append({**self.owner.grants[0], 'grant_id': SECOND,
            'record_id': 'beta-anchor', 'agent_id': 'beta', 'name': 'Beta', 'agent_ids': ['beta']})
        for profile in self.profiles:
            private_write(profile, {'transport': 'fulcra-native', 'url': self.owner.url, 'token': 'original'})
        private_write(self.config, {'url': self.owner.url, 'enrollments': [
            {'anchor_grant_id': ANCHOR, 'profile': str(self.profiles[0])},
            {'anchor_grant_id': SECOND, 'profile': str(self.profiles[1])}]})
        if bootstrap:
            self.assertEqual(self.renewal().tick()['renewed'], 2)
        self.before = [profile.read_bytes() for profile in self.profiles]
        self.owner.clock = 1040

    def renewal(self):
        return Renewal(self.owner, self.config, self.state, lease_seconds=60,
            renew_before=30, now=lambda: self.owner.clock)

    def test_bootstrap_keeps_first_observed_owner_across_unverified_attention(self):
        self.fresh_operator(bootstrap=False)
        original = self.owner.call
        identities = 0
        def remote_call(operation, data=None):
            nonlocal identities
            if operation == 'identity':
                identities += 1
                if identities > 1:
                    self.owner.owner_id = 'different-owner'
            if operation == 'attention' and identities == 1:
                raise TimeoutError('first owner attention unavailable')
            return original(operation, data)
        with patch.object(self.owner, 'call', side_effect=remote_call):
            result = self.renewal().tick()
        self.assertFalse(result['checked'])
        self.assertEqual(result['renewed'], 0)
        self.assertEqual(result['error'], 'operator_owner_changed')
        self.assertEqual([profile.read_bytes() for profile in self.profiles], self.before)
        self.assertEqual(self.owner.accepted, [])
        self.assertFalse(self.state.exists())

    def test_bootstrap_same_owner_can_verify_later_connection_after_attention_timeout(self):
        self.fresh_operator(bootstrap=False)
        original = self.owner.call
        failed = False
        def remote_call(operation, data=None):
            nonlocal failed
            if operation == 'attention' and not failed:
                failed = True
                raise TimeoutError('first attention unavailable')
            return original(operation, data)
        with patch.object(self.owner, 'call', side_effect=remote_call):
            result = self.renewal().tick()
        self.assertFalse(result['checked'])
        self.assertEqual(result['renewed'], 1)
        self.assertEqual(self.profiles[0].read_bytes(), self.before[0])
        self.assertEqual(private_read(self.profiles[1])['expires_at'], 1100)
        self.assertEqual(private_read(self.state)['owner_id'], 'owner')

    def test_fatal_journal_error_reports_only_durably_retained_pending_intents(self):
        self.assert_fatal_pending_readback(corrupt=False)

    def test_fatal_journal_error_marks_pending_count_unknown_when_ledger_cannot_be_read(self):
        self.assert_fatal_pending_readback(corrupt=True)

    def assert_fatal_pending_readback(self, corrupt):
        original_call = self.owner.call
        original_save = Renewal._save
        def remote_call(operation, data=None):
            result = original_call(operation, data)
            if operation == 'enroll' and data['agent_id'] == 'alpha':
                raise TimeoutError('alpha response lost after acceptance')
            return result
        def save(renewal, state):
            if state['entries'][SECOND].get('pending'):
                if corrupt:
                    self.state.write_text('unreadable retained journal')
                raise OSError('beta journal save failed before enrollment')
            return original_save(renewal, state)
        accepted = len(self.owner.accepted)
        with patch.object(self.owner, 'call', side_effect=remote_call), patch.object(Renewal, '_save', new=save):
            result = self.renewal().tick()
        self.assertFalse(result['checked'])
        self.assertEqual(result['renewed'], 0)
        self.assertEqual(result['pending_known'], None if corrupt else 1)
        self.assertEqual([profile.read_bytes() for profile in self.profiles], self.before)
        self.assertEqual(len(self.owner.accepted), accepted + 1)
        if corrupt:
            self.assertEqual(self.state.read_text(), 'unreadable retained journal')
        else:
            entries = private_read(self.state)['entries']
            self.assertIn('pending', entries[ANCHOR])
            self.assertNotIn('pending', entries[SECOND])

    def test_source_transport_timeout_preserves_first_profile_and_renews_later_connection(self):
        for operation in ('identity', 'attention', 'prepare_enrollment'):
            for error in (TimeoutError('remote timeout'), urllib.error.URLError('remote unavailable')):
                with self.subTest(operation=operation, error=type(error).__name__):
                    self.fresh_operator()
                    original = self.owner.call
                    failed = False
                    def remote_call(current, data=None):
                        nonlocal failed
                        if current == operation and not failed:
                            failed = True
                            raise error
                        return original(current, data)
                    with patch.object(self.owner, 'call', side_effect=remote_call):
                        result = self.renewal().tick()
                    self.assertFalse(result['checked'])
                    self.assertEqual(result['renewed'], 1)
                    self.assertEqual(self.profiles[0].read_bytes(), self.before[0])
                    self.assertEqual(private_read(self.profiles[1])['expires_at'], 1100)
                    self.assertNotIn('pending', private_read(self.state)['entries'][ANCHOR])
                    self.assertEqual(result['errors'][0]['code'], 'operator_connection_transport_unavailable')

    def test_lost_enrollment_response_keeps_exact_intent_and_later_connection_renews(self):
        original = self.owner.call
        failed_body = None
        def remote_call(operation, data=None):
            nonlocal failed_body
            result = original(operation, data)
            if operation == 'enroll' and data['agent_id'] == 'alpha' and failed_body is None:
                failed_body = copy.deepcopy(data)
                raise TimeoutError('response lost after remote acceptance')
            return result
        with patch.object(self.owner, 'call', side_effect=remote_call):
            result = self.renewal().tick()
        self.assertFalse(result['checked'])
        self.assertEqual(result['renewed'], 1)
        self.assertEqual(result['pending_known'], 1)
        self.assertEqual(self.profiles[0].read_bytes(), self.before[0])
        self.assertEqual(private_read(self.profiles[1])['expires_at'], 1100)
        pending = private_read(self.state)['entries'][ANCHOR]['pending']
        self.assertEqual(pending['body'], failed_body)
        self.assertNotIn('response', pending)
        accepted = len(self.owner.accepted)
        self.assertEqual(self.renewal().tick()['renewed'], 1)
        self.assertEqual(self.owner.calls[-1], failed_body)
        self.assertEqual(len(self.owner.accepted), accepted)
        self.assertNotIn('pending', private_read(self.state)['entries'][ANCHOR])

    def test_transport_failure_after_receipt_preserves_exact_pending_response(self):
        original = self.owner.call
        failed_body = None
        failed = False
        def remote_call(operation, data=None):
            nonlocal failed_body, failed
            if operation == 'enroll' and data['agent_id'] == 'alpha':
                failed_body = copy.deepcopy(data)
            result = original(operation, data)
            if operation == 'attention' and failed_body and not failed:
                failed = True
                raise urllib.error.URLError('readback lost after enrollment receipt')
            return result
        with patch.object(self.owner, 'call', side_effect=remote_call):
            result = self.renewal().tick()
        self.assertFalse(result['checked'])
        self.assertEqual(result['renewed'], 1)
        self.assertEqual(result['pending_known'], 1)
        pending = private_read(self.state)['entries'][ANCHOR]['pending']
        self.assertEqual(pending['body'], failed_body)
        self.assertIn('response', pending)
        self.assertEqual(self.profiles[0].read_bytes(), self.before[0])
        self.assertEqual(private_read(self.profiles[1])['expires_at'], 1100)
        accepted = len(self.owner.accepted)
        self.assertEqual(self.renewal().tick()['renewed'], 1)
        self.assertEqual(self.owner.calls[-1], failed_body)
        self.assertEqual(len(self.owner.accepted), accepted)

    def test_expired_unknown_transport_intent_is_retained_while_later_connection_renews(self):
        original = self.owner.call
        def remote_call(operation, data=None):
            if operation == 'enroll' and data['agent_id'] == 'alpha':
                raise urllib.error.URLError('remote acceptance unknown')
            return original(operation, data)
        with patch.object(self.owner, 'call', side_effect=remote_call):
            first = self.renewal().tick()
        self.assertEqual(first['renewed'], 1)
        pending = private_read(self.state)['entries'][ANCHOR]['pending']
        accepted = len(self.owner.accepted)
        self.owner.clock = 1101
        result = self.renewal().tick()
        self.assertEqual(result['renewed'], 1)
        self.assertEqual(result['pending'], 1)
        self.assertEqual(result['errors'][0]['code'], 'expired_intent_pending_readback')
        self.assertEqual(private_read(self.state)['entries'][ANCHOR]['pending'], pending)
        self.assertEqual(self.profiles[0].read_bytes(), self.before[0])
        self.assertEqual(private_read(self.profiles[1])['expires_at'], 1161)
        self.assertEqual(len(self.owner.accepted), accepted + 1)
        self.assertEqual(self.owner.calls[-1]['agent_id'], 'beta')

    def test_http_error_response_is_not_downgraded_to_an_isolated_network_failure(self):
        for status in (401, 403, 503):
            with self.subTest(status=status):
                self.fresh_operator()
                original = self.owner.call
                failed = False
                def remote_call(operation, data=None):
                    nonlocal failed
                    if operation == 'identity' and not failed:
                        failed = True
                        response = urllib.error.HTTPError(self.owner.url, status, 'response error', None, None)
                        self.addCleanup(response.close)
                        raise response
                    return original(operation, data)
                with patch.object(self.owner, 'call', side_effect=remote_call):
                    result = self.renewal().tick()
                self.assertFalse(result['checked'])
                self.assertEqual(result['renewed'], 0)
                self.assertEqual([profile.read_bytes() for profile in self.profiles], self.before)

    def test_local_journal_timeout_stops_before_any_new_remote_enrollment(self):
        before_ledger = self.state.read_bytes()
        accepted = len(self.owner.accepted)
        with patch.object(Renewal, '_save', side_effect=TimeoutError('local journal timeout')):
            result = self.renewal().tick()
        self.assertFalse(result['checked'])
        self.assertEqual(result['renewed'], 0)
        self.assertEqual([profile.read_bytes() for profile in self.profiles], self.before)
        self.assertEqual(self.state.read_bytes(), before_ledger)
        self.assertEqual(len(self.owner.accepted), accepted)

    def test_authentication_or_unverified_source_stops_the_whole_pass(self):
        for failure in ('authentication', 'source'):
            with self.subTest(failure=failure):
                original = self.owner.call
                def remote_call(operation, data=None):
                    if failure == 'authentication' and operation == 'identity':
                        raise DomainError('owner_auth_failed_reconnect_operator', 401)
                    result = original(operation, data)
                    if failure == 'source' and operation == 'attention':
                        result['source'] = 'unknown'
                    return result
                with patch.object(self.owner, 'call', side_effect=remote_call):
                    result = self.renewal().tick()
                self.assertFalse(result['checked'])
                self.assertEqual(result['renewed'], 0)
                self.assertEqual([profile.read_bytes() for profile in self.profiles], self.before)
                self.assertEqual(result['error'], 'owner_auth_failed_reconnect_operator'
                    if failure == 'authentication' else 'operator_source_unverified')


if __name__ == '__main__':
    unittest.main()
