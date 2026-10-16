# Remote issuer integration implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the remote Unblock resource through existing Fulcra sign-in with a durable, narrow worker authorization.

**Architecture:** Add an isolated resource branch to the existing issuer, with durable compare-and-swap transaction state and a bridge to the current native grant API. Existing Fulcra MCP flows continue through the original provider. Publish discovery only after the real issuer flow passes.

**Tech Stack:** Existing issuer Python/FastMCP 3.4.7/MCP 1.28.1/google-cloud-storage 3.15.1; existing Unblock SvelteKit/native API.

**Spec:** `docs/superpowers/specs/2026-10-16-remote-issuer-integration.md`

## Global constraints

- The dashboard and personal forks use supplied Fulcra webapp authentication without a newly registered OAuth client or external database.
- Keep owner access/refresh credentials server-side; workers receive only native grants.
- Preserve existing Fulcra resource behavior; no discovery for an unimplemented issuer flow.
- Resource/code/refresh state must survive two instances; no process-local locking or mounted file writes as cross-instance atomicity.
- Preserve pending effects and recovery obligations. No actual ChatGPT web, event or marketplace claim from unit tests.

## Review focus

- Duplicate `resource` fields must fail before any credential or native API effect.
- One OAuth client used concurrently by two humans must not cross credentials or projects.
- A lost successful native enrollment response must reconcile the original grant, not create another.
- Removing an owned deployment or changing its domain must prevent later renewal/credential forwarding.
- A code replay must not issue a second access token, including across service instances.

## Task 1: Resource guard at the actual token boundary

**Files in the issuer repository:** Create `fulcra_mcp/unblock_resource.py`, `tests/test_unblock_resource.py`; modify `fulcra_mcp/main.py` only to mount the new branch and `fulcra_mcp/provider.py` to dispatch resource-specific operations.

**Interfaces:** `parse_resource(form_items: list[tuple[str, str]]) -> str | None` rejects duplicate resource values. `require_resource(requested: str | None, bound: str, *, refresh: bool) -> str` returns the bound resource or raises the SDK `TokenError` before exchange. Request context is scoped to the individual ASGI request and reset in `finally`; never process-global mutable state.

- [ ] Write tests against real `TokenHandler`: matching code resource passes, mismatched/missing/duplicate code resource denies before `exchange_authorization_code`; refresh omitted/exact passes, different/duplicate denies before `exchange_refresh_token`.
- [ ] Run `uv run pytest tests/test_unblock_resource.py -q`; confirm failures on the pinned unguarded handler, rather than on missing fixtures.
- [ ] Implement the guard before the SDK discards requested resource. Preserve the original handler for original-resource requests; route known new authorization codes/refresh tokens by durable namespace when resource is omitted.
- [ ] Run focused tests and `uv run pytest tests/test_sdk_contract.py tests/test_provider_persistence.py -q`; commit guard and regression coverage.

## Task 2: Durable one-time transaction and refresh state

**Issuer files:** Create `fulcra_mcp/unblock_state.py`, `tests/test_unblock_state.py`; extend `fulcra_mcp/settings.py` using the existing state bucket setting.

**Interfaces:** `StateStore.create(key: str, value: dict) -> int`, `read(key: str) -> tuple[dict, int] | None`, `replace(key: str, value: dict, generation: int) -> int`. Implement GCS conditional writes under `unblock/v1/`; generation conflicts never become success. Store transaction binding, status, expiry and frozen effect intent/receipt. Hash bearer-derived record keys.

- [ ] Write tests with two store clients over one controllable generation backend: one winner for code consumption; process replacement recovery; state expiry; unavailable store; conflicting refresh; same-client/two-human separation; redacted logging and rejected malformed keys.
- [ ] Run `uv run pytest tests/test_unblock_state.py -q` and observe failures for absent CAS implementation.
- [ ] Implement the GCS adapter and state transitions `pending -> claimed -> completed | uncertain`; no automatic takeover of an uncertain external effect. Code replay cannot reissue and schedules revocation of any linked grant. Retain frozen refresh replacement for a 120-second exact retry window; changed bindings always fail.
- [ ] Verify adapter method signatures against google-cloud-storage 3.15.1, run tests, then run a bounded two-client disposable-object CAS probe in an authorized test bucket before deployment. Commit source and tests; label the unit backend separately from the real bucket probe.

## Task 3: Verified project consent and native grant bridge

**Issuer files:** Create `fulcra_mcp/unblock_bridge.py`, `fulcra_mcp/unblock_consent.py`, `tests/test_unblock_bridge.py`, `tests/test_unblock_consent.py`; modify `fulcra_mcp/provider.py` for the isolated new-resource callback dispatch.

**Interfaces:** `resolve_owned_project(owner_credentials, project_id: str, resource: str) -> ProjectBinding`; `enroll_worker(binding, frozen_intent: dict) -> NativeGrantReceipt`; `reconcile_enrollment(binding, frozen_intent: dict) -> NativeGrantReceipt | None`. `ProjectBinding` carries verified subject, project ID, canonical HTTPS origin, agent and environment. Use the current native API contract in `web/src/lib/server/unblock-api.js`; do not invent a second worker token format.

- [ ] Write tests for foreign/missing projects, canonical-domain mismatch, userinfo/ports/redirects, source lookup failure and changed ownership: all deny before dashboard requests. Add concurrent same-client/two-human consent and CSRF/replayed-form tests.
- [ ] Add lost-response enrollment and renewal tests: exact intent/receipt retained; no blind duplicate grant or upstream refresh. Assert native token expiry and scope, both resource replay directions, and original clients unchanged.
- [ ] Observe failing tests, implement the consent/binding/bridge, and run `uv run pytest tests/test_unblock_bridge.py tests/test_unblock_consent.py tests/test_provider_persistence.py tests/test_refresh_lock.py -q`; commit. Review the complete shared-service diff before any rollout decision.

## Task 4: Live issuer acceptance, then resource discovery

**Unblock files:** Modify `web/src/lib/server/unblock-mcp.js`; create the protected-resource metadata route using the verified deployed issuer URL; extend `web/tests/unblock-mcp.test.js`. Keep local exports at eight tools.

- [ ] First test the deployed issuer with a bounded authorized worker: real login/consent, code exchange, replacement recovery, reconnect/expiry, refresh uncertainty, revocation and both replay directions. Read back every source effect and revoke all temporary grants. Record shared-service deployment authority and exact source revision.
- [ ] Write failing metadata/challenge tests for the actually accepted issuer/resource and denial for unknown issuers. Implement metadata only after the preceding real flow passes; run `npm test`, `npm run check`, `npm run build` in `web`.
- [ ] Verify the actual ChatGPT web connection and replacement recovery. Preserve failures; browser/SDK transport success alone is insufficient. Commit only nonsecret evidence and report the exact remaining acceptance gaps.
- [ ] Plan durable MCP Events separately after authenticated connection acceptance; keep per-environment listeners available in the meantime.
