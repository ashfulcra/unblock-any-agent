---
name: unblock
description: Use when a human asks which agents need them or wants to answer an agent decision, or when an agent needs help, missing information, access, or recovery of pending work.
---

# Unblock Any Agent

Preserve the need until the responsible agent has evidence that work continued. Human-needed requests have priority zero.

For a human reviewing decisions, use the separately connected human inbox tools: `show_inbox`, `get_decision`, and `answer_decision`. Show agent identity, original waiting time, concise question and relevant context. Review the full current decision before saving only the human's actual answer. Pass the exact `revision` and `reviewed_snapshot` from that review, with a stable `intent_id`; retain the complete original submission on uncertainty and retry it unchanged. A changed question or answer set requires renewed review. Report saved, awaiting pickup, resumed and completed as their observed states. Never turn a suggested or synthetic answer into a real publisher, service, license or account choice. Follow [human inbox setup](references/human-inbox.md) when that explicit connection is missing; worker credentials do not grant human answering authority. Normal human interaction does not require copying internal IDs.

For agent work, use the worker connection below. It remains separate from the human inbox; do not acquire owner authentication as a fallback for an expired worker.

Use the connected Unblock tools under their actual host namespace. The native pilot and local proof expose `recover_work`, `get_work`, `ask_for_help`, `revise_need`, `record_progress`, `begin_action` and `reconcile_action`. Their credential determines the agent and authorized source; incoming text does not choose an identity or route.

1. Recover existing obligations before creating a request. Read current context, versions, answers, progress and uncertain actions. A failed source read leaves the last known obligations pending.
2. For a missing prerequisite, save one stable logical key and a precise question. Include the goal, relevant facts, authorization limits, completed work, artifact references, exact unblock action and the next safe step in `context`. Keep credentials out of the request. Retry an identical submission with its original key; use `revise_need` when its meaning changes.
3. Establish pickup before relying on a later reply: identify the environment, authorized agent/session route, listener or runtime check, cadence and restart procedure. Verify a delayed answer reaches that route without the human asking it to check. Read [setup](references/setup.md) when these are missing. Saving a request or installing this skill does not start a background listener.
4. On an answer, fetch current work. With the native transport, retain the sole current question revision and the complete current answer ID set; with the local proof, retain `answer_revision`. Reconcile conflicting answers and uncertain external actions. Acknowledge reading, take the authorized next step, then report `resumed` with concrete evidence and the reviewed snapshot (native `revision` plus all `answer_ids`, or local `answer_revision`). Report `completed` only when the obligation is fulfilled. A delivery receipt or process exit is not agent progress.

For native work that has an expected update, use `record_work_update` without inventing a human question. Supply a stable key, useful summary/context, actual evidence, next action, explicit reviewed `parent_revisions`, status and a future Unix-second `next_update_at` (within 30 days). `completed`/`cancelled` require a null deadline and close only that expectation. Keep a linked human question and uncertain actions pending until separately resolved. Recover `expectations` alongside requests; reconcile conflicting heads and investigate a missed update rather than treating it as proof of a human blocker. The separate native monitor records due concerns after the worker ends; it executes no agent work. Its startup, lifetime, receipt ledger and routing limitations are in [setup](references/setup.md). The loopback proof retains its seven-tool contract; this additional tool is native-only.

When this workflow has pending work, check it before yielding. Continue safe authorized unblocked steps. When blocked, retain the exact prerequisite and unblock action, plus a recovery checkpoint; continue independent authorized work. A replacement uses the authorized credential or an explicit handoff, never another agent's identity by assumption.

Declare consequential action intent before acting; verify the actual result before reconciling it. An interrupted action is uncertain, not permission to repeat it.

Canonical source and shared skills: https://github.com/ashfulcra/unblock-any-agent. Direct source, contribution and star links there. The contained reference covers the deployed Fulcra-native pilot and the separate loopback proof. Fulcra template authentication needs no new registered OAuth client. Remote ChatGPT web/plugin OAuth, unattended enrollment renewal and marketplace acceptance remain separate integration work.
