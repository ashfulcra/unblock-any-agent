# Fulcra issuer integration candidate

This patch keeps Unblock's custom integration in the [canonical skills/plugin repository](https://github.com/ashfulcra/unblock-any-agent). It adds an optional resource issuer to the existing Fulcra MCP service, using its current upstream sign-in configuration and `/callback`. No new OAuth client registration is required for the dashboard, forks, or this integration's upstream sign-in.

Status: source reviews and returned corrections are recorded below; their actionable findings were reproduced and corrected. See [review disposition](review.md). The candidate is disabled by default. Real GCS transaction acceptance, upstream login, ChatGPT web connection and event pickup remain unverified. Existing local Claude/OpenAI plugin and native dashboard routes remain available.

## Reproduce from a clean source checkout

From this repository's root, choose a new sibling checkout:

```sh
UNBLOCK_SOURCE="$(pwd)"
UNBLOCK_ISSUER_TARGET="../unblock-issuer-candidate"
git clone https://github.com/fulcradynamics/fulcra-context-mcp.git "$UNBLOCK_ISSUER_TARGET"
git -C "$UNBLOCK_ISSUER_TARGET" checkout --detach 8d0d768c07eb41c59ccc15366ba1fbfc51638c85
git -C "$UNBLOCK_ISSUER_TARGET" apply --check "$UNBLOCK_SOURCE/integrations/fulcra-issuer/unblock.patch"
git -C "$UNBLOCK_ISSUER_TARGET" apply "$UNBLOCK_SOURCE/integrations/fulcra-issuer/unblock.patch"
cd "$UNBLOCK_ISSUER_TARGET"
uv sync --locked
uv run --locked pytest -q
```

`manifest.json` pins the upstream commit, patch digest and resulting changed-file digests. The locked source suite passes 642 tests, with 16 inherited skips, five inherited expected failures and one inherited warning. The patch contains the source, HTTP and concurrency tests, and `docs/unblock-issuer.md` operator instructions. It changes no production configuration. Keep upstream's existing license and the accompanying `LICENSE.upstream` notice with upstream context; Unblock's public publisher/license choices remain release prerequisites.

## Scope

The human approves a verified owned dashboard and specific agent/environment. The client receives a bounded native worker grant. Owner credentials stay in private server state, isolated per login. Conditional GCS claims protect one-time code exchange and refresh; exact intent/readback protects enrollment and revocation. The new `/unblock` issuer is separate from the original personal-data token namespace.

Pilot policy requires an explicit resource list. A later explicit all-owned policy supports anybody's verified personal fork without a central per-person allowlist. Both policies use the actual authenticated owner/project/domain lookup before forwarding owner credentials. The default is closed.

Before enabling the shared service, obtain its operator's approval and an authorized disposable-object test bucket, verify GCS CAS across two clients, and validate upstream login on the existing callback origin or an already-authorized staging callback. Then validate actual ChatGPT connection, expiry/reconnect/revocation and replacement recovery before advertising that issuer in a dashboard's protected-resource metadata. Establish the operational receiver for unresolved source/credential effects before claiming unattended coverage.

The existing Fulcra webapp skill already handles dashboard authentication and managed deployment. This optional integration is the remaining remote plugin connection work, not a prerequisite for building or forking the web app.


## Bounded acceptance and recovery tooling

The patched source now includes `python -m fulcra_mcp.unblock_probe` and `python -m fulcra_mcp.unblock_operator`. Their `--help` commands discover no credentials. Full commands and scope rules are in the patched `docs/unblock-issuer.md`.

The probe uses two clients and exactly two synthetic hashed objects under a UUID-scoped `unblock-acceptance/<label>` prefix. It validates exact submitted CAS/claim records and conditionally cleans only its own objects. A private recovery manifest, including its directory entry, is synced before credential discovery/effects. `--cleanup-only` reuses that frozen manifest and retains the original outcome across retries.

The operator inspects at most 64 explicit code keys for one exact dashboard resource. It reports allowlisted metadata; unavailable or malformed source stays unresolved. It is read-only unless `--recover-revocations` is supplied, and then only already-requested revocations may be reconciled after a fresh provider resource check. Each finite invocation needs a new private report. It installs no scheduler, enumerates no new work and proves no unattended receiver coverage.

A fresh source review found three Important issues in these tools; all were reproduced and fixed in one pass. A later automated review found incomplete completed publications could appear checked; required publication fields and derived references are now validated before cleanup, with 40 additional regression cases. A further returned review exposed incomplete saved intents. Bridge and operator now share the full structural checks, and provider cleanup repeats them on its fresh root read. The 207 operator/probe/report cases use generation-aware storage doubles and the actual provider. Real bucket acceptance still requires an authorized operator environment; neither local fixtures nor source publication replaces that check.
