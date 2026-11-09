# Renewal Expiry Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline, followed by one fresh whole-branch review.

**Goal:** Avoid new automatic grant records when they cannot extend an already verified valid lease.
**Architecture:** Add a small fresh-intent guard to the existing trusted Renewal.tick, after source/scope/profile checks and normal expiry preparation. Preserve every pending recovery and initial bootstrap path. Deploy the reviewed helper to the existing selected14/2 runtime only.
**Tech Stack:** Python unittest, native Fulcra source, existing launchd supervisor.
**Spec:** docs/superpowers/specs/2026-11-09-renewal-expiry-guard.md

## Global Constraints

- No new scope, participant, identity, service, schedule, credential transfer or public/plugin release.
- Do not suppress pending intent reconciliation or existing binding/revocation/session errors.
- Preserve all records, journals and demo choices; no claim of fixing underlying transport latency.

## Review Focus

- Equal and shorter prepared expiry must leave the valid current profile and native history untouched.
- A restart followed by a real extension must still renew once.
- A lost response/pending intent must settle unchanged even after the current owner limit shrinks.
- Revoked/changed profiles cannot be reported healthy through the guard.
- Bootstrap and actually expired leases must retain their separate behavior.

### Task 1: Guard and regressions

**Files:** unblock/native_renewal.py, tests/test_native_renewal.py.

- [ ] Extend the controlled owner fixture with a prepared absolute expiry.
- [ ] Add tests for equal/shorter expiry across ticks/restart, later extension, pending lost-response recovery, bootstrap, expired lease/session and profile drift.
- [ ] Observe RED for the new no-op behavior, implement the smallest guard, observe GREEN and run full Python/MCP/export checks.
- [ ] Fresh whole-branch review, address concrete findings with regressions, commit/publish/read back source.

### Task 2: Existing runtime deployment

**Files:** private renewal-expiry-guard-20261109 artifacts; existing runtime source only.

- [ ] Preserve exact selected14/2 config/state/profile identities and any pending effects before deployment.
- [ ] Stage the exact reviewed source with rollback retained; replace only the existing runtime source and gracefully restart the same supervisor job.
- [ ] Verify actual replacement PID, fresh checked health, exact selected16 profile/ledger/native effects and unchanged scope/config/other identities.
- [ ] Retain measured evidence and any unperformed live-branch acceptance separately; complete only this owned bug task, keep the demo visual prerequisite pending and perform the exact own exit.
