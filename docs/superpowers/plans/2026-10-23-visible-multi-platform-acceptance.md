# Visible Multi Platform Acceptance Plan

> **For agentic workers:** Use superpowers:executing-plans to execute the existing acceptance requirements. This plan adds no permission to message other chats, enroll workers, transfer credentials or configure a new service.

**Goal:** Show Ash multiple distinct agents on multiple actual platforms raising requests, receiving Ash's answers and visibly continuing their own work.

**Architecture:** Reuse the Fulcra dashboard and existing platform packages. Keep each agent's identity, environment, session and request scope separate. Collect actual host evidence and source readbacks for each route; retain unsupported or unconnected routes as incomplete.

**Tech Stack:** Existing Fulcra native transport, Codex/ChatGPT human inbox, Claude Code package and supported runtime delivery.

**Spec:** `docs/requirements.md` R5/R6/R17/R18 and the October 23 multi-platform acceptance clarification; `docs/superpowers/specs/2026-10-16-agent-work-pickup.md`.

## Global Constraints

- Never report two labels in one process, exported stdio discovery, CLI sign-in, saved answers or launch receipts as two live agents completing work.
- Scope the first demonstration to bounded, reversible artifacts; label demonstration inputs. Synthetic choices cannot authorize real account, publishing or service changes.
- Preserve the sole reviewed request revision, all answers, action intents and uncertain effects for each participant.
- Use actual host-supported routing. No blocked browser handoff or authenticated QA proxy workaround.
- Do not copy this maintainer's private worker or owner credentials to another host. Every participant requires its own authorized scope.
- Cross-machine acceptance and cross-platform acceptance are separate; multiple Codex machines do not prove Claude or ChatGPT web support.
- An existing private plugin and Gatekeeper account sign-in are separate from public marketplace access.

## Current Evidence

- Codex desktop on this machine: actual human inbox review/answer and this maintainer's continuation already observed. Current screenshot confirms work-card/evidence/next-action rendering.
- Claude Code: current CLI authentication is available. Historical bounded synthetic pickup exists, but it does not establish a current visible multi-agent demonstration.
- Second Codex machine: an existing user chat reports an installed skill with no human inbox tools. Connection inspection/recovery is required there; installing the skill alone was insufficient.
- ChatGPT web: no current authenticated worker pickup/remote OAuth/events acceptance is established. Do not substitute Codex app-server discovery for this row.
- Latest checked native requests for Gatekeeper sign-in and company publishing access had no answers at the start of this turn. Preserve them and recheck actual source; do not infer submitted answers from a chat statement.

## Task 1: Establish Actual Participants

- [x] Recover current native obligations and inspect existing host evidence.
- [x] Inspect the second-machine user chat and identify the missing explicit human inbox connection.
- [x] Check actual Claude Code authentication without starting a session or changing credentials.
- [x] Confirm authorization to coordinate the named existing second-machine chat and a bounded Claude Code demonstration worker; do not send a prompt to another chat without explicit authorization.
- [x] Verify each participant's actual platform, tools, separate worker grant, permitted source and session destination. Retain precise connection failures instead of presenting a healthy queue.

Observed: Ash explicitly authorized coordination. The actual Claude Code session loaded the exported plugin and called ToolSearch, recovery, three allowed source reads, its own request, work update and final source recovery. It uses a separate agent-only grant. Codex raised its own request. The remote Codex chat verified its own owner/project and local human connection through stdio, but its app tools still require a supported MCP-server restart. Its broader configuration-preservation comparison failed without a retained prior snapshot; that uncertainty is not resolved or certified away.

## Task 2: Visible Answer And Continuation

- [x] Have at least two actual platform workers create clearly labeled demonstration requests under their own identities, with useful artifact goals and future expected updates.
- [x] Show both in the same human decision inbox, with identity, platform/environment, question and next step.
- [ ] Let Ash answer through the actual UI. Each responsible worker must recover its exact current revision/all answer IDs, reconcile prior actions, perform the bounded next step and read back its artifact before reporting resumed/completed.
- [ ] Show source-backed transitions and resulting artifacts in the human view. One agent must not mark the other agent's work complete.
- [ ] Delay one answer until its worker is idle; prove the declared pickup mechanism resumes it without Ash sending a second check prompt. Record real deadlines and observed latency.

## Task 3: Isolation And Recovery

- [x] Verify neighboring agents cannot read each other's restricted work. Own-request positive controls succeed; foreign-request queries are rejected with the existing service's generic 400 and no protected contents. Cross-agent action mutation is still to be exercised separately.
- [ ] Retry delivery and recover a stopped/replaced session; preserve pending intentions and prove the artifact was not duplicated.
- [ ] Verify a missed expected update is visible as a concern, not an invented human decision or completed work.
- [ ] Repeat the complete chain on actual ChatGPT web when its supported authorized connection is available. Keep this row incomplete until its own evidence exists.
- [ ] Publish a concise acceptance matrix and actual artifact links. Keep fresh source/release checks, existing blockers and own V5 task evidence accurate.

## Review Focus

Wrong destination; human answer to a revised question; credentials copied across identities; a launcher returning successfully without worker continuation; a stopped worker still shown as listening. Each must be exercised or retained as an explicit coverage gap before declaring this acceptance complete.
