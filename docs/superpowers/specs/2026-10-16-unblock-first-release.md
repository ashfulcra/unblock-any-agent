# Unblock First Release Specification

Status: revision required after independent Fable review, 2026-10-16. This specification selects a proposed first release from the broader [design](2026-10-16-unblock-any-agent-design.md), [requirements](../../requirements.md), [platform assessment](../../current-platform-assessment.md), and [marketplace plan](../../marketplace-release-plan.md). It is not yet approved for implementation.

## Independent review follow-up

The [Tycho-delegated Fable review](../../reviews/2026-10-16-fable-spec-review.md) of commit `102e3ce` recommends **revise first**. Its findings are retained as review claims pending validation. Before implementation planning, resolve the monitor runtime and credential custody (F1), MCP authorization-server path (F2), agent identity binding (F3), and future multi-human response write path (F4). Validate the remaining platform and release findings against current sources. Reviewer naming and scope recommendations remain proposals; they do not override the user’s requirements.

The [review-resolution brief](../../review-resolution.md) now proposes concrete architecture decisions and the first build sequence. Those recommendations require review before replacing the provisional architecture below.

## Release outcome

A human can find what their agents need, answer once, and see work continue. Requests and useful context survive the original session. The web app, Claude plugin, ChatGPT plugin, and installable skills all provide useful entry points into this same flow.

The first release centers on one human account and its agents, with basic scoped help from an existing authorized agent connection. Human identities, teams, agent identities, and runtime sessions remain separate so additional humans can join later. Full multi-human administration, quorum approvals, an agent-universe map, arbitrary legacy imports, and a universal task scheduler are later scope.

There are no inherited Coord architecture constraints. The maintainer's V5 enrollment is development bookkeeping only.

## Architecture decision

Use a thin product application with web and remote MCP interfaces over Fulcra's current structured-data, context/file, identity, and selected-sharing capabilities. Keep portable skills as the workflow layer; platform adapters add native UI, lifecycle capture, and delivery where supported. Begin from the current Fulcra web-app template and deployment path.

The shared application implements the same operations for every surface. Authenticate callers and resolve their account/team permissions before reading or changing private work. Persist requests, human responses, useful continuity context, and progress outside runtime sessions. Use current platform schemas and direct queries; no custom bus, replay engine, local database, or four-part actor binding is required.

Before building the full interface, demonstrate two integration contracts: browser and MCP credentials resolve to the intended human/account, and the chosen persistence behavior retains concurrent responses without silently overwriting them. If additional transactional infrastructure is needed, document the specific failed contract and the minimal addition. Native wake and monitoring have separate capability checks. These checks are deliverables, not assumptions of existing support.

## Minimal shared information

| Concept | Information the product needs |
| --- | --- |
| Agent | Stable product identity, human-readable name, team/account relationship, and current optional runtime route. A replacement session does not become a different agent by default. |
| Work context | Goal, responsible agent, current progress, relevant user instructions/decisions, artifact references, pending commitments, expected updates, and next useful action. |
| Help request | Stable identifier, work-context reference, need, useful context, recommended answer/options, permitted resolver or audience, urgency, and what happens after resolution. |
| Response | Stable identifier, request identity and the request/context version shown to the responder, actual authenticated responder, answer or artifact/action result, and time. |
| Continuation result | Which response was used, what the agent did next, useful evidence, and any remaining obstacle. |

These are product information contracts, not a prescribed table or event layout. Choose concrete types and indexes from current platform capabilities. Keep versioned artifact references where the exact content matters. Never rely on a sender label supplied by the model as authentication.

## Common operations

| Operation | Required behavior |
| --- | --- |
| `request_help` | Save the useful work context and a specific request. Return its stable identity and a link usable by the intended resolver. A retry must not create a second logical request. |
| `get_attention` | Return the caller's permitted requests and investigations, including known pending work after a reconnect. Distinguish unavailable sources from checked-and-quiet sources. |
| `answer_request` | Attribute the answer to the authenticated resolver and preserve the question/context they answered. Keep conflicting answers visible. Saving an answer does not itself mean work resumed. |
| `save_context` | Preserve useful progress, decisions, artifacts, commitments, and next actions for another session. Human corrections remain visible to later sessions. |
| `resume_work` | Retrieve relevant context and responses for an authorized agent. Reconcile them with current artifacts, permissions, and action results before recommending the next step. |
| `report_progress` | Record the observed next action, completion, or remaining obstacle. Update the human view using what actually happened. |

The application does not execute arbitrary commands through these operations. Consequential actions use the agent's separately authorized host tools. Repeated delivery or repeated resume must not repeat an external action without checking its result.

For a changed or obsolete request, retain the historical answer and show that the current need remains unresolved. Do not silently choose the latest incompatible answer. For the first single-human flow, the responsible agent reconciles the answer with the work context and records what it used. The later multi-human model can extend resolver policy without changing response attribution.

## Human and agent experience

The human starts with **Needs you**. Each card explains the agent's goal, exact need, recommendation, affected work, and intended next action. Appropriate controls answer, select an option, provide an artifact, delegate within existing permissions, defer with a revisit condition, or cancel. Supporting views distinguish investigation, waiting elsewhere, and resumed work.

The primary `unblock` skill is role-aware: it helps a human review requests, and helps an agent recover context, obtain missing help, or continue after a response. A typical interaction should not require anyone to copy internal identifiers.

The preferred Claude Code entry is a native `/unblock` command, with a namespaced skill entry available as a fallback. Registration must not overwrite a taken command or make setup fail if the short alias is unavailable. ChatGPT uses supported plugin/skill selection and app entry points; a global bare slash command is not promised there. Keep the proposed public plugin identifier `unblock` separate from the descriptive display brand Unblock Any Agent and the canonical source repository `ashfulcra/unblock-any-agent`.

## Continuity and detection

Capture context at meaningful work boundaries, before intentional handoff, and through verified host lifecycle mechanisms where available. New sessions recover goals, decisions, pending obligations, artifacts, and next actions. A different runtime can receive a scoped context package when its access and import path are supported. This transfers useful work context; it does not promise transfer of every provider's internal session state.

Support both agent-raised requests and detected stalls. The first detector checks declared expected updates and unanswered requests. It records the observation behind a concern. A clear human action goes to Needs you; an uncertain stall becomes an investigation addressed to the responsible agent when reachable. Keep it visible if the agent is unavailable. Agent-first notification for uncertain stalls is the proposed default, not a previously confirmed user preference.

Unattended monitoring requires a configured route that actually runs independently of the originating session. Setup must report watched sources, observed cadence, and delivery support, and verify one real due item. If no such route is enabled, show monitoring as inactive and offer an explicit check; do not advertise background detection. The implementation plan must include at least one supported independent monitoring route for the public release and keep model invocation out of quiet checks where possible.

Continuity and requests remain useful without automatic wake. The first recovery test may open the replacement session manually. Automatic pickup, busy-session handling, and unattended monitoring each require their own observed acceptance result. The public release must demonstrate automatic pickup on the native routes it advertises; manual Continue is a recovery mode, not a passing automatic-pickup test.

## Agent work pickup

R17 makes work pickup a release-critical function. Returned reviews, human answers, assigned work, and released dependencies must cause the responsible authorized agent to reconcile and continue. A saved result or sent notification does not establish that the agent noticed it. Treat pickup and independent stall detection as separate contracts: the former reacts to available work; the latter discovers a missing expected result.

Each connected agent needs listener setup instructions and a selected receiver, verified before automatic pickup is claimed: its host and supported surfaces, authenticated agent/work mapping, permitted triggering mechanism, active/subscribed status, handling while busy, behavior with no live session, and a recovery action. Prefer a separate listener session or scheduled task on each machine/environment that checks and routes messages to its registered local sessions; native plugin integrations can provide or improve this route. Use ticks, heartbeats or loops appropriate to other runtimes. Evaluate MCP Events for supported ChatGPT Work surfaces and Claude Code mod prompt submission for live Code sessions. Both are documented candidates, not demonstrated integrations. Local Codex, Claude chat/Cowork, and bare skills require their own capability result; do not inherit another surface’s wake claim.

Show whether a result is available, delivery was attempted/accepted, the responsible agent acknowledged the current work, and useful continuation occurred. These are observable distinctions, not a required storage schema. Bound delivery retries and the time to acknowledgment; keep missing acknowledgment visible and escalate through a configured authorized route. Reconnect/start must reconcile unresolved work, including items whose notification was already delivered. Preserve identity, context, and unresolved work when selecting a replacement session. Do not interrupt unrelated work, grant extra permissions, or repeat external actions through automatic delivery.

The [work-pickup design](2026-10-16-agent-work-pickup.md) records the incident, current evidence, proposed approach and test matrix. Prove Claude pickup through a native or listener/scheduled route, alongside the selected ChatGPT route, before investing in the full dashboard. Provide [listener instructions](../../listener-setup.md) for every connected agent; plugins or equivalents for additional platforms follow later. No new watcher or schedule is installed by this specification change.

## Distribution and personal dashboards

Build self-contained Claude and OpenAI exports from one shared source. The OpenAI public package includes the intended remote MCP capability from its first submission and excludes lifecycle hooks. Keep Claude-specific mod capabilities in the Claude export. Validate each package in the actual supported hosts, including the workflow available where native mod UI does not render.

Official public distribution is an early release objective. Audit publisher access, name validation, production endpoint/domain verification, supported package fields, public listing material, and reviewer access while building the useful flow. Track Anthropic directory acceptance and `claude-plugins-official` placement separately. Neither a GitHub repository nor a local command registration reserves a marketplace name.

The web app prominently offers Create your own dashboard. Its instructions let a visitor fork the canonical repository, use an agent setup prompt or manual guide, connect their own Fulcra account, choose agents/workspace, deploy at the returned Fulcra address, verify the result, and apply later updates without overwriting private configuration. Source and optional star links point to the canonical repository. No private account configuration is shipped in the fork or plugin archives.

## Acceptance cases

1. **Complete human loop:** an agent raises a request with context, the human answers in the web app, and the agent uses the answer and reports the observed next action.
2. **Session replacement:** end the original session before the human answers. A new authorized session retrieves the decision and context and continues without asking the human to repeat them.
3. **Real detector:** a declared update becomes overdue while the original session is unavailable. The enabled independent monitor notices it, preserves the observation, and surfaces the investigation or specific need. Repeated checks create no duplicate request.
4. **Cross-surface use:** start through each of web, Claude, ChatGPT, and skills; answer or resume through another entry point; observe the same request and response history.
5. **Stale or conflicting information:** change relevant work context or submit incompatible responses. Preserve attribution, explain what needs reconciliation, and avoid falsely claiming resolution.
6. **Action uncertainty:** interrupt after an external action but before its result is saved. Resume by checking the actual result before repeating it.
7. **Identity and access:** reject an unrelated account; later admit another human through an explicit supported team policy in an integration test. Verify revocation and scoped artifact access before advertising multi-human support.
8. **Continuity correction:** correct a retained decision or next action and confirm a later session uses the correction while retaining useful history.
9. **Basic agent help:** use an existing authorized connection to obtain a result from another agent; preserve responsibility and share only the allowed context.
10. **Personal deployment and package install:** deploy a clean fork for another account; install both platform exports; test the actual invocation forms, reconnect, and updates. Verify that canonical repository links remain intact and no private configuration is included.

11. **Returned review without a human nudge:** after the requesting agent becomes idle, another agent returns a review. The enabled receiver starts or resumes the correct authorized worker, which retrieves the report and records its next useful action. No human message requests a check. Repeat while busy, after reconnect/session replacement, with duplicate delivery, and with the receiver disabled. The disabled route must show a pickup gap and recovery action; it must not count as a successful automatic test.

12. **Listener coverage and local routing:** demonstrate the Claude path and selected ChatGPT path. On each pilot machine/environment, follow the listener guide to enable a dedicated listener or scheduled task, or a documented runtime tick/heartbeat/loop. Route a delayed result to the correct local session without giving it to a neighboring agent. Stop and replace a session, restart the listener, and verify unresolved work is recovered. Confirm that a configured-but-not-running trigger and a check-only route are shown accurately. Other runtimes may use the portable listener baseline while native plugins remain later scope.

Use real tools and record the tested version, host, action, and observed result. A unit test, successful package upload, model statement, or configured route alone is not end-to-end acceptance. Official review and marketplace publication remain separate release outcomes.

## Implementation sequence after review

First prove authentication, persistence, and Claude/ChatGPT work-pickup contracts with a minimal real request/response/context flow. Then build the human dashboard and replacement-session recovery. Add the detector and verified independent monitoring route, complete both plugin exports and four-entry-point onboarding, and verify clean-account deployment. Prepare and submit the smallest complete useful release as soon as its acceptance evidence and listing requirements are satisfied.

Use the reviewed specification to write the executable implementation plan. Keep new features outside this first-release boundary unless they are necessary to satisfy an acceptance case or the user changes the requirements.
