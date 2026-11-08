# Unattended Runtime Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Ash instructed execution without another approval round.

**Goal:** Renew existing connections independently of this chat and prevent blind replay after uncertain dispatch.

**Architecture:** Trusted Python runtime reuses NativeOwner/Renewal and the existing private ledgers. Explicit launchd supervision is outside worker exports. NativeListener retains uncertain claims until explicit reconciliation.

**Tech Stack:** Python standard library, existing Fulcra CLI, macOS launchd for this authorized local deployment.

**Spec:** ../specs/2026-11-08-unattended-runtime-design.md

## Global Constraints

- Preserve three-hour model cadence, one-hour grant maximum and exact existing family scopes.
- No copied owner credentials, new worker/listener identity, arbitrary host launcher or public release.
- Source failure preserves obligations; process exit and launch receipts do not prove checked source or continuation.
- Deployment uses only selected14 and selected2; frozen maintainer family remains separate.

## Review Focus

- Config/state/profile path collisions or changed selections must fail closed.
- Failed owner reads must not produce healthy status or discard last success.
- Concurrent runtime processes cannot race; existing renewal state locks remain authoritative.
- Unknown post-launch readback must not allow a replacement listener to repeat an effect.
- Restarting a runtime proves renewal only, never model pickup.

### Task 1: Preserve uncertain dispatch claims

**Files:** unblock/native_listener.py; tests/test_native_listener.py; generated plugin copies.
**Interfaces:** Existing tick/recover methods; no protocol change.

- [ ] Write regression using a real subprocess effect followed by unavailable source; replacement tick must not repeat it.
- [ ] Observe RED; retain expired claim on unknown post-launch source; explicit recover is required.
- [ ] Observe GREEN; run complete Python/MCP suite and regenerate/verify export parity.

### Task 2: Independent trusted renewal runtime

**Files:** unblock/native_runtime.py; tests/test_native_runtime.py; docs/native-renewal.md.
**Interfaces:** RenewalRuntime(config).tick() returns/persists sanitized health; run(stop_event) owns one private process lock and repeats bounded existing renewal checks.

- [ ] Write tests for real renewal fixture, source outage/recovery, preserved pending intent, config changes, overlapping targets and process lock.
- [ ] Observe RED; implement minimal runtime with fixed selected operator paths, private atomic health and no raw exception logging.
- [ ] Observe GREEN; run full suite and inspect exports for exclusion of trusted runtime.
- [ ] Commit source; perform fresh whole-change review and address important findings with regression tests.
- [ ] Deploy exact reviewed source to an isolated private runtime directory and configure only the existing two selected operators.
- [ ] Verify actual checked renewals, private profile readbacks, launchd process restart and retained health after restart. Record exact unperformed host pickup limits.
- [ ] Publish draft source PR/read back, record accepted own V5 evidence and exact exit check.
