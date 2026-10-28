# Create your own dashboard

[Fork Unblock Any Agent](https://github.com/ashfulcra/unblock-any-agent/fork) to keep your dashboard changes under your own account. Shared skills, contributions and optional stars belong on the [original repository](https://github.com/ashfulcra/unblock-any-agent).

The [Fulcra-hosted pilot](https://unblock-any-agent.my.fulcra.ai) provides sign-in, needs, human answers, scoped agent connections, replacement recovery and a separate listener route. Its template already supplies Fulcra sign-in; no new OAuth client registration is needed. Start with the hosted setup below for your own dashboard. The [separate local proof](local-proof.md) is also available for local evaluation.

## Try your fork locally

1. Clone your own fork and follow [Run the local proof](local-proof.md).
2. Create your own owner/workspace and separately enroll each agent and environment listener. Never copy another person's `.state`, credentials or route files into your fork.
3. Start the listener before answering a synthetic request. Verify that the correct worker retrieves context, acknowledges the answer and records a real next step.
4. Use the [shared skill and platform exports](local-plugins.md) as additional entry points into that same workspace.

## Build the Fulcra-hosted version

Start with [`web/`](../web/README.md) in your fork. Use the current [Fulcra web-app skill](https://github.com/fulcradynamics/agent-skills/tree/main/skills/build-and-deploy-a-web-app) with your fork and your own account. Its default Svelte template supplies Fulcra sign-in; keep that flow intact while adding the dashboard through authenticated Fulcra APIs. Follow its required baseline/evaluation workflow rather than claiming success from a deployment alone.

The deploying agent follows the Fulcra skill with the user's current CLI sign-in. Reuse that user's saved workspace, harness annotation and deploy project; create them through the skill only when absent. Create a distinct product `MomentAnnotation` for Unblock records. The skill's `fulcra-api data-type create MomentAnnotation "..."` command and deploy-project API return the actual identifiers. Preserve uncertain creation results and reconcile them before retrying. The agent handles those identifiers; the user need not find bucket names or edit configuration by hand.

From the repository root, prepare configuration using the actual identifiers returned for that user:

```sh
python3 -m unblock.fulcra_setup \
  --project-id YOUR_DEPLOY_PROJECT_UUID \
  --harness-annotation YOUR_HARNESS_ANNOTATION_UUID \
  --product-annotation YOUR_PRODUCT_ANNOTATION_UUID \
  --workspace workspace/your-unblock \
  --state /ABSOLUTE/PRIVATE/unblock-setup.json \
  --env-file /ABSOLUTE/YOUR-FORK/web/.env
```

This checks the current Fulcra owner, the exact deploy project and both active owned annotations before writing. It keeps the template's public sign-in defaults, sets the actual returned dashboard origin and generates the server signing key once. The private journal must stay outside the checkout. Repeat the same command after interruption; it preserves the signing key and rejects changed accounts/resources, unsafe files and conflicting environment contents. Use a fresh environment output path if one already exists without this journal; existing configuration is never overwritten. `--check` performs the same live resource checks without creating a journal or environment file.

Retain the journal and environment securely: changing the signing key invalidates existing grants and prevents reading old signed records unless the old key is retained. Never copy the original deployment's owner, annotations, key, credentials or project. See [web setup](../web/README.md) and [native configuration](native-pilot.md#fork-configuration).

The app uses authenticated Fulcra backend routes and native annotation persistence. **This deployment needs no external GCS bucket or shared MCP issuer rollout.** Those belong only to the optional remote issuer integration. Keep credentials and runtime settings outside Git and browser-delivered code. A fork does not grant access to anyone else's agents or data.

Create one Fulcra deploy project for your dashboard, save its project identifier privately and reuse it for later deploys. Use the actual production domain returned by the service; do not guess availability of a `my.fulcra.ai` address. The user does not need a separate Vercel account for the documented Fulcra deployment route. [Fulcra deployment instructions](https://github.com/fulcradynamics/agent-skills/blob/main/skills/build-and-deploy-a-web-app/references/deploy.md)

Enroll your own worker and a separate environment listener, then follow the [native setup](native-pilot.md) and [listener guide](listener-setup.md). An optional [trusted renewal operator](native-renewal.md) uses your existing CLI login; installation does not start it or a scheduler.

Verify sign-in, the intended workspace, answer submission, isolated access, delayed agent pickup and continuity after reconnect. Test with a clean second account before advertising self-serve multi-account deployment. Keep source/star links pointed at the original repository.

## Agent setup prompt

> Help me deploy my own Unblock Any Agent dashboard from my fork using Fulcra's build-and-deploy-a-web-app skill. Use my own current Fulcra login, workspace, harness/product annotations and deploy project; preserve the supplied template sign-in. Reuse saved resources, reconcile uncertain creates, then run the canonical `python3 -m unblock.fulcra_setup` command to verify ownership and generate private environment configuration. Keep its journal outside the checkout and reuse its signing key. Deploy using the skill's existing Fulcra project flow, passing the environment at build and runtime. Evaluate the actual deployed request → answer → correct agent continuation and reconnect journey. No shared issuer rollout, external GCS bucket, copied maintainer binding or new OAuth client is needed for this core app. Keep canonical source/contribution/star links at ashfulcra/unblock-any-agent and report actual host/deployment limits separately.

## Keep a fork updated

Add the original repository as `upstream` if your fork's clone has only `origin`. Fetch upstream changes and review them before merging into your own branch. Rebuild plugin exports after source changes. Redeploy with the saved Fulcra deploy project and fresh scoped deployment access, then repeat sign-in, access and delayed-pickup checks. Preserve private credentials and local workspace settings; they do not belong in either Git remote.

## Verification so far

A fresh clone of the published source passed dependency installation, Svelte check and production build using only `.env.example` with blank private fields. The probe first omitted the documented copy step and was corrected in the same clone. This establishes clean source/build setup. A different account’s sign-in, own annotations/key, deployment and complete agent loop still need an explicitly authorized test account; they are not established by the maintainer’s account or by a successful build.
