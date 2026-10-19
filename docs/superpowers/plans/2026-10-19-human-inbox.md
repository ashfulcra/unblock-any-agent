# Human inbox implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline. Ash has authorized autonomous continuation in this existing maintainer session; create no agent session or listener.

**Goal:** Review and answer agent decisions from chat with the same identity, waiting time, context and actual continuation evidence as the dashboard.

**Architecture:** Add a separate, explicitly configured human stdio entry point. Resolve its dashboard from an authenticated, owner-bound Fulcra deploy project before forwarding an in-memory existing CLI credential. Worker MCP remains worker-only. An MCP Apps view and concise text fallback consume the same checked inbox and reviewed decision tools. Persist pending answer intents privately and reconcile exact native readback after uncertainty or restart.

**Tech stack:** Python standard library, existing pinned MCP 2.3.0, self-contained HTML/JS MCP Apps resource.

**Spec:** ../specs/2026-10-19-decision-workspace.md and R19 in ../../requirements.md.

## Constraints

- No new account, OAuth client, service scope, worker/listener grant, automation or agent session.
- Owner configuration is explicit and private; never fall back from expired worker credentials to owner authentication.
- Preserve stable answer intent, exact reviewed question and complete current answer set; reading is not completion.
- Distinguish source/package/SDK proof from actual installed host UI, remote ChatGPT OAuth, and wake coverage.

## Review focus

- A changed CLI account or deploy project must fail before any credential is forwarded to the dashboard.
- A changed question or answer set must require renewed review; retain an already uncertain original submission.
- A lost write response must reconcile the same answer after restart without changing intent or authorizing agent work.
- A failed read must retain known work and pending answers; no empty inbox or completed claim.
- Untrusted question/context text must render as text and must not choose tool names, routes or identities.

## Task 1 — Checked human inbox and durable answers

Files: `unblock/human_inbox.py`, `tests/test_human_inbox.py`.

- [x] Test owner/project mismatch, concise checked inbox, full snapshot, stale review, lost response and restart, changed-intent rejection, and source failure retention.
- [x] Implement `HumanInbox` with explicit private project/owner/state configuration; fixed platform API verification; inbox, get decision, and answer only.
- [x] Verify exact recorded answer identity/revision/content. Pending is not saved proof; saved is not resumed proof.
- [x] Run focused tests and commit.

## Task 2 — In-chat tools and interactive decision view

Files: `unblock/human_mcp.py`, `scripts/run_inbox_mcp.py`, `unblock/ui/inbox.html`, tests, package builder and setup reference.

- [x] Test discovery of only human inbox/get/answer tools, UI resource metadata and text fallback; worker discovery stays unchanged.
- [x] Implement a standard MCP Apps resource with agent/time/context cards, one full decision form, retained drafts/pending retries and source error handling. Use the host tool bridge, never browser credentials or arbitrary URLs.
- [x] Package support files with an explicit optional human launch recipe; preserve default worker configuration and the existing private plugin identity/audience.
- [x] Verify SDK discovery and bounded actual-source synthetic answer recovery, then actual supported-host loading/rendering when available. Record any exact boundary rather than inferring acceptance.

## Task 3 — Review and publication

- [x] Run applicable Python/web/package checks; reuse existing reviewer session for the human change.
- [x] Publish source through a reviewable PR and read back. Update the existing private plugin only with reviewed changed files, retaining metadata and auth settings.
- [x] Record actual deployment/UI/API/host evidence in the existing harness and own V5 task. Retain remote OAuth/operator and public listing prerequisites separately.

## Execution evidence — 2026-10-19

Implemented the dashboard and separate human inbox inline under Ash’s autonomous instruction. Dashboard and human path received independent review in existing reviewer sessions; the identified stale-source, hidden-answer, original-date, reviewed-snapshot, draft race and rejected-save recovery defects were fixed and rechecked. Fresh verification: 108 Python tests, 74 web tests, Svelte check with zero errors (two inherited login warnings), package check and loopback smoke.

The existing deployment was updated. Real-source browser tests covered desktop/narrow layouts, original waits, context, search/map/filter, preserved drafts, revised-question review, checked save, source failures and actual same-worker continuation without repeating the existing synthetic effect. The human inbox passed actual stdio discovery/resource/live reads and a bounded MCP Apps compatibility preview save plus native continuation. The existing private plugin was updated to 0.6.0 with affected-file readback; default source exports keep the worker connection unchanged and document the optional explicit human connection.

Installed ChatGPT/Codex UI acceptance is **not complete**. No Unblock tools are exposed to this active host session after the private release, and computer control is denied for the Codex app. No new agent/task session was created to evade that boundary. A supported existing-host connection reload and invocation remains the exact acceptance prerequisite. Remote ChatGPT web still needs the separately authorized issuer deployment. The source, SDK, compatibility preview and saved package are distinct evidence, not host acceptance.

Ruling: preserve private operational evidence and pending intents rather than deleting the execution record; current owner/worker bindings and unresolved external prerequisites must survive recovery.

## Returned PR18 review and changed host evidence

The returned review identified a real multi-intent recovery lock and silent active-board overflow. Pending answers are now keyed by immutable intent, with legacy storage migration and separate earlier-answer verification. The current reviewed question can receive a fresh answer without erasing earlier uncertainty; old readback preserves newer drafts in both views. Active lanes provide explicit access to all work. Actual-source UI-handler regressions and client restart tests cover these cases.

The human inbox tools subsequently loaded in this same existing thread. Actual get/review/answer calls and exact same-worker synthetic continuation succeeded without a new agent session or repeated effect. The earlier reload prerequisite became obsolete. Own requests can now be withdrawn with evidence and the exact current answer set, including zero answers; uncertain effects still block withdrawal, later answers invalidate the old snapshot, and history remains retained. Hosted and stdio contracts agree. No owner answer was fabricated. Visual Apps rendering remains separate from actual tool transport acceptance.
