# Native Host Pickup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the deployed native pilot to real agent entry points and an independently running environment listener, then prove delayed Claude pickup.

**Architecture:** Retain native persistence and template sign-in. Extend enrollment with a separate listener role bound to an environment and explicit agent IDs; it can check/recover and report its own delivery observations, but cannot mutate agent work. Add a native HTTP client and native MCP tools rather than forcing the native service into the local SQLite API. Reuse the tested local dispatch claim/route rules where applicable, preserving one ledger per environment and explicit crash reconciliation.

**Tech Stack:** SvelteKit/Node, Python standard library, existing pinned MCP SDK, Claude Code restricted synthetic sessions.

**Spec:** ../specs/2026-10-16-agent-work-pickup.md and ../specs/2026-10-16-unblock-first-release.md; private Fulcra M3.

## Global Constraints

- Existing session-bound credentials remain bounded to the originating access token; unattended renewal is not invented.
- Listener read/route permission does not grant progress, answers, enrollment or action authority; its delivery observations remain distinct.
- Stable agents and local runtime routes remain separate; no arbitrary command is accepted from native messages.
- Source failures preserve pending work and cannot establish quiet.
- Duplicate delivery and concurrent listeners must not overlap workers; expired claims need explicit reconciliation.
- Official host installs, ChatGPT route, remote MCP OAuth and marketplace eligibility remain independently verified outcomes.
- All web changes use the existing Fulcra harness and saved deployment project.

## Review Focus

- A listener cannot mutate work or read an agent omitted from its explicit grant.
- A stale/expired/revoked grant stops polling/dispatch and preserves known pending items.
- Wrong environment/neighbor route and simultaneous checks do not execute another worker.
- A queued launcher receipt is not acknowledgment; unchanged progress cannot prove fresh continuation.
- A timed-out worker stops before claim release; interrupted uncertain dispatch needs recovery evidence.

### Task 1: Native listener enrollment and identity

**Files:** Modify web/src/lib/server/unblock-api.js, native API route, NeedsDashboard.svelte and web/tests/unblock-api.test.js.
**Interfaces:** Enrollment accepts kind agent/listener, environment and listener agent_ids; sealed grant contains immutable scope. GET identity/attention returns verified principal metadata. Listener operations permit identity/attention/recover plus delivery-only observations for explicitly allowed agent IDs. Delivery records cannot answer, change context, settle actions or report agent progress. Existing M2 agent grants default to agent kind.

- [x] Write failing authority tests for read-only listener, allowed/foreign agent recovery, environment identity and expired/revoked roles.
- [x] Implement the smallest enrollment/identity extension; owner UI exposes explicit role/environment/agent scope.
- [x] Run complete web tests/check/build and deploy through the saved project; verify actual narrow listener access.

### Task 2: Native CLI/MCP entry points

**Files:** Create unblock/native_client.py and unblock/native_mcp.py; modify scripts/run_mcp.py, scripts/build_plugins.py, shared skill setup reference and package docs; create tests/test_native_client.py and tests/test_native_mcp.py.
**Interfaces:** NativeClient.from_file uses a private profile with transport fulcra-native, URL and token; call(operation,body=None) accesses only fixed native operations with no redirects/proxies. CLI reads JSON from a file/stdin without credentials in argv. Native MCP exports ask_for_help, recover_work, get_work, revise_need, record_progress, begin_action and reconcile_action, with signatures matching the native immutable-revision/answer-set contract. Existing local profile path remains supported unchanged.

- [x] Write failing client tests for transport, malformed origin, proxy/redirect protection, source failure and no role escalation; run RED.
- [x] Implement client and seven native tools; launch selection uses the explicit profile transport. Verify actual stdio discovery/recovery with enrolled native agent profile and both copied export commands.
- [x] Update setup instructions with bounded expiry, native-vs-loopback distinction and canonical source links. Run package and full Python checks.

### Task 3: Native environment listener and real Claude proof

**Files:** Create unblock/native_listener.py, unblock/native_worker.py, tests/test_native_listener.py and tests/test_native_worker.py; retain production smoke fixtures privately; update listener guide/native pilot.
**Interfaces:** A listener profile is verified through native identity, then checks permitted requests and routes metadata-only payloads to private local argv definitions. Reuse private route validation, SQLite dispatch claims and process-group timeout cleanup from the existing local listener without requiring the native service to implement its API. Snapshot identity includes question revision, current answer IDs, uncertain/settled actions and route. Confirm fresh authorized progress by record IDs, not a launcher receipt. Bound retries to three attempts per work/route snapshot; preserve a linked delivery gap and exact operator recovery action.

- [x] Write failing tests for role/environment isolation, no overlap, lost source retention, queued-vs-ack and explicit expired-claim reconciliation.
- [x] Implement native tick/listen/recover commands and a restricted synthetic native worker/Claude route. A separate process must exist before a synthetic human answer.
- [x] Run delayed production answer → listener → native Claude restricted session → exact artifact readback/progress; repeat replacement and stopped-route negative cases. Keep private state outside source.
- [ ] Fresh independent review of complete slice, one evidence-backed fix pass, then source/CI/readback and real harness evidence. Do not mark full M3 complete while ChatGPT/renewal/marketplace outcomes remain open; preserve exact remaining tasks.

Self-review: every failure class maps to Task 1/2/3 tests; hosted scope and actual Claude behavior require live checks. This adds a native transport and uses existing verified dispatch mechanics; it does not inherit local backend topology or claim native wake on other platforms. Ash's standing continuous-execution instruction supplies the execution method; proceed inline without repeating architecture/permission prompts for reversible authorized work.
