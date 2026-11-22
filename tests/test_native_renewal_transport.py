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

    def fresh_operator(self):
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
        self.assertEqual(self.renewal().tick()['renewed'], 2)
        self.before = [profile.read_bytes() for profile in self.profiles]
        self.owner.clock = 1040

    def renewal(self):
        return Renewal(self.owner, self.config, self.state, lease_seconds=60,
            renew_before=30, now=lambda: self.owner.clock)

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
                        raise urllib.error.HTTPError(self.owner.url, status, 'response error', None, None)
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
