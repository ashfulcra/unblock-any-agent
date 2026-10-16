# Create your own dashboard

[Fork Unblock Any Agent](https://github.com/ashfulcra/unblock-any-agent/fork) to keep your dashboard changes under your own account. Shared skills, contributions and optional stars belong on the [original repository](https://github.com/ashfulcra/unblock-any-agent).

The current dashboard works locally. A Fulcra-hosted version remains integration work: do not deploy the local bootstrap-auth server publicly. The [live integration prerequisites](live-integration.md#p1--registered-identity-provider-and-public-service) describe the service and authentication it must connect to.

## Try your fork locally

1. Clone your own fork and follow [Run the local proof](local-proof.md).
2. Create your own owner/workspace and separately enroll each agent and environment listener. Never copy another person's `.state`, credentials or route files into your fork.
3. Start the listener before answering a synthetic request. Verify that the correct worker retrieves context, acknowledges the answer and records a real next step.
4. Use the [shared skill and platform exports](local-plugins.md) as additional entry points into that same workspace.

## Build the Fulcra-hosted version

Use the current [Fulcra web-app skill](https://github.com/fulcradynamics/agent-skills/tree/main/skills/build-and-deploy-a-web-app) with your fork and your own account. Its default Svelte template supplies Fulcra sign-in; keep that flow intact while connecting the dashboard to the authenticated Unblock service. Follow its required baseline/evaluation workflow rather than claiming success from a deployment alone.

Connect the intended backend and workspace through the authenticated service. Keep service credentials and runtime settings outside Git and outside browser-delivered code. A fork does not grant access to anyone else's agents or data.

Create one Fulcra deploy project for your dashboard, save its project identifier privately and reuse it for later deploys. Use the actual production domain returned by the service; do not guess availability of a `my.fulcra.ai` address. The user does not need a separate Vercel account for the documented Fulcra deployment route. [Fulcra deployment instructions](https://github.com/fulcradynamics/agent-skills/blob/main/skills/build-and-deploy-a-web-app/references/deploy.md)

Verify sign-in, the intended workspace, answer submission, isolated access, delayed agent pickup and continuity after reconnect. Test with a clean second account before advertising self-serve multi-account deployment. Keep source/star links pointed at the original repository.

## Agent setup prompt

> Help me create my own Unblock Any Agent dashboard from my fork. Read its requirements, current implementation evidence and live integration prerequisites. Use my own Fulcra account and workspace, preserve the template sign-in flow, and keep secrets out of source and browser code. Follow the current Fulcra web-app skill's baseline and evaluation workflow. Reuse a saved deploy project or create one if none exists; retain its actual returned domain. Verify the complete request → human answer → correct agent continuation flow and reconnect behavior. Tell me exactly which live integration prerequisite is missing if the hosted version cannot yet work. Keep shared skill/source and optional star links pointed at ashfulcra/unblock-any-agent.

## Keep a fork updated

Add the original repository as `upstream` if your fork's clone has only `origin`. Fetch upstream changes and review them before merging into your own branch. Rebuild plugin exports after source changes. Redeploy with the saved Fulcra deploy project and fresh scoped deployment access, then repeat sign-in, access and delayed-pickup checks. Preserve private credentials and local workspace settings; they do not belong in either Git remote.
