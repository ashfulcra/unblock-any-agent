# Native HTTP MCP review — 2026-10-16

The existing Fulcra web app now exposes the seven native worker tools over HTTP using the official MCP SDK. Each request verifies its worker enrollment against the current source; owner cookies and listener credentials cannot enable worker tools. The web app retains the official Fulcra webapp sign-in flow without a new registered OAuth client or database.

## Observed behavior

A deployed modern SDK client discovered all seven tools, created a synthetic need and corrected its context, then closed before a dashboard answer. A replacement client recovered that current context and exact answer, retained and read back an action intent, verified one fixed private synthetic marker, settled the action, and reported actual resumed and completed progress. The dashboard showed completion. The dedicated enrollment was revoked and read back; the same later client was denied with HTTP 401.

The first revoked-client probe returned 503. That failed result was retained; an authentication-before-source fix and explicit expiry/revocation regression corrected it, and the same already-revoked profile subsequently returned 401. No substitute identity was used to hide the failure.

## Independent review and fixes

A fresh whole-branch reviewer found zero Critical issues, one Important issue and one Minor issue. Both findings were accepted and fixed in one pass:

1. Network rejection, timeout and malformed upstream JSON were classified as credential failure during preflight, or operation rejection during a later tool call. The upstream boundary now supplies explicit source-error provenance. Six regressions failed before the fix and passed afterwards. These failures retain pending-work guidance; uncertain publication still takes precedence.
2. HTTP UUID validation accepted uppercase references without Python's lowercase normalization. A real native lookup regression failed before the fix and passed after normalization.

The author verified these fixes; no repeat review was requested. Host/Origin restrictions, streamed size limits, strict schemas, per-request principal isolation, expiry/revocation, pending/readback, Unicode retry intent parity and post-ingestion uncertainty are covered by actual SDK-client tests. Modern and legacy stateless clients are exercised; change subscriptions are explicitly disabled.

A separate [returned repository review](https://github.com/ashfulcra/unblock-any-agent/pull/6#discussion_r4298522804) identified an advertised 200-character action key exceeding the native service's 160-character intent limit. A real SDK regression accepted 160 characters and failed because 161 still reached native dispatch. The HTTP schema now uses the shared 160-character key bound; both boundaries pass and an overlong key is rejected before dispatch. This returned finding was picked up without a human reminder.

## Validation and limits

All 37 web tests passed, Svelte check reported zero errors and two inherited template warnings, and the production build passed. The unchanged Python runtime previously passed 78 tests, and version 0.4.0 exports passed strict package and seven-tool launch checks. Worker packages omit owner/operator modules. Credentials and live private bindings remain outside source.

This is a verified native bearer transport and bounded continuity proof. Actual ChatGPT remote authorization, event delivery, official marketplace acceptance, persistent host startup and clean second-account deployment remain separate work. Dashboard interaction used the bounded authenticated QA proxy; a fresh interactive production-origin sign-in and independent reviewer replay were not claimed. Eventual source visibility and reconciliation remain required; universal exactly-once external effects are not claimed. See [transport setup](../native-http-mcp.md).
