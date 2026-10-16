# Fulcra Native Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Prove a scoped agent need → authenticated human answer → replacement recovery using the deployed Fulcra app and native persistence.

**Architecture:** Keep official template authentication unchanged. Store immutable logical events in a dedicated Fulcra MomentAnnotation; stable record IDs make identical retries converge, while conflicting semantic payloads receive distinct IDs and remain visible. The owner enrolls agent credentials sealed by a server-only key: credentials carry the existing upstream access token, expire with it, and are checked against native enrollment/revocation history. No new OAuth registration, external database or stored refresh token is needed for this bounded proof.

**Tech Stack:** SvelteKit, Node crypto, built-in Node test runner, Fulcra ingest and data APIs.

**Spec:** ../specs/2026-10-16-unblock-first-release.md; private Fulcra workspace M2.

## Global Constraints

- Preserve supplied sign-in/session behavior.
- Credential-derived agent identity; caller names never grant authority.
- Readback establishes visibility; ingest receipts alone do not establish persistence.
- Answers are distinct from acknowledgment, continuation and action reconciliation.
- Credentials expire with the upstream session; unattended refresh is not claimed by this slice.
- Existing harness annotation/deploy project reused; product data uses a separate annotation.
- Single-owner pilot only; multi-human and installed-host acceptance remain later work.

## Review Focus

- Conflicting concurrent answers remain visible; old progress cannot hide a newer answer.
- Unanswered needs and uncertain actions survive replacement/reconnect.
- Invalid, expired, revoked and neighboring-agent credentials are denied.
- Pending ingestion and failed reads remain unknown/pending, never empty success.
- Modified retry payloads and changed context preserve both histories without applying stale answers.

### Task 1: Native protocol and bounded credentials

**Files:** Create web/src/lib/server/unblock-core.js and web/tests/unblock-core.test.js; add npm test.
**Interfaces:** canonicalRecord(event), projectEvents(records), sealAgent(grant,key), openAgent(token,key), authorizeAgent(grant,events,account,now). Events have schema, event_id, kind, request_id, agent_id, payload, recorded_at. Requests include immutable context/recommendation/next action and logical need key; answers bind request variant; progress binds the exact answer ID set. Action intents remain attention until settled with evidence.

- [x] Write failing tests for retry variants, retained answers/stale progress, open recovery, uncertain actions and credential scope/expiry/revocation.
- [x] Run npm test and observe missing module failures.
- [x] Implement canonical records, conservative projection and AES-GCM bounded credentials. Derive physical record ID from canonical event bytes; semantic conflict variants remain separate.
- [x] Run npm test; require all targeted cases pass.

### Task 2: Real native backend and enrollment

**Files:** Create web/src/lib/server/unblock-api.js and web/src/routes/api/unblock/[...operation]/+server.js; extend .env.example.
**Interfaces:** GET attention/recover; POST enroll/revoke/request/answer/progress/action/settle. Owner uses existing HTTP-only cookie verified by upstream user-info; agent uses sealed credential verified then same upstream user-info and retained grant history. Agent operations force credential agent ID and check request ownership. Owner answers retain actual authenticated account. Writes return pending until exact native readback appears; no unbounded request polling.

- [x] Test native adapter with a deterministic in-memory transport for authority, read failure and pending publication; then exercise actual deployment APIs separately.
- [x] Implement native GET and JSONL POST against official observed endpoints. Configure one pilot annotation and server-only random encryption key outside source.
- [x] Verify real agent request, owner answer and replacement recovery, including foreign-agent denials and native exact readback.

### Task 3: Minimal Needs you experience and real evaluation

**Files:** Modify web/src/routes/+page.svelte; create web/src/lib/components/NeedsDashboard.svelte and docs/native-pilot.md; update web CI for npm test.
**Interfaces:** Human view lists current needs, answers awaiting pickup, observed progress and uncertain actions. Owner enrollment exposes a copy-once credential and expiry; never logs it. Answer submission retains a stable retry intent until readback and preserves conflicting history.

- [x] Build the smallest human interface for enrollment, answering, context and observed progress, with canonical fork/source links.
- [x] Run tests/check/build, deploy with the saved project, then exercise request → browser answer → replacement recovery and permission negatives. Independent Evaluator reviews source and actual evidence.
- [x] Record successful review and milestone closure only after complete actual evidence. Otherwise retain M2 incomplete with the exact outstanding check.

Self-review: five failure classes map to Task 1/2 tests; live journey and unchanged login/harness regressions map to Task 3. Native record ID retry semantics were directly probed before implementation; no transactional or universal exactly-once claim follows from that probe. Native revocation is asynchronous: enrollment/revocation is pending until observed, and an upstream read failure denies authorization. No narrowed credential is represented as the full upstream bearer token.
