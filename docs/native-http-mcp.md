# Native worker MCP over HTTP

The native pilot exposes eight worker tools at `/mcp` through the official MCP SDK. Modern2026-07-28 and legacy stateless clients use the same scoped native service and retained context. The server requires a current sealed worker grant on every request; owner cookies/tokens and listener credentials cannot enable these worker tools.

## Enable the endpoint

Set server-only `UNBLOCK_MCP_ORIGIN` to the exact dashboard origin returned by your saved Fulcra deployment, then rebuild/redeploy that same project. It accepts HTTPS, or explicit loopback HTTP for local development. The existing owner, product annotation and sealing key remain the native configuration. Leave the origin blank for an unavailable `/mcp`; web sign-in and the existing API still work. Settings are loaded for the server process lifetime; redeploy after changing them.

Requests must target that origin with its matching Host. A browser Origin, when supplied, must also match. Only JSON POST requests are supported, bounded to65536 bytes including streamed bodies. No browser CORS expansion or persistent protocol session is configured.

Use an existing private native worker profile from [pilot enrollment](native-pilot.md). Keep its token in your runtime’s private HTTP credential configuration; the source manifest contains no token. For a JavaScript client, use `@modelcontextprotocol/client`2.3.1, `Client` with `versionNegotiation: {mode: 'auto'}`, and `StreamableHTTPClientTransport` pointed to the profile origin plus `/mcp`. Supply the profile’s sealed credential as the Bearer header through transport configuration, never a shell argument or browser URL. Discover tools and call `recover_work` before doing anything else. A response whose source failed cannot establish an empty queue.

The tools match the native stdio bridge: `ask_for_help`, `recover_work`, `get_work`, `revise_need`, `record_progress`, `begin_action`, `reconcile_action` and native-only `record_work_update`. The last declares an expected update without inventing a human question; see [declared-update detection](native-detection.md). UUID references and exact reviewed revisions/answer sets come from the current source. A stable key and identical retry body preserve an uncertain write; pending receipts require exact readback before claiming visibility. Action tools retain intent/evidence and execute no commands.

## Host and release status

This is a native-grant MCP transport, not a completed ChatGPT OAuth connection. It advertises no invented authorization metadata, event subscription or background wake. Actual ChatGPT authorization/resource discovery and MCP Events remain separate integration work; fixed bearer setup alone does not satisfy the public submission portal. The [existing trusted operator](native-renewal.md) remains the optional bounded renewal route. Installing a plugin starts neither that operator nor an environment listener.

See [native pilot](native-pilot.md), [listener setup](listener-setup.md), and [official distribution plan](marketplace-release-plan.md). Keep forks and source/star discovery directed to the [canonical repository](https://github.com/ashfulcra/unblock-any-agent).

## Observed bounded evaluation

The deployed endpoint was exercised with an actual modern SDK client: seven tools were discovered, a synthetic need and corrected context were saved/read back, and that client closed before the owner dashboard answer. A replacement HTTP client recovered the exact current question/approval, declared/read back an action, created and verified one fixed private blue marker, settled it and reported actual continuation/completion. The dashboard showed the resulting resumed/completed evidence. Anonymous, owner/listener, changed-principal, neighbor, expiry/revocation, source loss, request-limit and origin cases also have SDK-client/HTTP tests. This is protocol/client evidence; actual ChatGPT connection and event pickup remain unverified.
