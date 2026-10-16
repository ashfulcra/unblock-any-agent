# Remaining OpenAI connection work

Status: proposed next integration, 2026-10-16. The Fulcra web baseline already uses the template's supplied public client, device flow, authenticated cookies and managed deployment. A new registered OAuth client or external database is not a prerequisite for that web app or its forks. Keep those working routes intact.

## Evidence so far

| Route | Observed result | Remaining limit |
| --- | --- | --- |
| Claude source install | The complete 0.4.0 export installed from the canonical GitHub marketplace in an isolated Claude configuration. Earlier actual Claude recovery and independent listener continuation passed. | This is GitHub distribution; official directory acceptance and persistent startup remain separate. |
| Explicitly configured OpenAI native runtime | Codex CLI 0.144.4 discovered seven tools, recovered only the dedicated synthetic worker's empty work with `source: checked`, and denied the same tool after verified revocation. | This test supplied the MCP command and private profile through per-thread configuration. It does not prove the uploaded plugin or ChatGPT web. |
| Account-backed private OpenAI plugin | After explicit MCP profile-path configuration in a temporary private package, all seven tools appeared in the actual Codex desktop task. Its real `recover_work` returned `source: checked` for the exact synthetic worker; after native revocation readback, the same tool denied access. | The shell-process environment alone did not configure the app-managed plugin. The separate standalone CLI attempts still failed initialization. The temporary setting was removed and original MCP configuration restored/read back, with forward-only private version 0.4.2. Public source remains 0.4.0. |
| Deployed HTTP MCP | Modern SDK replacement recovery, answer use, action/effect evidence, progress and revoked-token denial passed. | The endpoint accepts native worker grants. ChatGPT OAuth discovery and event delivery have not been implemented or verified. |

The first selected-plugin model attempt failed because that standalone CLI rejected its configured model. A later test used the CLI's advertised default and completed its model turn, but still failed the MCP handshake. Explicit private-package profile configuration subsequently passed in the actual desktop task. These are separate observations. All temporary worker grants from these probes were revoked with native readback; the original profiles, failed attempts and receipts were retained privately. No public namespace or official listing was obtained.

## Authentication direction

Reuse existing Fulcra authorization capabilities before considering another authorization service. The existing Fulcra MCP service already advertises dynamic client registration and S256 PKCE. OpenAI also supports Client ID Metadata Documents, which avoid a manual registration step. Neither is evidence that an existing bearer token is valid for a different resource. [OpenAI authentication contract](https://developers.openai.com/plugins/build/auth)

The inspected Fulcra MCP implementation is pinned at [bb928b1](https://github.com/fulcradynamics/fulcra-context-mcp/tree/bb928b120901330c155e98e0beb1de973f4f52b9). Its [provider](https://github.com/fulcradynamics/fulcra-context-mcp/blob/bb928b120901330c155e98e0beb1de973f4f52b9/fulcra_mcp/provider.py) persists issued token/grant records and its [credential layer](https://github.com/fulcradynamics/fulcra-context-mcp/blob/bb928b120901330c155e98e0beb1de973f4f52b9/fulcra_mcp/credentials.py) handles upstream refresh. The inspected authorization state/code path is process-local, and does not establish propagation of a distinct Unblock resource. Reuse is a candidate integration, not an already available connection.

The preferred feasibility slice is a separate Unblock protected resource alongside the existing authorization service, with only the seven worker operations. Confirm an extension point and deployment authority before changing the shared service. Preserve the existing Fulcra resource and its clients. Do not add all personal-data tools to the Unblock package simply to obtain a working authorization flow.

That slice must establish:

1. **Resource binding.** Preserve the exact resource through authorization, one-time code exchange, access tokens and refresh. Reject tokens issued for the existing Fulcra MCP resource at Unblock, and reject Unblock tokens at that resource. Bind client, verified human account, resource and explicit worker scope together.
2. **Worker and dashboard binding.** The human approves the actual worker/environment and dashboard. Resolve identity from verified authorization and an owner-approved binding. A model-supplied agent ID, sender label or URL cannot select another principal. A personal fork needs a proven owner/deployment association. Never forward an upstream owner token to an arbitrary supplied URL.
3. **Credential custody.** Keep upstream owner credentials and refresh entirely server-side. Give the worker only its narrow access. Native expiry, renewal lineage, revocation and pending-readback rules still apply. Decide and test the bridge to the existing native grants before advertising a connected plugin.
4. **Durable authorization state.** Survive instance replacement and concurrent sign-ins/token exchange without crossing human accounts or consuming a code twice. Use demonstrated durable platform facilities. An in-memory authorization-code or subscription map is insufficient for the serverless web app.
5. **Discovery that reflects reality.** Publish protected-resource metadata and an authentication challenge only when the advertised issuer/resource flow actually works. The current native-grant `/mcp` endpoint must not advertise invented OAuth support.

These are engineering and capability checks. They do not reinstate the withdrawn manual OAuth-client-registration gate for the web app. No shared Fulcra service configuration or production authorization behavior has been changed by this proposal.

## Pickup after connection

For supported ChatGPT Work surfaces, evaluate MCP Events on the authenticated resource. Require durable subscriptions, verified HTTPS callbacks, signed delivery, expiry/revocation handling, duplicate-safe retries and a correct work context. A successful webhook response is receipt; require the intended agent's acknowledgment and useful continuation separately. [MCP Events contract](https://developers.openai.com/plugins/build/mcp-events)

Keep the existing independent listener/tick instructions available for other runtimes. Starting a local MCP process is not installing a persistent receiver. Do not transfer a Work/web event claim to local Codex, or a restricted Claude listener result to an arbitrary busy/closed session.

## Acceptance and release dependencies

The explicit-profile desktop plugin test now covers discovery, checked recovery and later revocation. Generalize the supported per-environment configuration instructions without bundling credentials or claiming that a shell variable configures the desktop app. Keep that result separate from remote authorization. Then prove a real ChatGPT web connection, reconnect/expiry/revocation, and delayed answer pickup after the requester becomes idle or is replaced. Preserve pending work when a receiver or authorization source is unavailable.

Use two distinct authorized test accounts to prove isolation and a personal fork. The clean source/example-only configuration already builds; the second-account deployment remains pending selection of its intended owner. Official publication additionally needs the chosen verified publisher and source license, eligibility, reviewer access, listing metadata and actual portal checks. The private plugin's account-normalized author fields do not select the public publisher.

The canonical source, skill, fork instructions and star links remain at [ashfulcra/unblock-any-agent](https://github.com/ashfulcra/unblock-any-agent).
