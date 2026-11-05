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

## Evidence updated November 5, 2026

The [current acceptance matrix](../../reviews/2026-11-05-platform-acceptance.md)
separates actual model, API and browser evidence with their limits. Raw reports,
source receipts and browser captures remain in private accepted work evidence.
Source publication alone does not complete the parent acceptance task.

- Original Codex desktop and Claude Code workers recovered real human answers and completed separate reports. Completed cards and full report evidence were later verified in the maintainer and second-machine in-app browsers.
- A separate October 28 bounded live Claude CLI trial proved scheduled idle-answer pickup without a second check prompt. It does not prove wake after that process exits.
- A separately human-authorized November 5 Codex CLI trial proved fresh-model report recovery and exact-action retry with an unchanged artifact. Arbitrary original desktop model replacement and Codex automatic wake remain unproven.
- Gatekeeper sign-in, its separate deployed dashboard and manual missed-update concern rendering/resolution are verified. Persistent automatic monitoring/investigation is not established by the manual check.
- Actual ChatGPT web worker connection/OAuth/Events and company publishing access remain separate incomplete prerequisites. Do not reopen completed login needs or rerun completed trials.

## Task 1: Establish Actual Participants

- [x] Recover current native obligations and inspect existing host evidence.
- [x] Inspect the second-machine user chat and identify the missing explicit human inbox connection.
- [x] Check actual Claude Code authentication without starting a session or changing credentials.
- [x] Confirm authorization to coordinate the named existing second-machine chat and a bounded Claude Code demonstration worker; do not send a prompt to another chat without explicit authorization.
- [x] Verify each participant's actual platform, tools, separate worker grant, permitted source and session destination. Retain precise connection failures instead of presenting a healthy queue.

Observed: Ash explicitly authorized coordination. The actual Claude Code session loaded the exported plugin and called ToolSearch, recovery, three allowed source reads, its own request, work update and final source recovery using a separate agent-only grant. Codex raised its own request. The second-machine tester later verified the actual human inbox and authenticated browser view; the proposed Settings > MCP servers > Restart instruction was absent and withdrawn. Its broader configuration-preservation comparison remains unresolved without the prior snapshot. Completed participant grants and trials do not authorize new workers, renewals or waiting windows.

## Task 2: Visible Answer And Continuation

- [x] Have at least two actual platform workers create clearly labeled demonstration requests under their own identities, with useful artifact goals and future expected updates.
- [x] Show both in the same human decision inbox, with identity, platform/environment, question and next step.
- [x] Let Ash answer through the actual UI. Each responsible worker must recover its exact current revision/all answer IDs, reconcile prior actions, perform the bounded next step and read back its artifact before reporting resumed/completed.
- [x] Show source-backed transitions and resulting artifacts in the human view. One agent must not mark the other agent's work complete. Verified in both actual in-app browsers October 26 UTC.
- [x] Delay one answer until its worker is idle; prove the declared pickup mechanism resumes it without Ash sending a second check prompt. Verified only for the separately authorized October 28 live Claude CLI trial, about 56 seconds after the real answer. The original October 23 route did not establish this.

## Task 3: Isolation And Recovery

- [x] Verify neighboring agents cannot read each other's restricted work. Own-request positive controls succeed; restricted foreign-read and action API probes reject access without protected contents. These adapter/API controls do not imply model-tool negative cases were performed.
- [x] Retry delivery and recover a stopped/replaced session; preserve pending intentions and prove the artifact was not duplicated. November 5 actual Codex CLI fresh-model recovery/retry verified one action and unchanged report hash/mtime. Arbitrary original desktop replacement remains unproven.
- [x] Verify a missed expected update is visible as a concern, not an invented human decision or completed work. November 5 manual observation, actual browser rendering and actual model resolution verified; no persistent monitor or automatic dispatch claim.
- [ ] Repeat the complete chain on actual ChatGPT web when its supported authorized connection is available. Keep this row incomplete until its own evidence exists.
- [x] Retain actual artifact links and exact source evidence in the private owned work record; do not publish credentials, journals or private checkpoint evidence.
- [x] Publish a concise sanitized acceptance matrix in source. Its publication/readback must also be accepted in the owned fold; the parent remains incomplete for the separate ChatGPT web step.

## Review Focus

Wrong destination; human answer to a revised question; credentials copied across identities; a launcher returning successfully without worker continuation; a stopped worker still shown as listening. Each must be exercised or retained as an explicit coverage gap before declaring this acceptance complete.
