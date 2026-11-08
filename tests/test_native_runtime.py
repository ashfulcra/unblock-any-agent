import json
import os
from pathlib import Path
import tempfile
import unittest

from unblock.client import private_read, private_write
from unblock.native_renewal import replace_private
from unblock.store import DomainError
from test_native_renewal import ANCHOR, OwnerFixture

try:
    from unblock.native_runtime import RenewalRuntime
except ImportError:
    RenewalRuntime = None


class NativeRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(RenewalRuntime, 'Independent trusted renewal runtime is missing')
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.owner = OwnerFixture()
        self.profile = self.root/'worker.json'; self.operator = self.root/'operator.json'
        self.state = self.root/'state.json'; self.health = self.root/'health.json'
        self.config = self.root/'runtime.json'
        private_write(self.profile, {'transport':'fulcra-native','url':self.owner.url,'token':'original-secret'})
        private_write(self.operator, {'url':self.owner.url,'owner_id':'owner','enrollments':[{'anchor_grant_id':ANCHOR,'profile':str(self.profile)}]})
        self.settings = {'operators':[{'config':str(self.operator),'state':str(self.state)}], 'health':str(self.health),'interval':60}
        private_write(self.config, self.settings)

    def runtime(self):
        return RenewalRuntime(self.config, owner_factory=lambda url:self.owner, now=lambda:self.owner.clock)

    def test_pending_outage_and_restart_preserve_intent_and_last_success(self):
        runtime = self.runtime()
        self.assertFalse(runtime.tick()['healthy'])
        pending = private_read(self.state)['entries'][ANCHOR]['pending']['body']
        self.owner.publish(); self.assertTrue(runtime.tick()['healthy'])
        healthy = private_read(self.health); self.assertEqual(healthy['last_success_at'],1000)
        self.owner.clock += 10; self.owner.offline = True
        failure = self.runtime().tick()
        self.assertFalse(failure['healthy']); self.assertEqual(failure['last_success_at'],1000)
        self.assertEqual(private_read(self.profile)['expires_at'],pending['expires_at'])
        self.owner.offline = False
        self.assertTrue(self.runtime().tick()['healthy'])
        self.assertNotIn('secret', self.health.read_text()); self.assertNotIn('sealed-',self.health.read_text())
        self.assertEqual(self.health.stat().st_mode & 0o777,0o600)

    def test_lost_enrollment_response_is_not_erased_or_replaced(self):
        self.owner.lose = True; self.assertFalse(self.runtime().tick()['healthy'])
        body = private_read(self.state)['entries'][ANCHOR]['pending']['body']
        self.owner.publish(); self.assertTrue(self.runtime().tick()['healthy'])
        self.assertEqual(self.owner.calls[-1],body)
        self.assertEqual(len(self.owner.accepted),1)

    def test_changed_operator_or_runtime_selection_refuses_renewal(self):
        runtime = self.runtime(); self.owner.offline = True; runtime.tick()
        replace_private(self.operator, {**private_read(self.operator),'owner_id':'different'})
        self.assertFalse(runtime.tick()['healthy'])
        self.assertEqual(self.owner.calls,[])
        with self.assertRaises(ValueError): self.runtime()

    def test_profile_health_state_and_group_aliases_are_rejected(self):
        for field,target in [('health',str(self.profile)),('health',str(self.operator)),('health',str(self.state))]:
            replace_private(self.config,{**self.settings,field:target})
            with self.assertRaises(ValueError):self.runtime()
        replace_private(self.config,{**self.settings,'operators':self.settings['operators']*2})
        with self.assertRaises(ValueError):self.runtime()

    def test_second_operator_cannot_share_a_managed_profile(self):
        other = self.root/'other.json'; private_write(other,private_read(self.operator))
        replace_private(self.config,{**self.settings,'operators':self.settings['operators']+[{'config':str(other),'state':str(self.root/'other-state.json')}]})
        with self.assertRaises(ValueError):self.runtime()

    def test_process_lock_excludes_another_runtime_and_releases(self):
        one=self.runtime();two=self.runtime()
        with one.lock():
            with self.assertRaises(DomainError):
                with two.lock():self.fail('overlapping runtime entered')
        with two.lock():pass

    def test_tick_refuses_changed_runtime_file_without_adopting_it(self):
        runtime=self.runtime();replace_private(self.config,{**self.settings,'interval':120})
        result=runtime.tick();self.assertFalse(result['healthy']);self.assertEqual(self.owner.calls,[])

    def test_failure_in_one_group_does_not_starve_an_independent_group(self):
        second=self.root/'second';second.mkdir();other=OwnerFixture();other.url='https://other.invalid'
        profile=second/'worker.json';operator=second/'operator.json'
        private_write(profile,{'transport':'fulcra-native','url':other.url,'token':'second-secret'})
        private_write(operator,{'url':other.url,'owner_id':'owner','enrollments':[{'anchor_grant_id':ANCHOR,'profile':str(profile)}]})
        replace_private(self.config,{**self.settings,'operators':self.settings['operators']+[{'config':str(operator),'state':str(second/'state.json')}]})
        owners={self.owner.url:self.owner,other.url:other};self.owner.offline=True
        runtime=RenewalRuntime(self.config,owner_factory=owners.__getitem__,now=lambda:1000)
        self.assertFalse(runtime.tick()['healthy']);self.assertEqual(len(other.calls),1)
