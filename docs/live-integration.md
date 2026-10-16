# Live integration prerequisites

The local proof and package-process checks pass. This is the next integration boundary, not a claim that the first public release is finished. Follow the first-release sequence: prove real OAuth/client linking and both advertised pickup routes before expanding the interface and detector.

## P1 — Registered identity provider and public service

The live OAuth proof needs an application registration for Unblock with Fulcra as upstream sign-in. Required inputs are the provider issuer/discovery URL, registered client ID, supported scopes/audience and token authentication method, and the exact public gateway origin. Register that origin plus `/auth/callback` with the provider. A public PKCE client need not have a secret; a confidential client must store its secret only in the deployment secret store. Do not reuse the maintainer's personal CLI token as a public service credential.

Use a maintained MCP OAuth implementation for downstream discovery, PKCE/client registration, resource binding, durable grants, refresh and revocation. FastMCP's OAuth/OIDC proxy is a candidate, not an installed production boundary. Its documentation requires a registered upstream client and matching callback; public clients additionally need an explicit signing key. [Provider setup](https://gofastmcp.com/servers/auth/oauth-proxy#provider-setup-requirements)

The public service also needs a real hosting target and durable transactional storage. The loopback HTTP server refuses public bindings, and its SQLite files must not be placed on ephemeral serverless disks. Keep signing keys and grant storage stable across restarts. Neither a backend deployment target nor a production OAuth registration/credential reference is configured in this checkout or its runtime environment as of 2026-10-16.

**Unblock action:** provision or identify the intended public application runtime/store and registered upstream OAuth client; configure the exact origin/callback and provide secret references through that runtime's secret storage. Retain client metadata and callback readback without exposing secrets. Then implement the configured gateway and prove real sign-in, correct resource audience, account isolation, refresh, revocation and reconnect. Synthetic provider tests alone cannot close this live acceptance gate.

## P2 — Actual host pickup

The restricted new Claude session route passed. The exact local package process also passed tool discovery and recovery. Actual installed Claude/ChatGPT plugin behavior, a busy target, closed-session behavior and ChatGPT MCP Events remain open integration cases. Test only the capabilities of the actual selected host. No account-level plugin install or new UI task was created by these source-development checks.

**Unblock action:** connect the working service in each pilot host with the correct authenticated identity and its supported receiver; verify delayed delivery without a human check prompt, busy/replacement handling, queued-versus-acknowledged progress and stopped-receiver recovery. A separate environment listener remains the baseline where native wake is absent. Remote web tests depend on P1.

## P3 — Official publication

Source publication is complete; marketplace publication is separate. Required evidence includes the actual publishing identity and portal access, name validation, a clean host install, supported public package, listing/support/privacy/terms material, project license decision and reviewer access. Keep the public web/remote-MCP goal in the initial universal package plan.

OpenAI's local MCP submission route requires approved-partner organization allowlisting. Have the publishing organization confirm that access with its OpenAI representative before using the documented local-MCP upload flow. No such eligibility has been verified here. [Desktop-only submission](https://developers.openai.com/plugins/deploy/desktop-only)

**Unblock action:** identify the verified publishing organizations, confirm portal and applicable partner access, and complete the real service/host checks before submission. A GitHub name or passing manifest does not reserve `/unblock` or either directory namespace.

## P4 — Personal hosted dashboards

Use [personal dashboard instructions](personal-dashboard.md) for forking, account separation and the Fulcra deployment workflow. The current response view runs locally; a production fork must connect through P1 and preserve the owner's authentication. Hosted clean-account acceptance remains open.
