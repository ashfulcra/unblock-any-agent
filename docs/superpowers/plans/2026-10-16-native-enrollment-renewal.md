# Native Enrollment Renewal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Renew explicitly authorized native worker/listener profiles through an existing trusted Fulcra CLI operator without broadening their scope.

**Architecture:** A separate operator uses existing CLI authentication in memory and fixed owner API calls against a saved origin. Durable enrollment intents and an exclusive private ledger protect retries; exact readback precedes atomic profile replacement. Enrolled workers and listeners never receive owner credentials or renewal authority.

**Tech Stack:** Python standard library, existing native API and Fulcra CLI authentication.

**Spec:** ../specs/2026-10-16-native-enrollment-renewal.md; first-release continuity/pickup requirements.

## Global Constraints

- No new registered OAuth client, external database or owner refresh-token copy.
- Renew existing enrollment anchors only, preserving role, environment and explicit agent scope.
- Owner revocation stops renewal; a new profile is usable only after exact grant readback.
- An uncertain pending write keeps its body/expiry/intent; no receipt establishes persisted authorization.
- Owned mode0600 profiles and an exclusive private state lock; no automatic scheduler installation.
- Source failures preserve known pending work and expose the reconnect action.

## Review Focus

- Lost enrollment response/readback and restart must converge on one grant.
- Revocation during renewal cannot silently produce a usable replacement.
- A changed owner account, origin, enrollment scope or target file must stop safely.
- Concurrent operator ticks cannot overwrite each other's pending intents/profiles.
- Expired/revoked owner CLI access cannot be mistaken for quiet or successful renewal.

### Task 1: Fixed owner transport

**Files:** Create unblock/native_owner.py and tests/test_native_owner.py.
**Interfaces:** NativeOwner(url, access_token).call(operation, body=None); allow only identity,attention,prepare_enrollment,enroll. Cookie credential plus exact saved Origin for writes; fixed HTTPS/explicit loopback origin, no proxy/redirect forwarding. Existing CLI token retrieved only in memory via fixed executable argv, checked through authenticated owner identity.

- [x] Write and run failing real HTTP fixture tests for owner cookie/origin, role checks, redirect/proxy refusal and sanitized failure.
- [x] Implement minimal transport and fixed existing-CLI token acquisition; make tests pass.

### Task 2: Durable bounded renewal

**Files:** Create unblock/native_renewal.py and tests/test_native_renewal.py; add the read-only enrollment metadata endpoint and preparation helper, update contained setup reference and native pilot/listener docs after verification.
**Interfaces:** Renewal(owner, private_config, private_state).tick(); config maps a saved origin and existing anchor grant IDs to private profile paths. First verified owner read freezes scope/destination; subsequent ticks validate anchor/latest revocation and unchanged scope. Persistent pending body/expiry/intent precedes enrollment; exact visible grant readback precedes atomic profile rotation. Only safe public status is returned. CLI --once or bounded --interval loop uses existing operator authentication; no scheduling/persistence installation.

- [x] Write failing tests for pending response loss/restart, fixed expiry, frozen scope, revoked anchors/latest grants, private target rejection and simultaneous ticks.
- [x] Implement smallest operator/ledger/profile replacement; run full Python and relevant package regressions.
- [x] Run actual short-lived renewal and expired-old/replacement-native checks with dedicated private synthetic anchors, preserving the listener's identity/scope/ledger. Do not weaken production credential limits for the test.
- [ ] Fresh final review, one RED-to-GREEN fix pass, source scan/publication/readback; retain actual coverage and remaining release prerequisites.

Execution: Ash's standing instruction supplies autonomous inline execution. This chooses a bounded existing-auth operator route; general public remote-MCP authorization and persistent host startup remain separate work. Record implementation rulings/evidence in the plan's private ledger.
