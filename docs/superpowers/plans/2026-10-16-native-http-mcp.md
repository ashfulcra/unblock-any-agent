# Native HTTP MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Serve the native worker contract over an authenticated HTTP MCP boundary in the existing app.

**Architecture:** Official SDK per-request factories call the existing native service; explicit canonical origin and narrow worker credentials guard the boundary. Existing sign-in/persistence/renewal stay intact.

**Tech Stack:** SvelteKit, pinned @modelcontextprotocol/server2.3.1/client2.3.1, Zod4.

**Spec:** ../specs/2026-10-16-native-http-mcp.md

## Global Constraints

- No new registered OAuth client, custom authorization service or external database for this transport slice.
- Seven existing tools and authority boundaries; no owner cookie/listener worker access or incoming executable/source selection.
- Per-request actual source authorization;65536-byte POST limit, explicit UNBLOCK_MCP_ORIGIN and strict Origin/Host checks.
- Support2026-07-28 and legacy stateless via official SDK; advertise no event subscription or installed-host claim.
- Existing Fulcra app harness/saved deployment; no template auth changes; retain uncertain writes and exact readback.

## Review Focus

- Reusing a transport with another credential must never reuse the prior principal.
- Revocation/source loss between discovery and mutation must stop effects and preserve pending guidance.
- Lost response after ingestion must retain the same deterministic retry intent across Python/HTTP, including Unicode.
- Streamed oversized bodies and unexpected Host/Origin must be denied before dispatch.
- SDK shutdown must not retain a request credential or close a response before it is consumed.

### Task 1: SDK boundary and worker tool parity

**Files:** Create web/src/lib/server/unblock-mcp.js, web/tests/unblock-mcp.test.js, web/tests/helpers/native-fixture.js; modify web/tests/unblock-api.test.js and dependency lock/package files.
**Interfaces:** createNativeMcp({service,origin}) returns {fetch(request):Promise<Response>,close():Promise<void>}; service.handle(operation,{token,body}) is the existing authority. Fresh SDK factory per request; token captured only for that request. Canonical intent serialization matches native_mcp.intent. No source/auth input is accepted by tools.

- [x] Write actual SDK-client failing tests for discovery/seven-tool loop, replacement, native pending/readback, exact intent parity, no extra identity arguments, role/expiry/revocation/neighbor/source failures and HTTP guards/body limit. Extract the unchanged existing fixture; run RED.
- [x] Pin SDK/client2.3.1 and a compatible exact Zod4 version, implement mappings/guards/transport with the official handler, then run GREEN web tests and check. Expected all existing21 and new transport tests pass; check0errors/2inheritedwarnings.
- [x] Commit the independently testable adapter after comparing actual results with every acceptance class.

### Task 2: App mount and live protocol loop

**Files:** Create web/src/routes/mcp/+server.js, docs/native-http-mcp.md; modify web/.env.example, native/package version declarations and setup docs/tests. Keep private proof fixtures outside source.
**Interfaces:** /mcp wires createService from existing server config plus UNBLOCK_MCP_ORIGIN; optional missing origin returns503. All methods use one guarded handler; only POST dispatches. Version0.4.0 in server/export/native MCP and package expectations.

- [ ] Wire route/config/version/docs; run full Python/web/check/build and package checks. Expected preserved baseline plus seven-tool MCP HTTP behavior; private bindings absent from source/exports.
- [ ] Continue the bounded M2-2 harness started before Task1, deploy and exercise actual SDK discovery/request, close initial client, answer in deployed dashboard, recover in replacement, declare/read back action, write/read private synthetic marker, settle/report observed progress and complete. Verify revoked later call denied. No external effect or marketplace claim.
- [ ] Fresh whole-branch review with focus above, one RED-to-GREEN fix pass and full required checks; source scan/PR/CI/readback/main integration, own V5 fold and harness evidence. Full M3 remains incomplete.

Self-review: each focus maps to Task1 protocol tests; actual route/deploy/replacement behavior is Task2. Operator modules remain excluded from worker exports. Ash’s standing autonomous execution supplies inline execution; preserve decisions in the private plan ledger and continue without repeating permission menus.
