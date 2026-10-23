# Unblock Any Agent — Fulcra web app

Hosted baseline: https://unblock-any-agent.my.fulcra.ai

Canonical source, shared skills, forks and optional stars: https://github.com/ashfulcra/unblock-any-agent

Based on the official [Fulcra Svelte template](https://github.com/fulcradynamics/app-template-svelte/tree/613a3d817df7933e73b6fb9cbda86fd7377b8e6b). The supplied public Fulcra client/device-flow configuration works locally and after deployment. **No new OAuth application, callback allowlist or separate database is required for the web baseline.** Authentication behavior is preserved; changes to supporting auth files are typing/equivalent defaults only. The hosted single-owner pilot provides sign-in, the owner-only build harness, scoped short-lived agent enrollment, needs/answers and retained replacement recovery. See [native pilot setup and limits](../docs/native-pilot.md).

## Local setup

```sh
npm ci
cp .env.example .env
npm run dev
```

Set your own server-only `OWNER_USER_ID` and harness annotation in `.env` through the [Fulcra web-app skill](https://github.com/fulcradynamics/agent-skills/tree/main/skills/build-and-deploy-a-web-app). Reuse the annotation and deploy project stored in your own workspace progress. Never commit `.env`, tokens, owner identity or deployment bindings.

For a new account-owned deployment, use the [verified setup command](../docs/personal-dashboard.md#build-the-fulcra-hosted-version) from the repository root before creating `.env`. It verifies your existing Fulcra deploy project and distinct owned harness/product annotations, then creates private environment configuration and a retained signing-key journal. `python3 -m unblock.fulcra_setup --help` lists the inputs; your deploying agent obtains them through the Fulcra skill. Repeating setup does not rotate the key or overwrite an unrelated `.env`. Add `--check` for a live read-only preflight. Core app persistence and communication use Fulcra annotations, with no external GCS bucket or shared issuer prerequisite.

```sh
npm run check
npm run build
```

Type check currently reports zero errors and two existing template `on:click` deprecation warnings. A compatible lockfile update removed the inherited high/moderate audit advisories; four low cookie advisories remain inherited through SvelteKit 2, whose offered fix requires a major framework update. The app uses constant cookie names/path/domain; that upgrade is tracked separately from the baseline.

## Deployment and evaluation

Follow the skill's [Fulcra deployment flow](https://github.com/fulcradynamics/agent-skills/blob/main/skills/build-and-deploy-a-web-app/references/deploy.md). Create one deploy project, retain its actual returned domain privately, and use fresh project-scoped deployment access for subsequent deploys. Pass environment configuration at build and runtime. No personal Vercel account is needed for this path.

M1 is evaluated against actual authenticated API data, anonymous/non-owner denials and the owner dashboard's real run/evidence/workspace panels. An owner should try the interactive sign-in once; the skill tracks that confirmation as a nonblocking outstanding item. Deployment alone is not a completed milestone.

The repository's [personal dashboard guide](../docs/personal-dashboard.md) covers forking, ownership and later updates. A custom remote MCP OAuth gateway remains a separate plugin integration question and does not gate this app.
