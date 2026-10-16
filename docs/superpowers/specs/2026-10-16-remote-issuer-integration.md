# Existing Fulcra issuer integration for Unblock

Proposed implementation slice, 2026-10-16. This extends the [remaining connection work](../../remote-connection-plan.md); it does not change the first-release requirements.

## Outcome

A human connects the remote Unblock MCP from ChatGPT through the existing Fulcra sign-in, approves one owned dashboard and agent/environment, and receives only the existing narrow worker capabilities. A later session can recover that same work. The dashboard and personal forks continue to use the supplied Fulcra webapp authentication without a newly registered OAuth client or external database.

Keep existing Fulcra MCP clients working. Evaluate this as a distinct protected resource, rather than giving an Unblock token access to all Fulcra tools. Existing native grants, listener instructions and local plugins remain usable during implementation.

## Verified starting point

The inspected issuer is `fulcradynamics/fulcra-context-mcp@bb928b120901330c155e98e0beb1de973f4f52b9`, locked to FastMCP 3.4.7, MCP 1.28.1 and google-cloud-storage 3.15.1. These are issuer dependency versions, not changes to this repository's local MCP runtime.

A no-credential probe of its actual provider observed requested resource loss and loss of login state after provider replacement. Its refresh model lacks a resource field. A separate four-case probe of the actual SDK token handler accepted both matching and mismatched resources for code and refresh exchange. The handler parses `resource` but does not check or forward it to the exchange methods. This is feasibility evidence, not a live issuer exploit or authentication test.

Reproduce the latter with:

```sh
uv run --no-project --with mcp==1.28.1 python scripts/probes/pinned_sdk_resource.py
```

The probe uses fake authentication/provider objects and `.invalid` URLs. All four statuses should be 200 in this pinned baseline; the implemented resource adapter must reject the mismatched cases before effects.

An actual read-only authenticated Fulcra project lookup matched the saved deployment and canonical domain. The platform exposes owner project list/detail operations; no deployment token was minted to establish that association. Cross-account source fixtures are supporting evidence; actual second-account acceptance remains separate.

## Selected contract

Use the existing authorization service and its registered upstream callback. Client registration for the plugin uses supported automatic discovery/registration. OpenAI documents CIMD and DCR support; neither a manually registered new client nor possession of an existing bearer establishes a different resource's authorization. [Authentication contract](https://developers.openai.com/plugins/build/auth)

A new resource flow has an immutable binding:

- Verified human subject, OAuth client and exact redirect URI.
- Requested resource, S256 challenge, approved deployment ID and canonical origin.
- Approved logical agent, environment and worker scope.
- Authorization transaction ID, expiry and later grant/renewal lineage.

Use cryptographically random internal login state and keep caller state separate. Credentials belong to that transaction and human, never a `client_id` slot shared by concurrent sign-ins. The human consent page displays the verified dashboard, agent and environment; arbitrary model-supplied values cannot establish ownership.

Resolve project ownership using the authenticated platform lookup before forwarding any owner credential to a dashboard. Construct the target only from the returned canonical project domain, require HTTPS, reject userinfo/nonstandard ports and redirects, and verify the exact requested resource. The resulting access token is the existing narrow native worker grant. Keep owner access/refresh credentials server-side. Never persist that token in the original Fulcra MCP access-token namespace; test replay rejection in both directions.

Keep a resource-specific durable state namespace. Use the existing configured GCS bucket through generation preconditions, not mounted file writes or process locks as cross-instance transactions. Missing storage/configuration fails closed for the new flow while existing flows retain their existing behavior. Code consumption, refresh claims and transaction transitions are compare-and-swap operations. Retain an enrollment/renewal intent before the effect and reconcile its exact receipt after uncertainty. Unknown upstream token-refresh effects require reconnect, not blind repetition.

The token endpoint validates resource before exchange, including duplicate form fields. A code request must match its stored resource. A refresh request may omit resource and inherit its stored binding, or repeat that exact value; any different resource or increased scope is rejected. A code is consumed once; a later use fails and triggers revocation of grants already issued from that code. An uncertain first response does not justify reusing the code. Refresh retries may replay only a frozen exact replacement within the bounded retry window; concurrent different requests cannot broaden authority. OAuth expiry reflects the native grant's actual capped expiry.

## Acceptance and boundaries

Prove two service instances and restarts, same-client/different-human concurrency, wrong/duplicate resources, redirect/verifier/client substitution, repeated codes, lost enrollment responses, refresh rotation, owner project removal/domain change, native revocation and both directions of resource replay denial. Preserve pending obligations throughout.

Only after an actual issuer deployment and end-to-end token flow should Unblock advertise its protected-resource metadata and challenge. Then test actual ChatGPT web discovery, connection, recovery, expiry/reconnect and denial after revocation. A successful local SDK test does not establish those outcomes.

MCP Events is the following slice: durable subscriptions, approved callback targets, signed delivery, duplicate handling, expiry/revocation and actual agent acknowledgment/useful continuation. Event receipt alone is insufficient. [Events contract](https://developers.openai.com/plugins/build/mcp-events)

Shared issuer production changes need authority for that service and a reviewed change. Prepare source and tests before that deployment decision. Official publisher/license, listing acceptance, namespace availability and the selected second account remain separate. No shared issuer, OAuth metadata, permissions or production credential state changed in this planning slice.
