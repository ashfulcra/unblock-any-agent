# Unblock Any Agent

Help agents obtain what they need and continue their work. Agents needing a human are priority zero; help from another agent uses the same product experience. Continuity preserves useful context, decisions, artifacts, and outstanding work across sessions and authorized handoffs.

A working local proof now includes an authenticated request/answer service, a minimal human dashboard, a CLI, durable recovery and an environment listener. See [Run the local proof](docs/local-proof.md). The canonical [unblock skill](skills/unblock/SKILL.md) and [local Claude/OpenAI development exports](docs/local-plugins.md) now include an agent-bound MCP bridge. The [Fulcra web baseline](https://unblock-any-agent.my.fulcra.ai) is deployed with sign-in and an owner-only build harness. The hosted single-owner pilot now supports scoped enrollment, needs, human answers, replacement recovery and a separate environment listener with verified restricted Claude pickup; see [pilot setup and limits](docs/native-pilot.md). An explicit trusted [renewal operator](docs/native-renewal.md) has passed bounded live expiry, outage and restart checks. The [native HTTP MCP endpoint](docs/native-http-mcp.md) has passed deployed replacement-continuity and revocation checks. Native [declared-update monitoring](docs/native-detection.md) separates missed updates from human questions. Persistent startup, actual ChatGPT authorization/events and official distribution remain in progress.

[Deploy your own Fulcra dashboard](docs/personal-dashboard.md): ask your agent to use Fulcra's build-and-deploy-a-web-app skill with your fork and current account. The verified setup command prepares private configuration from your own project and annotations. Fulcra supplies sign-in, persistence, communication and deployment; the core app requires no external GCS bucket or shared issuer rollout. [Live integration status](docs/live-integration.md) records remaining host/account acceptance.

[Self-contained plugin source candidates](plugins/README.md) are published at stable Claude and OpenAI paths for loading and review. They reproduce the canonical skill/runtime and remain development candidates, with no official listing or namespace reservation claimed.

## Planning documents

- [Review resolution and next build](docs/review-resolution.md): proposed decisions for authentication, identity, storage and the first working loop.
- [First-release specification](docs/superpowers/specs/2026-10-16-unblock-first-release.md): the concrete scope ready for review.
- [Agent work pickup](docs/superpowers/specs/2026-10-16-agent-work-pickup.md): Claude and ChatGPT routes, local listeners and recovery.
- [Listener setup](docs/listener-setup.md): the minimum onboarding contract for every connected agent.
- [Requirements](docs/requirements.md): confirmed user decisions, including clean-slate architecture, official marketplaces, short naming, and forkable personal dashboards.
- [Current platform assessment](docs/current-platform-assessment.md): evidence and the proposed architecture.
- [Marketplace release plan](docs/marketplace-release-plan.md): package, naming, invocation, and submission rules.
- [Broader design](docs/superpowers/specs/2026-10-16-unblock-any-agent-design.md): product direction and future scope.

The canonical source is `ashfulcra/unblock-any-agent`. Proposed plugin identity: `unblock`; proposed display name: Unblock Any Agent. Marketplace names and the short command remain subject to validation. No namespace is reserved.

Publisher: **Fulcra Dynamics**. Original project contributions are licensed under [Apache 2.0](LICENSE); [third-party notices](THIRD_PARTY_NOTICES) preserve upstream terms. Publisher verification and official marketplace acceptance remain separate from these source choices.
