# Current Platform Assessment and First Build Recommendation

Assessed 2026-10-16. This is a planning recommendation based on current primary documentation, inspected source, and one read-only account capability check. Product write flows, plugin authorization, native wake behavior, and clean-account deployment have not yet been exercised end to end.

## Recommendation

Start platform-first with a thin application layer: use Fulcra for durable work context, structured requests/results, artifacts, and selected sharing capabilities; expose a consistent product experience through the web app, skills, and platform plugins. Use native host capabilities for notifications, message delivery, and session lifecycle handling where they work. Keep the product identity and recoverable context independent of any one session.

The application layer owns the user-facing operations and access checks. It does not need to become a universal task manager or recreate Coord. Begin with the smallest persistent state needed for pending requests and continuity. A separate transactional database or workflow service is conditional on a demonstrated requirement that current platform capabilities cannot satisfy simply.

This recommendation is an architectural inference. Two matters need targeted implementation evidence before the concrete architecture is finalized: end-user authorization across browser and plugin surfaces, and concurrent/stale response handling using the selected persistence primitives.

Official public plugin distribution is now an explicit requirement. The [marketplace release plan](marketplace-release-plan.md) adds platform-specific package exports, naming/command verification, and an initial remote-MCP-capable OpenAI submission to the early critical path. Current official-directory restrictions determine the public package; local runtime capabilities alone do not establish submission eligibility.

## Current findings

| Area | Current evidence | Implication and limit |
| --- | --- | --- |
| Fulcra structured data | The live authenticated catalog returned recordable v1 `Event` and `Metric` base types. Current MCP source supports custom fields, record IDs, reading records, and retries with the same record ID. | Prefer current structured primitives over legacy note envelopes. This read establishes available base types, not a successful product write or a conditional-update guarantee. |
| Fulcra continuity and discovery | Current platform documentation describes versioned files. Current MCP source exposes update summaries and shared-account discovery. | Requests and useful context can survive a host session. Update discovery is a candidate mechanism; push delivery and transactional queue semantics were not established. |
| Fulcra web app | The current Svelte template provides device-flow sign-in with server-side API proxying. The referenced deployment skill creates/reuses a project and returns its production domain. | A forkable authenticated web app is a credible starting point. A clean-account deployment and production persistence still need verification. |
| ChatGPT plugin entry | Current OpenAI documentation supports skills, MCP tools, optional MCP Apps UI, and extensions for sidebar and conversation panels. | The product can provide workflow instructions and an interactive entry point. Individual extensions remain dependent on host capabilities and availability. |
| ChatGPT interaction and continuation | Current UI extensions support sending context to an active conversation, and to a new conversation on supported desktop/Work web surfaces. Published workspace agents have a separate trigger API with stable conversation keys and idempotent trigger requests. | Offer a direct user-initiated Continue path. Treat published-agent automation as an optional verified route; the API does not establish access to arbitrary existing chats. |
| ChatGPT background lifecycle | Current user documentation excludes plugin lifecycle hooks from cloud-orchestrated Work; synced Work has separate admin-defined MCP-hook support. | Do not assume a plugin installs one universal always-on listener or compaction hook. Durable context must be retrievable without that assumption. |
| Claude live delivery | Mods document background prompt submission that waits for an idle session. Channels push into running sessions but are preview and allowlist gated. | Test mod-based pickup in supported Claude Code hosts first; do not assume channels are distributable for this plugin or that either route restarts a closed session. |
| Claude continuity | Current mod reference includes compaction and session lifecycle events and a machine-shared store; its documented start/resume behavior has important distinctions. | A mod can help capture context and react to lifecycle changes. Cloud-visible or cross-machine continuity needs durable shared context beyond a local store. Verify lifecycle behavior against the exact installed host. |
| Multiple human identities | Current OpenAI MCP guidance authenticates end users through OAuth and server-side checks. Fulcra supports selective sharing of owner-scoped context. | Resolve identity from authentication and team permissions. Neither a supplied sender name nor a shared conversation defines all action permissions. Verify distinct-account behavior before shipping multi-human teams. |

## Work-pickup assessment correction, 2026-10-16

The initial assessment omitted [MCP Events](https://developers.openai.com/plugins/build/mcp-events). OpenAI documents webhook subscriptions that can trigger work in ChatGPT Work on web, desktop with Cloud selected, and dots. They require MCP 2.0 (`2026-07-28`), durable subscriptions, callback verification, and signed delivery. A webhook acknowledgment proves receipt, not processing. This is the preferred route to evaluate for supported Work surfaces; local Codex pickup is not established by that documentation. Plugin installation alone does not create a subscription.

This changes the earlier emphasis on manual Continue and workspace-agent triggers. The absence of plugin lifecycle hooks does not imply the absence of event-triggered work. No subscription, server, or end-to-end pickup has been installed or verified for this project. The [pickup design](superpowers/specs/2026-10-16-agent-work-pickup.md) defines the required proofs and separates inbound work from detecting an overdue obligation.

## Primary sources

- [Fulcra platform concepts](https://docs.fulcradynamics.com/fulcra-platform/): data types, records, provenance, and versioned files.
- [Fulcra MCP tools](https://github.com/fulcradynamics/fulcra-context-mcp/blob/main/fulcra_mcp/tools.py): `record_data`, `get_records`, `get_data_updates`, and sharing-related tool contracts. Source inspection is not a live acceptance test.
- [Fulcra app template](https://github.com/fulcradynamics/app-template-svelte/tree/613a3d817df7933e73b6fb9cbda86fd7377b8e6b): current inspected web baseline.
- [Fulcra deployment guide](https://github.com/fulcradynamics/agent-skills/blob/main/skills/build-and-deploy-a-web-app/references/deploy.md): personal deployment flow.
- [OpenAI plugin architecture](https://developers.openai.com/plugins/concepts/plugins): skills, MCP, and optional UI.
- [OpenAI plugin extensions](https://developers.openai.com/plugins/build/extensions): native entry points and interaction surfaces.
- [OpenAI plugin authentication](https://developers.openai.com/plugins/build/auth): end-user authentication and server authorization requirements.
- [OpenAI UI message extensions](https://github.com/openai/mcp-extensions/blob/main/docs/spec.md#uimessage-extensions): supported active/new-conversation interaction. Consult runtime capability advertisement.
- [Workspace agent triggers](https://developers.openai.com/workspace-agents/trigger-runs): triggering published agents, conversation keys, idempotency, and status limits.
- [ChatGPT plugin support](https://learn.chatgpt.com/docs/plugins): surface-specific lifecycle-hook support.
- [Claude channels](https://code.claude.com/docs/en/channels): delivery into a running session.
- [Claude mods](https://code.claude.com/docs/en/plugins/mods/overview) and [mod reference](https://code.claude.com/docs/en/plugins/mods/reference): UI, session operations, and lifecycle events.

The authenticated read-only base-type check is retained in the maintainer's private research evidence. No user data, credentials, source bindings, or private identifiers belong in this public planning document.

## Candidate comparison

| Approach | Current assessment |
| --- | --- |
| Platform-first with thin application logic | Recommended first. Fits the four entry points, owner-controlled continuity, and forkable web-app requirement while minimizing additional infrastructure. Verify authorization and response concurrency rather than assuming them. |
| Dedicated request/workflow service plus Fulcra context | Keep available if transactional behavior, durable background work, or multi-user operations materially simplify the product. The additional service must justify its deployment and operating burden. |
| Host-native coordination with a shared view | Use host-native capabilities inside the selected design. As the entire architecture, this leaves unproven cross-host durability and absent-session behavior. |

## First build slice

Build one real human-unblocking and continuity journey, beginning with the web app and a skill used by an existing agent:

1. The agent saves useful work context and a specific request for the human, with its recommended answer and next action.
2. The signed-in human sees and answers that request in the web app.
3. The original session is ended deliberately for the test. The saved request and answer remain available.
4. A new authorized session, using the skill or a supported plugin interaction, retrieves the relevant context, decisions, and answer.
5. That agent reconciles current state and takes the next useful action without asking the human to repeat the decision.
6. The dashboard shows the observed result or the concrete remaining obstacle. Repeating the delivery or opening another session does not duplicate a consequential action.

Manual opening of the replacement session is acceptable for the first continuity proof. Automatic wake is an additional, separately verified acceptance case. The first release still includes both explicit and detected requests and all four entry points; this slice establishes the common behavior before completing those surfaces.

## Next concrete design work

Specify the minimal request, human response, and continuity context needed for that journey. Decide the browser/plugin authorization boundary, verify the selected record/update behavior, and make the personal-deployment setup explicit. Choose native Claude delivery and ChatGPT continuation paths by the exact runtime capabilities instead of promising universal background reachability.

Then produce a small executable implementation plan for the reviewed slice. Broader detection, the full plugin interfaces, multiple human teams, richer continuity, delegation, and release packaging build on the same proven journey.
