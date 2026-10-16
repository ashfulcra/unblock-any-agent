# Unblock Any Agent Draft Design

Status: proposed design, revised 2026-10-16 for the explicit clean-slate architecture requirement. This draft advances product planning; it is not an approved implementation specification. Confirmed user decisions are recorded separately in [Requirements](../../requirements.md).

The focused [first-release specification](2026-10-16-unblock-first-release.md) is now the next review artifact. This broader draft preserves the product direction and future scope.

## Product goal

Help an agent obtain what it needs and continue the work it already owns. Prioritize the user's experience of helping their agents. Use the same request model when the resolver is a human, another agent on the account, or an agent belonging to someone else.

Include continuity as a first-class capability: the user and their agents retain useful context, decisions, and outstanding work across interruptions, session changes, and authorized handoffs. Getting help and recovering the context needed to use it belong in the same product experience.

The complete interaction is: identify the obstacle, prepare a useful request, reach an authorized resolver, retain their answer, apply it to the originating work, and verify continuation. A reply is useful progress; the product also tracks whether the answer actually released the work.

## First user journey

An agent preparing a dashboard needs a hostname decision. It raises a request attached to its deployment task and checkpoint. The user sees:

> Choose the dashboard hostname.
>
> I recommend project.my.fulcra.ai. After your answer, I will check availability, deploy, and verify the live page.
>
> Actions: Use recommendation, Enter another, Ask an agent.

The user answers from any entry point. The originating agent reads the durable answer, checks that it still applies to the current blocker, and continues within its existing authorization. The request shows when the answer was applied and when deployment work resumed. If the agent cannot resume, the answer remains retained and the user sees the remaining recovery action.

## Proposed product concepts

| Concept | Responsibility |
| --- | --- |
| Work context | Identifies the originating objective, responsible agent, useful context, and next action. A reference to a native task or conversation may be sufficient; a new universal task system is not assumed. |
| Team membership | Relates independent human and agent identities to a team, with explicit scope and permissions. |
| Blocker condition | States the exact prerequisite and its current revision, so an answer to an earlier question cannot silently satisfy a changed one. |
| Unblock request | Presents the need, context, resolver, options, recommendation, urgency, and outcome required. |
| Resolution | Attributes an answer, artifact, action result, or delegation to its source and the condition it addresses. |
| Delivery attempt | Retains routing, native acceptance, receiver acknowledgment, uncertainty, and recovery separately from resolution. |
| Continuation evidence | Records application of the resolution and the next observed work action, or the new obstacle preventing it. |
| Continuity context | Preserves the useful goals, instructions, decisions, knowledge, progress, artifacts, pending commitments, and next actions needed to resume or hand over work. |

These concepts describe behavior to support, not required tables, event types, or independently persisted objects. Request kinds cover answers, decisions, approvals, access, artifacts, actions, and handoffs. The responsible agent remains accountable when someone helps; if another agent takes over, make the transfer and its acceptance clear using the best current mechanism.

## Multiple human resolvers

Start with one human in the first complete journey; keep the team independent of that person's identity. A team may eventually contain multiple independently authenticated humans helping the same agents. An agent's identity and work history must survive changes in human membership, runtime sessions, or default resolver. Exact runtime/session bindings are routing details when needed, not the product's identity model.

Distinguish who may resolve a request from who raised it and who is doing the work. Support a named human first and allow routing to an eligible group or team role later. Attribute every answer and approval to the actual human. Use the selected identity and team system to verify permission, and retain enough context to explain why a response was accepted. Choose the concrete schema after assessing current capabilities.

The proposed initial policy accepts one valid answer from an eligible resolver. Concurrent incompatible answers are surfaced for reconciliation rather than silently choosing the last write. Joint or quorum approval is a possible future policy, not a first-release requirement. Work requiring a specific account owner's permission remains addressed to that owner, even when another teammate can supply information.

Human viewers see only the request context and artifacts they are permitted to access. Forwarding or grouping a request cannot broaden its audience. Revoked membership prevents new actions, while the historical attribution of previously accepted answers remains intact. The first implementation must accommodate this growth without requiring a full team-administration UI immediately.

Evaluate current authentication, team membership, and sharing capabilities for future cross-account human teams. Historical workspace conventions do not define the product team model. Verify the selected access model with distinct users before advertising multi-human support.

The experience distinguishes a request still needing help, a result supplied, the agent using the result, and work actually continuing. These are observable outcomes, not a required event sequence or inherited state machine. Cancellation and delegation must be clear. Preserve useful history when an answer is stale, unsuitable, or followed by a different obstacle.

The UI must distinguish delivery problems, investigations, and work progress. It can therefore say “answer saved, agent unreachable” or “request open, delivery unverified” accurately. Completion of the parent task is tracked separately from the moment work resumes.

## Explicit requests and detected stalls

An explicit request is prepared by the agent with useful work context, the need, a recommendation where useful, and intended continuation. Asking for access names the required capability and the user action that can grant it; secret values do not belong in request bodies.

A detector operates on observable evidence: unanswered requests, tool failures, unmet dependency expectations, session interruptions, and missed updates the agent actually committed to provide. It retains the observation, source time, source coverage, and reason for concern. Time without activity alone does not prove a blocker.

Detected stalls first become investigation records linked to the work. Proposed routing:

1. When a specific required human action is known, prepare an actionable request for the user immediately.
2. When the cause is uncertain and a verified route exists, ask the owning agent to reconcile its state.
3. “Still working” updates the next expected observation; “blocked” creates or updates the request; “finished” supplies completion evidence; an unreachable agent produces a recovery issue.
4. Keep unresolved investigations visible. Notification urgency and grace periods are policy, separate from visibility. The agent-first notification policy is still a proposed default.

The first detector slice watches a missed promised update and an unanswered request. Later detectors add richer failure and dependency signals using the same intake. Each request retains its origin, so the user can distinguish an agent's explicit ask from a system inference.

Seeing or notifying about a request does not mean it has been handled. Previously unanswered requests remain visible across new sessions and reconnects. When a source cannot be checked, retain known work and explain the uncertainty. Choose event subscriptions, queries, scheduled checks, or another mechanism based on current verified support.

## Human attention and actions

The primary view is **Needs you**, with the exact action, agent recommendation, affected work, and waiting time. Supporting views are **Checking**, **Waiting elsewhere**, and **Recently resumed**. Every surface presents the same durable request identifiers and current condition revision.

Offer controls appropriate to the request: answer, choose an option, authorize the specific prepared action, provide an artifact, delegate, defer with a revisit condition, or cancel. A resolver's answer does not grant unrelated permissions. A short answer should be enough when the agent has already assembled context.

Group requests that share an equivalent prerequisite and compatible audiences. Present the affected work before applying a shared answer. Similar wording alone is not sufficient to merge requests, and a private answer must not cross an account or audience boundary merely because the UI grouped items.

Prioritize by declared urgency, deadlines, time waiting, and known work released by the action. Show the reason for ordering rather than inventing a precision score. Keep the larger agent map as an explanation and routing view linked from the relevant request.

## Resolution and continuation

Accept an answer against the current request revision. Concurrent or conflicting answers remain attributable and require reconciliation; a stale browser view cannot silently overwrite the current answer. Preserve the selected answer before trying to wake the worker.

The worker checks the answer's source, permissions, artifact access, and matching blocker condition. It records that it applied the result and executes its next authorized action. Work is shown as resumed only after observing that action. If the answer is insufficient or no longer relevant, the worker explains what remains and updates the linked request.

Retries, reconnects, and parallel sessions must not cause duplicated consequential actions or hide existing requests. Preserve enough information to recover safely after interruption. Use current transactional, idempotency, workflow, or host-native mechanisms where they satisfy these outcomes; a custom journal or replay engine is not prescribed.

Where a host cannot wake an agent, retain a pending continuation and provide a visible Continue action or recovery instructions. Readiness to deliver is established for the actual account, host, and session. A configured route or running process is not proof that the intended worker received the request.

## Reliable agent work pickup

The user identified a concrete failure: Tycho’s review was durable and addressed correctly, but the maintainer did not notice until the human prompted a check. Work pickup is a core requirement (R17). Plugins must be evaluated as receiver integrations that can cause authorized execution, alongside their skills and UI. Availability of a result, notification delivery, agent acknowledgment, and observed continuation remain distinct. Each agent needs a verified route and explicit busy/offline/replacement behavior. See the [work-pickup design](2026-10-16-agent-work-pickup.md); it supplements the first-release spec and takes precedence over interpreting a manual Continue path as sufficient automated pickup.

## Continuity and recovery

The user should be able to return to ongoing work without reconstructing its context. An agent resuming after context compaction, a new session, an outage, or replacement should know the objective, relevant user instructions and preferences, decisions already made, useful knowledge, artifacts, progress, pending obligations, blockers, and next useful actions. Preserve the source and recency of information so later agents can distinguish a current instruction from an outdated assumption.

Capture useful continuity context at meaningful work boundaries and before intentional handoffs. Retain enough recent progress to recover from an unplanned interruption as well. Assess current host-native persistence and compaction support before adding custom machinery. The exact representation, capture mechanism, and retention policy remain open architecture decisions.

On resume, recover the relevant context, then reconcile it with current reality: outstanding requests may have been answered, files may have changed, permissions may have expired, and an action may already have happened. Continue from the next justified step. Never repeat a consequential external action merely because its completion was absent from a compact summary. Where the result is uncertain, surface the concrete check or decision needed to proceed.

For handoff or replacement, make the pending responsibility, useful context, and expected next action clear to the receiving agent. Confirm that the recipient can access the needed material. Preserve the originating history and human decision attribution, including when the new agent uses another runtime or provider. Platform-specific limitations must be stated and tested; portable work context does not imply that every host can transfer a live session or all internal runtime state.

Let humans inspect and correct the saved work context, decisions, and next actions. Corrections need to reach later sessions. Share only the context the recipient is permitted to receive; private human material and credentials are not implicitly included in a team handoff. Relevant durable knowledge may be reused across work, with its provenance and freshness visible.

The first continuity slice is deliberately practical: after an agent raises a request and disappears, the user answers; a new authorized session recovers the work context and answer, reconciles current state, and takes the next useful action. Later slices broaden this to agent replacement, cross-runtime handoff, relevant persistent knowledge/preferences, and selective export/import where needed. These are proposed scope details under the confirmed continuity requirement, not a commitment to a legacy memory or checkpoint system.

## Architecture selection from current capabilities

No legacy Coord decision constrains this product. Protocols, schemas, append-only event history, deterministic replay, SQLite journals, CLI prerequisites, grant-file layouts, four-part actors, and polling schedules are all open implementation choices. Existing code may be reused only when it is the best fit after comparison with current alternatives.

The maintainer currently uses V5 for development awareness. That administrative setup does not select the product backend, identity model, storage, transport, workflow engine, or installation requirements. Backward compatibility and legacy migration are outside the initial product scope unless a concrete need is established.

Keep the four entry points consistent about the same request and its result. Whether that consistency comes from platform-native records, an application service, current host-native work APIs, or a combination is the architecture question to answer. Durable product identity must outlive individual sessions; runtime bindings are replaceable delivery routes.

### Candidates to compare

The [current platform assessment](../../current-platform-assessment.md) now recommends a platform-first approach with a thin application layer. This is a provisional architecture recommendation grounded in current documentation and a read-only capability check. Browser/plugin authorization and response concurrency still need implementation evidence; no end-to-end product capability is claimed yet.

| Candidate | Shape | Questions that decide whether it fits |
| --- | --- | --- |
| Platform-first | Use current Fulcra identity, structured data, sharing, files, and app hosting as far as they meet the requirements. Add application logic only for demonstrated gaps. | Can current APIs support the required concurrent responses, multi-user access, change discovery, and agent continuation with a simple deployable app? |
| Application service with Fulcra context | An application service manages active requests and coordination operations; Fulcra supplies the selected identity/context/sharing functions. Web, skills, and plugins use the same service. | Does this substantially simplify live updates, concurrency, and multi-human teams? Can someone fork and deploy a personal instance without excessive infrastructure? |
| Host-native coordination with a shared view | Use current platform task, messaging, notification, and continuation APIs directly, keeping only the cross-platform state the product actually needs. | Can native capabilities provide a coherent cross-platform workflow and durable recovery? Which gaps would still require a shared service? |

These are candidates to investigate, not claims of platform support or a decision to build three systems. Select components together where that produces a simpler product. Do not force a new bus, a complete task manager, or a universal scheduler if current platforms already supply the needed behavior.

### Capability assessment

Evaluate current documentation and then verify the material gaps in the actual target environments. Record the source date, environment/version, observed behavior, and implications for the product. Old incidents identify questions worth testing; they do not establish current limitations.

| Area | Evidence needed for a decision |
| --- | --- |
| Identity and access | Current authentication, durable agent identity, independently authenticated humans, team membership, authorization, and revocation. |
| Request state | Structured data support, query/update behavior, conflict handling, change discovery, retention, and access to artifacts. |
| Agent continuation | Current Claude and ChatGPT/plugin runtime APIs for receiving work, notifying or waking an agent, handling busy/offline sessions, and recovering across session replacement. |
| Continuity | Current native memory/compaction/persistence features, recoverable work context, human corrections, pending obligations, artifact access, and authorized context transfer across sessions or runtimes. |
| Human experience | Native interactive views, links into the right work context, answer submission, and synchronization across entry points. |
| Personal deployment | A clean fork deployed under the visitor's Fulcra account, required infrastructure, upgrades, and operating burden. |
| Operations | Measured latency, recurring model use, service costs, interruption recovery, and duplicated actions. |

The current Fulcra overview distinguishes owner-controlled durable context from an application's operational database and from a transactional queue/workflow runtime. Its typed data and sharing capabilities are useful building blocks; they do not by themselves choose the product state model. See [current Fulcra agent overview](https://github.com/kubla/fulcra-for-agents/blob/main/fulcra-for-agents.md) and [platform concepts](https://docs.fulcradynamics.com/fulcra-platform/). The initial review supports considering these options; it does not verify a finished architecture.

### Functional proof before architecture commitment

Exercise the same scenario against the best current candidates: an agent asks for help; a human answers through another entry point; the agent receives the answer and continues; an interruption occurs during the exchange; a new authorized session recovers the context, answer, and next action without requiring the human to reconstruct them. The request and outcome remain understandable afterward. Include a second human's identity/access case and a personal-deployment walkthrough when evaluating how the design grows.

Choose the approach that makes this flow simplest to build, operate, use, and fork while satisfying the required access and recovery behavior. Establish the minimal shared product interface from that evidence. Specify data schemas and detailed API signatures after the architecture choice, rather than adapting the product to existing Coord event names.

## Entry points and personal dashboards

All four entry points must be usable: web app, Claude plugin, ChatGPT plugin, and skill repository. Each supports joining the same authorized workspace and reaching the same requests. An entry point may expose manual continuation when its host has no verified background wake.

Official public marketplace/directory distribution is required for both plugins. Follow the [marketplace release and naming plan](../../marketplace-release-plan.md) from the first build, with `unblock` as the preferred short package/skill candidate and `/unblock` as a host-dependent invocation target. Use the descriptive display brand Unblock Any Agent. Availability and actual namespace allocation must be verified; no name has been reserved.

Generate platform-specific self-contained packages from shared source. Current OpenAI public-directory rules exclude lifecycle-hook packages and require the intended MCP capability at initial submission, so the Claude-specific mod and OpenAI package must not be treated as one identical artifact. Track Anthropic's directory submission and `claude-plugins-official` placement as distinct routes. These are current release constraints, separate from legacy Coord decisions.

The proposed canonical source is `ashfulcra/unblock-any-agent`, containing the skill distribution and related product sources. Link repository discovery, source, documentation, issues, and optional star invitations there.

The web app includes “Create your own dashboard” instructions: fork the original repository, use an agent setup prompt or manual guide, authenticate to the visitor's own Fulcra account, choose agents and workspace, create or reuse a deploy project, deploy, and verify the returned production domain. Personal configuration and credentials stay outside the public fork. Include update instructions and retain an attribution/source link to the original repository. These distribution requirements are recorded for delivery after the core contract is established.

## Delivery sequence

These are product milestones, not an approved executable implementation plan. The first release retains both explicit and detected intake and all four entry points. The sequence is open to revision as current capabilities make a faster complete journey possible.

| Milestone | Deliverable | Acceptance evidence |
| --- | --- | --- |
| 1 | Current-capability assessment and a selected architecture for the smallest complete human-unblocking and continuity journey. | Compare credible current approaches against the same flow, identity/access needs, context recovery, and personal deployment. Explain why the chosen components are needed. |
| 2 | One usable end-to-end journey with context recovery, with official-package identities and compatible export shapes established early. | An agent asks, a human answers, and a new authorized session recovers the context and continues without making the user repeat prior decisions. A stale answer or uncertain external action is reconciled safely. Validate package/name rules and the production MCP boundary alongside this slice. No CLI-first dependency is assumed. |
| 3 | Both explicit and detected intake with a useful human attention view. | A missed promised update or unanswered request is noticed; the user sees the known need or an honest investigation; repeated detection creates no duplicate work. |
| 4 | All four entry points sharing the same experience, with the first complete useful plugin release ready for official submission. | Start in web, Claude, ChatGPT, or the skills; answer elsewhere; observe consistent work progress. Verify each advertised background capability and invocation form in its real host. Validate official package exports and submit-ready listing material. |
| 5 | Broader routing through another agent or another person's agent. | A permitted helper returns a useful result and the responsible agent continues. Access boundaries and responsibility remain clear. |
| 6 | Forkable dashboard onboarding and expanded release packaging. | A clean fork is configured for another account, deployed at its returned Fulcra address, and upgraded without losing personal configuration. Canonical source/star links remain intact. This milestone does not gate the first useful official plugin submission. |

Broader continuity follows the initial recovery slice: agent replacement, authorized cross-runtime handoff, human correction of retained context, useful persistent knowledge/preferences, and selective context export/import. Sequence these around demonstrated user needs and current platform support, without making them prerequisites for the first human-unblocking journey.

Plan for multiple human resolvers from the outset; full team administration can follow the first release. Each milestone includes relevant documentation and evaluation of the actual experience. The referenced web-app skill provides a candidate build/evaluation workflow, not a reason to inherit any Coord architecture or postpone a usable human journey behind legacy infrastructure.

## Verification scenarios

Use meaningful end-to-end scenarios: answer from another surface; duplicate detection; changed blocker while a card is open; conflicting answers; reply arriving while the agent is offline; restart between answer and wake; source read failure; ambiguous delivery; revoked access; inaccessible artifact; and two agents waiting for one shared decision. Verify the state retained and the action performed, not just the appearance of a success message.

For personal dashboards, verify a clean-account setup and separation from the original owner's data. For background behavior, test idle, busy, restart, and unavailable routes independently. Set a declared observation window for each test; do not equate a bounded read with complete history.

For continuity, test context compaction, a session disappearing before the human answers, a new session arriving after the answer, agent replacement, changed artifacts, revoked access, stale retained instructions, human corrections, and interruption after an external action but before its result is recorded. Verify that the receiving agent can retrieve the necessary context, preserve outstanding commitments, and identify the next justified action. Include a scoped cross-runtime handoff before claiming portability across those hosts.

## Next planning work

Use the [current platform assessment and first-slice recommendation](../../current-platform-assessment.md) to define the minimal request, human-response, and continuity-context interfaces. Resolve browser/plugin authorization and verify the selected persistence behavior, then refine the first slice into a reviewable specification. The uncertain-stall notification preference remains open; the explicitly labeled agent-first proposal allows planning to continue without installing automation or notifying anyone.
