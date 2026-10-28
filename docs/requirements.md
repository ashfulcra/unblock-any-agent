# Unblock Any Agent Requirements

Recorded 2026-10-16. This is the requirements record for the canonical `ashfulcra/unblock-any-agent` repository. A local implementation now exists; [execution evidence](execution-ledger.md) distinguishes verified behavior from planned production functionality. Proposed behavior belongs in the [draft design](superpowers/specs/2026-10-16-unblock-any-agent-design.md); it is not an additional user decision.

## Purpose and references

Build a combination of skills, Claude and ChatGPT plugins, and a web UI that helps agents get unstuck and continue their work. Use Coord and AICQ to understand useful functions and failure modes. Evaluate the Fulcra connection, workspace, and web-app skills and today's underlying platforms against the product requirements. Existing implementations do not prescribe the new architecture.

The project name is `unblock-any-agent`, under `ashfulcra`.

The assigned maintainer identity is **Unblock Any Agent Maintainer**, with the routing identifier `unblock-any-agent-maintainer`. Its runtime bindings and interim V5 configuration remain private.

## Confirmed requirements

| ID | Requirement | Source |
| --- | --- | --- |
| R1 | Agents needing the user are priority zero. | “Agents needing me is priority zero” |
| R2 | Human help, help from another of the user's agents, and help from another person's agent belong to the same underlying unblocking system. | “all of those priorities are kind of the same thing” |
| R3 | Include requests raised explicitly by agents and detection of apparently stalled work in the first version. | “Both,” answering the choice between explicit requests and detection |
| R4 | The web app is an entry point. | Additional entry-point requirement |
| R5 | The Claude plugin is an entry point. | “plug-ins for both platforms” |
| R6 | The ChatGPT plugin is an entry point. | “plug-ins for both platforms” |
| R7 | The skill repository is an entry point. | Additional entry-point requirement |
| R8 | Accumulate GitHub stars on the skill repository. | “we want to accumulate stars on the skill repo” |
| R9 | The web app includes instructions to fork the repository and create a personal Fulcra-hosted dashboard. | Personal-dashboard requirement |
| R10 | Record the distribution and dashboard requirements now, and continue planning the core product. | Latest direction |
| R11 | Plan for multiple distinct human identities to unblock one agent team eventually. | Multiple-human requirement |
| R12 | The working product is intended to supersede the existing coordination tooling; current V5 participation is useful for awareness and is not a priority dependency for this project. | Direction accompanying the V5 registration question |
| R13 | Legacy Coord design decisions, implementation history, protocols, and workarounds impose no architectural constraints. Preserve desired functionality and choose how to deliver it using current capabilities. | Explicit clean-slate architecture instruction |
| R14 | Include continuity functionality in the product plan. | “Folding in continuity functionality should go on the plan as well” |
| R15 | Build the Claude and ChatGPT plugins for distribution through their official public plugin marketplaces/directories, including applicable package, naming, review, and publishing requirements. | Official-marketplace requirement |
| R16 | Move quickly toward a short public plugin/command identity such as `unblock` and `/unblock`, accounting for namespace competition and each host's actual invocation rules. | Short-name and launch-urgency direction |
| R17 | Make agent work pickup a core capability: returned answers, reviews, assignments, and released dependencies must reach the responsible agent and cause safe continuation without the human repeatedly prompting it to check. Evaluate plugins as runtime integrations, and verify each host’s actual delivery and wake behavior. | User identified the missed Tycho review as a product failure case |
| R18 | Include a Claude pickup route in the minimum scope; at bare minimum provide listener instructions for every connected agent. Prefer a separate listener session or scheduled task on each machine/environment that checks and routes work to its local sessions; support runtime-appropriate ticks, heartbeats and loops. Plugins or equivalents for additional platforms are later functionality. | Explicit listener baseline and platform sequencing |
| R19 | At each turn exit, inspect owned work and addressed replies; take the next safe authorized step without another prompt and continue. | “Give yourself an exit check on each turn. If there is a next step you can take without me do it. After that keep working.” |

## User decision record

The following statements preserve the user's wording in conversation order.

1. “We’re going to start a new repo under ashfulcra - unblock-any-agent - combination of skills plus Claude and chatgpt plugins and webui that combine some of the functions of coordv5 and my Aicq Claude code mod, based on the connect agents, workspaces and webapp skills in https://github.com/fulcradynamics/agent-skills - look at all the things I referenced and brainstorm - the goal is in the name of the repo”
2. “Agents needing me is priority zero, but all of those priorities are kind of the same thing”
3. “Both” — in response to whether requests should be explicit or also detected from stalled work.
4. “Additional requirement: the web app version should be an entry point, as should the plug-ins for both platforms and the skill repo. But we want to accumulate stars on the skill repo”
5. “Specifically with regard to the web app: it should have instructions to fork and for anybody to create their own my.folkra.AI web app dashboard”
6. “OK, just record those requirements for now and keep working on the plan that you were working on a few minutes ago”
7. “I guess we should plan for eventually having multiple human identities unblocking one agent team. What’s blocking V5 registration? I don’t really care if you’re on V5 because this is going to supersede all of it when we get it working, but I guess it’s good for awareness for now”
8. “Your identity is unblock any agent maintainer. Create a new one”
9. “I explicitly do not want to be bound by any legacy decisions in how coord was built and iterated. Everything it’s built on top of has evolved greatly since we built it. We care about functionality, not about carrying forward how it’s done.”
10. “Folding in continuity  functionality should go on the plan as well”
11. “For for the Claude and ChatGPT plugins, the goal is to use their recently enabled functionality for plugins to become plugins in their official marketplace. So consider package requirements, naming conventions ETC.  There’s a namespace competition there, so we’re going fast towards the slash command /unblock or something similar”

12. “Note that you did not notice Tycho’s review. Figuring out how each agent will pick up work is a big part of this. I’m assuming the plug-ins can help here.”

13. “We need at minimum a Claude route also, or at bare minimum listener instructions for each connected agent, preferable a separate session or scheduled task on each machine / Env checking and routing messages to sessions that live there, or instructions to check with regular ticks, heartbeats, loops whatever for other agent runtimes as appropriate. Later functionality will be figuring out plugins or equivalent for other platforms.”

## Official distribution and naming

Official public distribution is a design input from the first package, rather than a final release afterthought. Keep the canonical skill/source repository `ashfulcra/unblock-any-agent`. The proposed package identifier and primary skill name are `unblock`, with a descriptive public display name such as **Unblock Any Agent**. `/unblock` is the preferred short invocation target; exact syntax and alias support depend on the host and require verification. No namespace reservation is claimed.

The [marketplace release plan](marketplace-release-plan.md) records current package rules, platform-specific export requirements, the distinction between Anthropic's directory and its official Code marketplace, and the fastest credible path to a complete first public release. Package names, display names, skill names, command aliases, and publisher identity must be treated as separate choices.

## Continuity scope for planning

Continuity is a confirmed product capability. The proposed scope is to preserve and recover the useful state needed to continue work across context compaction, session changes, interruptions, agent replacement, and authorized handoff to another runtime or provider. Include goals, user instructions and decisions, relevant knowledge, artifacts, progress, unanswered requests, outstanding commitments, and the next useful actions.

The human-first outcome is that the user can unblock an agent and the work can continue later without requiring the user to reconstruct prior context or repeat decisions. A replacement agent should understand what remains and what has already been attempted. Proposed details and delivery stages are in the draft design; no old continuity package, storage layout, memory format, or backup mechanism is required.

## Architecture selection rule

Start from the required user and agent experiences, examine current platform capabilities, and choose the simplest implementation that meets them. The existing bus, event schemas, deterministic replay/fold, local journals, CLI requirements, session-bound actors, polling mechanisms, and deployment topology are not requirements for this product. Reuse is optional and must earn its place against current alternatives.

Keep reliability outcomes such as preserving unanswered requests, attributing human decisions, respecting access boundaries, and recovering interrupted work. Design their implementation afresh. The concepts in the draft are proposed product concepts, not a commitment to old schemas or state machines.

Backward compatibility, legacy migration, and existing package integration are not assumed deliverables. Add them only for a demonstrated user need. Current maintainer V5 registration is development bookkeeping, separate from the product architecture.

## Interpretation and proposed distribution

Treat `ashfulcra/unblock-any-agent` as the canonical skill repository and the destination for source links and stars. This interpretation follows the named new repository; the user did not request a separate skill repository.

Interpret the dashboard hosting reference as Fulcra's `my.fulcra.ai` hosting described by the referenced web-app skill. Save and use the actual domain returned by the deployment service.

Proposed distribution: keep skills, plugin sources, web source, documentation, and release history together. Offer independent onboarding from all four entry points into the same requests and workspaces. The web app's “Create your own dashboard” instructions cover forking, an agent setup prompt, manual setup, personal authentication, workspace configuration, deployment, verification, and later updates. Repository and optional star links point to the original repository. These mechanics remain design proposals.

## Human identity and team growth

Support one person helping their agents first, while reserving a model in which a team has several independently authenticated humans. Keep the team, agent identity, human identity, and permissions distinct. Future human participants may hold separate Fulcra accounts; a shared display name or access to a conversation does not establish team authority.

Proposed routing supports a named human or a defined set of eligible resolvers, with response attribution and a versioned resolution policy. The default policy, team administration, and any joint-approval behavior are design decisions rather than confirmed requirements.

The maintainer's V5 participation provides temporary development awareness. It creates no product dependency, integration obligation, or compatibility requirement. If a future user needs existing work imported, scope that import explicitly and preserve the work that user chooses to bring across.

## Agent work pickup

A durable answer is useful only if the responsible agent picks it up. Treat the missed Tycho review as an acceptance scenario: a review arrived while the maintainer was idle, and Ash had to request a check. The design must cover idle, busy, disconnected, closed, and replacement sessions, and distinguish publication, delivery, agent acknowledgment, and observed continuation. Plugins are candidates for native integration, not evidence that automatic pickup is enabled. See the [work-pickup design](superpowers/specs/2026-10-16-agent-work-pickup.md).

## Minimum listener coverage

Claude pickup is part of the first-release baseline alongside ChatGPT. Every connected agent gets [listener setup instructions](listener-setup.md) appropriate to its actual runtime. Prefer one separate local listener session or scheduled task per machine/environment to check permitted work and route it to registered local sessions. Where that is unsuitable, use an existing heartbeat/tick facility or a supported in-session loop, with its lifetime and restart behavior documented. A passive instruction to check someday is not active coverage.

The baseline does not wait for native plugins on every runtime. Preserve the existing Claude and ChatGPT official-plugin goals; develop additional platform plugins or equivalents later.

## Open product choice

The escalation policy for uncertain detected stalls is unanswered. The proposed default is to contact the agent first when the cause is uncertain, and notify the user directly when a specific human action is already known. An unreachable agent must remain visible as a recovery issue.

## Functional references

The dated references below record what was inspected for useful functionality and lessons. Architecture selection must use current documentation and verified platform behavior; these source snapshots are not dependency pins.

- [Fulcra connection skill](https://github.com/fulcradynamics/agent-skills/tree/c419b169128effbbb8d74fb775a5f960655cf959/skills/connect-our-agents): cross-account connections and messages.
- [Fulcra workspace skill](https://github.com/fulcradynamics/agent-skills/tree/c419b169128effbbb8d74fb775a5f960655cf959/skills/fulcra-workspaces): durable purpose, tasks, roles, and continuity.
- [Fulcra web-app skill](https://github.com/fulcradynamics/agent-skills/tree/c419b169128effbbb8d74fb775a5f960655cf959/skills/build-and-deploy-a-web-app): authentication, deployment, and evaluated milestones.
- [CoordV5](https://github.com/ashfulcra/fulcra-tools/tree/31f75bc1f4642ab9c3ef562fdf73ba5a74ca1bca/packages/coord-v5): authorized work projection, questions, checkpoints, handoffs, and delivery journals.
- [AICQ Claude mod](https://github.com/ashfulcra/fulcra-tools/tree/31f75bc1f4642ab9c3ef562fdf73ba5a74ca1bca/packages/aicq-claude-mod): collaboration UI, response modes, and universe map.
- [AICQ session inbox fix](https://github.com/ashfulcra/fulcra-tools/commit/97d9c8be): separate per-session display state from the shared arrival ledger.
- [Fulcra deployment flow](https://github.com/fulcradynamics/agent-skills/blob/c419b169128effbbb8d74fb775a5f960655cf959/skills/build-and-deploy-a-web-app/references/deploy.md): create or reuse a deployment project and verify its returned production domain.


## 2026-10-16 authentication correction

User: “you dont need a registered oauth client if you use the fulcra webapp skill”. Use the existing Fulcra template authentication and native deploy path. A new OAuth registration or separate custom backend/database is not a prerequisite for the hosted web baseline. Preserve the distinction between web sign-in and any later remote MCP resource authorization.


## R19 — Usable decision workspace and in-chat entry (2026-10-19)

Ash identified the previous web experience as a wall of text and forms, and confirmed that ChatGPT/Codex UX is central to the project. Agent identity and elapsed waiting time must be prominent. Every decision shows a concise question and relevant context; opening it reveals the full context and recommendation. Provide organized visual exploration, agent filtering/search, original waiting dates, and one focused decision panel. Completed decisions remain reviewable; source failures are unknown, never an empty queue. Private UX work proceeds independently of public publisher/license and separate-account fork prerequisites.

The dashboard correction is deployed with board, list and agent ownership map. The separate human inbox inside the host remains an active deliverable; worker credentials must not gain human answering authority. Actual ChatGPT web authorization and actual installed-host behavior require their own evidence.

## Visible multi-agent, multi-platform acceptance (2026-10-23)

Ash: “when you work through the stuff i just responded - i need to see this work with multiple agents on multiple platforms”.

Acceptance must visibly show distinct actual agents on different platforms in the same decision workspace. Each agent raises its own scoped request, receives the human's actual answer, performs its next authorized step and reports source-backed resumed/completed work with an artifact. Include delayed pickup after a worker becomes idle, neighboring-agent isolation, repeated delivery and interruption recovery. Record actual platform and machine coverage separately. Codex does not establish ChatGPT web or Claude support, and an installed skill, tool discovery or saved answer does not establish worker continuation. Keep the complete ChatGPT route incomplete until its own host evidence exists. The execution checklist is in [the visible acceptance plan](superpowers/plans/2026-10-23-visible-multi-platform-acceptance.md).

## One-click recommendation (2026-10-28)

Ash: “i should be able to just hit a button to send the reccomendatin”.
Place Send recommendation beside the agent’s recommendation in the inline inbox and hosted dashboard. One click submits its full text using the existing reviewed-question and answer-intent safeguards. Preserve manual answers, changed-question review and exact retries of uncertain saves.
