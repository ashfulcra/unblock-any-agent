# Native declared-update detection implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Detect a missed declared update independently of the ended worker, retaining one scoped investigation and its history.

**Architecture:** Extend native signed records with work updates and scoped overdue observations. A separate check-only monitor records deterministic observations and reconciles private receipts; the existing dashboard and recovery expose them independently of human questions.

**Tech Stack:** Existing Svelte/Node native service, Python3.13+ standard library monitor/SQLite, pinned MCP2.3.0 and modern TypeScript MCP SDK.

**Spec:** ../specs/2026-10-16-native-deadline-detection.md

## Global constraints

- Existing authentication, annotation, sealing key and saved Fulcra deployment; no new OAuth client, database, or owner refresh credential in a worker/monitor.
- Working deadline after server time and within30days; terminal update deadline null. States working/completed/cancelled.
- Explicit reviewed parents; retained concurrent/history/pending/uncertain work. Listener observations cannot assert worker progress.
- M2-3 timeout90minutes; two retries and two harness-fix attempts. Full M3attempt2 remains incomplete with one retry.
- Public package version0.5.0 after this feature; owner/operator modules remain excluded. Local proof retains its separate contract.

## Review focus

- Retry of an already persisted update after its deadline/new head returns the old receipt; Task1 pins it.
- Concurrent deadline changes cannot hide a conflict or authorize an old observation; Task1 pins it.
- Source failure after ingest and then definite rejection preserves earlier uncertain receipts; Task2 pins it.
- Restart, revoked profile and changed source/scope cannot erase or repurpose the monitor ledger; Task2 pins it.
- Closing a linked expectation does not remove unanswered human needs or uncertain actions; Task1 pins it and Task2 checks the deployed view.

### Task1: Native expectation and observation contract

**Files:** create `web/src/lib/server/unblock-expectations.js`, `web/tests/unblock-expectations.test.js`; modify `unblock-core.js`, `unblock-api.js`, `unblock/native_client.py`, `unblock/native_mcp.py`, `web/src/lib/server/unblock-mcp.js` and their tests.

**Interfaces:** `projectExpectations(records, now)` returns `{id,agent_id,history,revisions,observations,current_observations,state}`. Native `work_update`/`observe_due` inputs are fixed by the spec. Attention adds `expectations`. MCP `record_work_update` maps to native updates; existing contracts remain valid.

- [ ] Write failing fixture tests for scoped declaration, early/due observation, repeated checks, update/history/conflicts, historical retry and linked unanswered/uncertain requests. Run `cd web && npm test`; confirm failures identify absent behavior.
- [ ] Implement projection, service authorization/publication and CLI/MCP schemas, including strict scalar/reference/time/parent validation and actual server-time checks. Keep non-request records out of the existing request projection.
- [ ] Run web tests/check/build and native client/MCP Python tests; require real modern+legacy eight-tool discovery and harmless recovery. Commit the independently testable contract.

### Task2: Independent monitor, dashboard and live proof

**Files:** create `unblock/native_monitor.py`, `tests/test_native_monitor.py`, `web/src/lib/components/ExpectationsDashboard.svelte`, `docs/native-detection.md`; modify `NeedsDashboard.svelte`, skill setup, package builder/generated exports, native HTTP/pilot/listener docs and execution ledger.

**Interfaces:** `NativeMonitor(client, environment, state).tick()` returns checked/source status, persisted/pending observation receipts and retained errors. Ledger binds actual source, principal, environment and allowed agents. CLI has `--config`, `--environment`, `--state`, `--interval` and `--once`; no route execution or scheduler installation.

- [ ] Write failing monitor tests: delayed due update with separate subprocess, repeated/restarted observation, pending readback, source loss after ingest, rejected retry preserving uncertainty, expiry/revocation and ledger rebinding. Run targeted unittest; require absent behavior failures.
- [ ] Implement bounded check-only loop, strict private SQLite journal and exact readback reconciliation. Add dashboard investigation/history/manual check with retained error state; expose source failure and unverified persistent coverage accurately.
- [ ] Rebuild both self-contained0.5.0 exports with generator; verify no credential/owner/operator files, exact generated trees, strict platform/package validation and actual manifest launches from a clean cache.
- [ ] Execute M2-3 live: enroll separate synthetic worker/listener, declare a deadline then end worker, pre-start monitor, observe one investigation in API/browser/replacement recovery, repeat/restart without duplicate, update worker and retain history plus linked human need. Revoke/read back both grants, verify denial, stop probes/proxy. Keep full M3 incomplete.
- [ ] Run required suites/check/build. Request one fresh whole-branch review under executing-plans, preserve raw report and perform one evidence-backed fix pass.
- [ ] Publish PR/CI/read back exact source and main; require real deployed Evaluator evidence before REVIEW/MARK_COMPLETE/RUN_COMPLETE. Update own V5/checkpoint and workspace obligations. Commit the completed slice.
