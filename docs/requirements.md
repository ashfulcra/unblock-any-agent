# Unblock Any Agent Requirements

Recorded 2026-10-16. This is the requirements record for the planned `ashfulcra/unblock-any-agent` repository. Product implementation has not started. Proposed behavior belongs in the [draft design](superpowers/specs/2026-10-16-unblock-any-agent-design.md); it is not an additional user decision.

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
