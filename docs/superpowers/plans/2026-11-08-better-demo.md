# Better Unblock Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan inline, then request one fresh whole-branch review.

**Goal:** Present a clear, rehearsed two-agent decision-to-result story by November9 afternoon.
**Architecture:** An exact-ID presentation mode over existing owner source and answer controls. Existing scoped local demo participants prepare fresh sample work; historical trials remain immutable. No new backend/auth/receiver service.
**Tech Stack:** Svelte5, Node tests, native Fulcra source, supported Codex thread tools.
**Spec:** docs/superpowers/specs/2026-11-08-presentation-view.md

## Global Constraints

- Existing owner sign-in, scopes, full revision/all-answer review and uncertain intent semantics remain intact.
- No visual-rendering claim while browser control is disabled.
- No new schedule, service, credential, recipient or public release.
- Provisional deadline November9 14:00America/New_York; never attribute that time or demo choices to Ash.

## Review Focus

- Malformed/partial selection must fail visibly without broadening the view.
- Current source failure must preserve last-known cards and suppress fresh-success claims.
- Completed/withdrawn/conflicting/uncertain states must remain distinct.
- Hash navigation must not open an unrelated request in a presentation.
- Agent evidence and user-controlled URL values must render as text, not HTML or executable instructions.

### Task1: Focused source-backed presentation

**Files:** create web/src/lib/presentation.js, web/src/lib/components/Presentation.svelte, web/tests/presentation.test.js; modify NeedsDashboard.svelte and dashboard-answers.test.js.
**Interfaces:** parsePresentation(search), presentationLink(ids), presentationRows(rows, ids), presentationStage(row); component consumes rows/IDs/grants/source state and opens existing detail panel.

- [ ] Write tests for exact selection/order, malformed/duplicate/overlong/missing IDs, saved answer vs folded progress, conflicts/uncertainty, and compiled Svelte rendering/escaping.
- [ ] Run tests and observe RED; implement the minimal helpers/component and integrate with guarded source/answer path.
- [ ] Run targeted/full web tests, check and build. Record actual evidence and commit.

### Task2: Fresh two-agent demo and deployment

**Files:** docs/demo-runbook.md; private better-demo-20261109 evidence outside source.
**Interfaces:** Existing exact mapped selected2 profiles/threads; native need/recover/action/progress, supported send_message_to_thread with durable intent/receipt.

- [ ] Check current native source and responsible models, then dispatch fresh clearly labeled rehearsal assignments with no physical/account side effects.
- [ ] Record only explicitly simulated rehearsal decisions; route exact current source/all answers once, verify actual model/report effects, then prepare distinct unanswered live requests.
- [ ] Record timing and output hashes; create exact presenter link, three-minute runbook and explicit prompted fallback.
- [ ] Fresh whole-branch review, fix substantive findings with regressions, publish/read back source, deploy existing main owner project and verify actual API/bundle.
- [ ] Record visual evaluation limitation separately; preserve pending obligation and exact own exit check. Never mark deployed UI acceptance complete without observation.
