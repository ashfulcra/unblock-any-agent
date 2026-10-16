# Live integration prerequisites

The local proof and package-process checks pass. This is the next integration boundary, not a claim that the first public release is finished. Follow the first-release sequence: prove each real host connection and advertised pickup route before expanding the interface and detector.

## P1 — Fulcra-native web baseline

Correction, 2026-10-16: a **new OAuth client registration is not required** to build this dashboard with the Fulcra web-app skill. Its official Svelte template already supplies Fulcra sign-in/device flow and public client configuration. Fulcra deploy projects provide the hosted app target. The maintainer's earlier registration/runtime gates incorrectly turned a proposed custom MCP backend into a prerequisite for all web work.

Use the supplied authentication flow unchanged, the authenticated Fulcra APIs and workspace/files/annotations, and the skill's deployment/evaluation harness. The working hosted baseline and populated owner-only harness passed independent evaluation at [unblock-any-agent.my.fulcra.ai](https://unblock-any-agent.my.fulcra.ai). [Evaluation evidence](reviews/2026-10-16-fulcra-baseline-review.md) distinguishes direct API checks from browser checks through a read-only authenticated QA proxy. Evaluate native persistence against the required retry, conflict and identity guarantees before introducing a separate store; a missing custom database URL does not block this baseline.

**Current native pickup:** both exported manifest commands recover native work; a separate native listener routed a delayed browser answer into a restricted synthetic Claude session after the originating MCP process closed. Replacement preserved the marker and action count; stopped/failed/repaired routes were exercised. [Native host review](reviews/2026-10-16-native-host-review.md) records evidence, fixes and limits. **Next action:** finish review/publication of the bounded renewal path, then verify selected actual host connections. The bounded M2 flow is proven: actual agent enrollment/request, browser answer, replacement subprocess recovery, observed continuation, corrected context/draft protection, retained settled action history and permission negatives. Credentials expire with the original access token, within one hour; a separate explicit [trusted operator](native-renewal.md) has passed bounded live renewal and outage recovery. Its final review/publication, persistent startup and real second-account acceptance remain open. See [pilot evidence](reviews/2026-10-16-native-loop-review.md). M1 is complete: workspace and actual harness events were written/read back, the template was deployed using one saved project, anonymous/non-owner access was denied, and the completed run appeared in the owner dashboard. Existing CLI authentication supports tool-based evaluation. The skill treats the user's first interactive sign-in confirmation as a nonblocking outstanding item.

A remote MCP authorization gateway is a separate integration question. If the chosen plugin service eventually needs its own OAuth resource boundary, verify that boundary against the actual Fulcra/MCP capabilities at that time. It is not a prerequisite for the Fulcra-hosted dashboard.

Sources: [Fulcra web-app skill](https://github.com/fulcradynamics/agent-skills/tree/main/skills/build-and-deploy-a-web-app), [template client configuration](https://github.com/fulcradynamics/app-template-svelte/blob/main/.env.example), [Fulcra deployment path](https://github.com/fulcradynamics/agent-skills/blob/main/skills/build-and-deploy-a-web-app/references/deploy.md).

## P2 — Actual host pickup

The restricted new Claude session route passed against both the local proof and deployed native pilot. Native scope/dispatch tests and actual delayed/replacement/stopped/failed/repaired routes passed. This remains a bounded synthetic worker, not general arbitrary-session wake. The exact local package process also passed tool discovery and recovery. Actual installed Claude/ChatGPT plugin behavior, a busy target, closed-session behavior and ChatGPT MCP Events remain open integration cases. Test only the capabilities of the actual selected host. No account-level plugin install or new UI task was created by these source-development checks.

**Unblock action:** connect the working service in each pilot host with the correct authenticated identity and its supported receiver; verify delayed delivery without a human check prompt, busy/replacement handling, queued-versus-acknowledged progress and stopped-receiver recovery. A separate environment listener remains the baseline where native wake is absent. Remote web tests use the Fulcra-native baseline in P1; plugin MCP authorization is assessed separately.

## P3 — Official publication

Source publication is complete; marketplace publication is separate. Required evidence includes the actual publishing identity and portal access, name validation, a clean host install, supported public package, listing/support/privacy/terms material, project license decision and reviewer access. Keep the public web/remote-MCP goal in the initial universal package plan.

OpenAI's local MCP submission route requires approved-partner organization allowlisting. Have the publishing organization confirm that access with its OpenAI representative before using the documented local-MCP upload flow. No such eligibility has been verified here. [Desktop-only submission](https://developers.openai.com/plugins/deploy/desktop-only)

**Unblock action:** identify the verified publishing organizations, confirm portal and applicable partner access, and complete the real service/host checks before submission. A GitHub name or passing manifest does not reserve `/unblock` or either directory namespace.

## P4 — Personal hosted dashboards

Use [personal dashboard instructions](personal-dashboard.md) for forking, account separation and the Fulcra deployment workflow. The native response view, sign-in and harness are live; and a hosted fork follows P1 and preserves the supplied Fulcra authentication. Hosted clean-account acceptance remains open.
