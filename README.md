# Unblock Any Agent

Help agents obtain what they need and continue their work. Agents needing a human are priority zero; help from another agent uses the same product experience. Continuity preserves useful context, decisions, artifacts, and outstanding work across sessions and authorized handoffs.

A working local proof now includes an authenticated request/answer service, a minimal human dashboard, a CLI, durable recovery and an environment listener. See [Run the local proof](docs/local-proof.md). The canonical [unblock skill](skills/unblock/SKILL.md) and [local Claude/OpenAI development exports](docs/local-plugins.md) now include an agent-bound MCP bridge. Remote OAuth/MCP integration, installed-host verification, official distribution and public app deployment remain in progress.

[Create your own dashboard](docs/personal-dashboard.md): fork the canonical source, try it locally, and follow the Fulcra-hosted setup path with your own account. [Live integration prerequisites](docs/live-integration.md) distinguish what still needs a production service or host/account access.

## Planning documents

- [Review resolution and next build](docs/review-resolution.md): proposed decisions for authentication, identity, storage and the first working loop.
- [First-release specification](docs/superpowers/specs/2026-10-16-unblock-first-release.md): the concrete scope ready for review.
- [Agent work pickup](docs/superpowers/specs/2026-10-16-agent-work-pickup.md): Claude and ChatGPT routes, local listeners and recovery.
- [Listener setup](docs/listener-setup.md): the minimum onboarding contract for every connected agent.
- [Requirements](docs/requirements.md): confirmed user decisions, including clean-slate architecture, official marketplaces, short naming, and forkable personal dashboards.
- [Current platform assessment](docs/current-platform-assessment.md): evidence and the proposed architecture.
- [Marketplace release plan](docs/marketplace-release-plan.md): package, naming, invocation, and submission rules.
- [Broader design](docs/superpowers/specs/2026-10-16-unblock-any-agent-design.md): product direction and future scope.

The intended canonical source is `ashfulcra/unblock-any-agent`. Proposed plugin identity: `unblock`; proposed display name: Unblock Any Agent. Marketplace names and the short command remain subject to validation. No namespace is reserved.
