# Native MCP over HTTP

## Intent and scope

Expose the deployed native pilot’s seven worker tools over MCP HTTP so remote runtimes can use the same need/answer/continuity contract without a local Python bridge. Preserve Ash’s requirements: human blockers first, stable owned obligations, replacement recovery, current capabilities and no inherited Coord topology. This is a transport slice, not a claim of a connected ChatGPT plugin, OAuth authorization flow or automatic event pickup.

Selected approach: mount the official TypeScript SDK handler in the existing Fulcra Svelte app and call the existing native service directly. Existing Fulcra MCP tools remain useful for shared files/messages, but their sender labels do not establish our narrow worker identity. A separate custom authorization service/database is not justified by this transport slice. No new registered OAuth client is a webapp prerequisite.

## Contract

Use `@modelcontextprotocol/server`2.3.1 with `createMcpHandler`, supporting modern2026-07-28 discovery and legacy stateless clients. Use its schemas/dispatch/transport rather than implementing JSON-RPC. Advertise server `unblock`0.4.0 and the exact seven native tools: ask_for_help, recover_work, get_work, revise_need, record_progress, begin_action, reconcile_action. Keep argument names and deterministic intent bodies consistent with the Python native bridge, including sorted reviewed references and Unicode escaping in hashes. Pending write receipts remain pending; no tool executes arbitrary commands.

Every HTTP request requires a current sealed native **worker** credential in Bearer authorization. Browser cookies, owner tokens and listener grants cannot enable worker tools. Verify identity against the actual current source before protocol handling and retain existing per-operation authorization. Never share a principal/server instance between requests. An expiry/revocation/source failure after discovery must fail the later call, not return an empty work set.

`UNBLOCK_MCP_ORIGIN` explicitly enables the endpoint at `/mcp` for one canonical HTTPS origin (or explicit loopback HTTP development origin). Reject another request origin/Host and any supplied browser Origin that differs from the configured origin. Do not trust a caller-selected source, account, executable or destination. With no configured origin return503 without changing web sign-in or the existing API. Limit POST bodies to65536 bytes, including streamed/chunked bodies. Reject other methods; no sessions, SSE subscriptions or webhook capability is advertised.

Return native operation objects as structured MCP tool output plus text. Sanitize failures and preserve rejected-versus-uncertain write guidance: a post-ingestion exception never authorizes a fresh intent or effect retry. Validate UUID references, reviewed parent revisions and argument shapes; retain the native service’s scope and complete-answer checks. Do not impose a new answer-count cap.

## Files and boundaries

`web/src/lib/server/unblock-mcp.js` owns schemas, mappings and HTTP guard/SDK lifecycle; `web/src/routes/mcp/+server.js` wires existing private configuration/service. Keep template auth routes/components unchanged. Extract only the existing test fixture into `web/tests/helpers/native-fixture.js` so native API and actual SDK-client tests exercise the same real authority/projection implementation. Pin server/client/Zod dependencies in the lockfile; the client is test-only. Bump development exports/native MCP to0.4.0 consistently.

## Acceptance

Real SDK Client discovery/calls over handler.fetch cover seven tools, pending/readback, revision, human answer, action/settlement and progress/replacement. Negative checks cover anonymous/cookie/owner/listener/expired/revoked/neighbor credentials, changed principal between requests, malformed/oversized input, Host/Origin and source failure. A Python-oracle hash fixture checks cross-runtime retry intent parity including Unicode. Run complete relevant suites/check/build and both package validations.

Deploy through the saved project and same Fulcra harness. A dedicated synthetic need goes through the actual HTTP client, owner dashboard answer, a replacement HTTP client, private marker readback and authenticated progress. Revoke its grant and confirm a later call fails. Preserve failed attempts and exact source/main readback. Fresh whole-branch review gets one fix pass.

## Release limits

No fake OAuth metadata or plugin connection is declared. Existing grants are bounded and an explicit owner operator remains the renewal route. Actual ChatGPT OAuth/resource discovery, event subscription/delivery, persistent host startup, official publisher/package acceptance and second-account deployment remain separately tracked. This endpoint can be tested with a native grant before those outcomes; it is not submission-ready authentication by itself.
