# Review resolution and the next build

2026-10-16. Proposed decisions for review, following the Fable report and confirmed listener baseline. This is a design brief, not an executable implementation plan or a claim that the integrations work.

## Recommendation

Build one application service that enforces identity and workspace permissions for all four entry points. Use Fulcra for connected account data, useful continuity context and artifacts. Keep operational authorization, subscriptions and concurrent request changes behind the application service, with a durable transactional store. Do not force a backend choice around the old Coord implementation or around the initial template's cookie-based proxy.

The alternatives are a strictly owner-account Fulcra record model with cross-account response sharing, or host-native coordination joined by a shared view. The first makes future multi-human writes and revocation harder; the second leaves cross-host recovery and consistent permissions unresolved. The application-service approach introduces hosting and storage to operate, but gives one place to enforce the contracts the review identified. This is a fresh recommendation, not a verified need for a particular database vendor.

Forked personal dashboards can use the same service with each visitor's own authenticated identity and workspace. A full private backend deployment can be a separate advanced path; do not require each dashboard fork to provision an OAuth authorization server merely to render its owner's work. The canonical marketplace plugins retain a stable service endpoint. Confirm this deployment distinction in the written specification before implementation.

## Decisions that close the main design gaps

| Concern | Proposed decision | Proof still required |
| --- | --- | --- |
| F1: independent monitoring and credential custody | A separate listener or scheduled task in the agent's environment checks incoming work and declared due items. Its scoped application credential lives in that runtime's supported secret storage. It does not depend on a browser cookie or the blocked worker staying active. | One unattended due-item check, credential refresh/revocation, local dispatch and restart recovery. Native event delivery supplements this route for sources it covers. |
| F2: MCP authorization server | Give Unblock an explicit OAuth gateway/resource boundary backed by Fulcra sign-in. Evaluate the existing Fulcra MCP authorization-provider pattern using maintained MCP libraries; do not forward upstream bearer tokens to clients or assume they authorize the Unblock resource. | Protected-resource discovery, PKCE, supported client registration, resource binding, token validation, renewal/revocation, distinct-user isolation and actual Claude/ChatGPT connection. Provider registration or a missing supported library feature is a named prerequisite, not hidden application glue. |
| F3: authenticated agents | The signed-in owner enrolls an agent and issues a separate scoped, revocable application credential. Bind it to the stable agent and permitted workspaces; register runtime destinations separately. A worker's name in a payload is never its proof of identity. | Agent A cannot impersonate B, read B's restricted context or exceed its grant. A replacement route preserves identity only through authorized enrollment/rebinding. The shared listener receives explicit read/dispatch grants. |
| F4: second-human response writes | The application service owns operational request/response state. Each human authenticates independently and writes through workspace authorization. Responses are attributed to the actual human even when artifacts are held in another account. Fulcra read-only shares do not become write permission. | Two-human integration test, concurrent answers, membership removal and artifact access. Broad team administration remains later scope. |

Product-issued agent credentials are for the native/local integration, not a replacement for end-user OAuth in marketplace MCP connections. Hosts that cannot present a distinct agent credential must use an explicit enrollment/binding flow or report account-level identity honestly; do not infer an agent from a client name.

The operational store must support unique logical request keys, retained response revisions, grant revocation, durable subscription ownership and concurrent updates. Compare its smallest deployable implementation after the authorization proof. A serverless deployment cannot silently rely on a local ephemeral file. Fulcra continues to provide the selected portable context and artifact functions; the service must document what lives where and how the owner exports or removes it.

## Current source check

The Svelte template at `613a3d817df7933e73b6fb9cbda86fd7377b8e6b` supplies device-flow sign-in, HTTP-only cookies and API proxying. That does not establish OAuth authorization for this product's MCP endpoint. [Template source](https://github.com/fulcradynamics/app-template-svelte/tree/613a3d817df7933e73b6fb9cbda86fd7377b8e6b).

Fulcra's MCP server at `bb928b120901330c155e98e0beb1de973f4f52b9` already has an OAuth provider that maps issued MCP tokens to upstream Fulcra credential grants, including persistence, refresh and revocation code. It is an existing implementation to evaluate, not a reason to build authentication from scratch. This inspection does not establish compliance with every current resource-binding or MCP Events requirement. [Provider source](https://github.com/fulcradynamics/fulcra-context-mcp/blob/bb928b120901330c155e98e0beb1de973f4f52b9/fulcra_mcp/provider.py).

OpenAI requires an OAuth authorization-server/resource-server contract for authenticated MCP and recommends established identity-provider implementations. Its guidance distinguishes those roles and requires server-side token checks. The implementation must pass those checks against the chosen provider rather than relying on successful upstream sign-in. [Official authentication guidance](https://developers.openai.com/plugins/build/auth).

## Remaining review findings

- F5: keep `/unblock` as the desired command and skill. Recommend evaluating `unblock-any-agent` as the permanent package identifier, but preserve `unblock` as the current candidate until actual name validation and a user naming decision. No name is reserved.
- F6/F8/F13/F14: ship the shared remote MCP in both platform exports; include the separate Claude connector submission. Use Code-only native capabilities only on supported Code hosts. Test continuity on a surface without lifecycle hooks. A trigger receipt is delivery evidence; the agent's progress report proves continuation.
- F7: before a consequential action, retain enough action identity and intended effect to check an interrupted attempt. Use the target's idempotency facility when available. An unqueryable, non-idempotent uncertain action stays uncertain and needs reconciliation; do not claim universal exactly-once behavior or prescribe a legacy journal.
- F9: responses name the immutable server-issued request/context revision they answered. Preserve stale answers without applying them silently.
- F10: test source freshness using real watched items; a failed or unverified discovery result cannot establish that work is quiet. Reproduce old failure reports before treating them as current limitations.
- F11/F12: verify exact dated directory metadata/reviewer requirements, add the public policy/support pages, and teach fork deployment with secrets outside the repository. Keep canonical source links in the exports. Public fork versus private template use is an onboarding option.
- F15: reserve a stable logical need key in the application, scoped to agent/work and blocker revision, so a replacement session can discover the same request. Use one atomic create-or-return-existing operation rather than relying on an identifier that only the lost session knew.

The bounded agent-first stall policy remains a proposed default: investigations are visible immediately, and an unreachable agent or expired escalation deadline surfaces the need to the human. No reviewer recommendation becomes a user decision merely by appearing here.

## First build and acceptance order

1. Prove the application authorization boundary with a signed-in human, one enrolled agent, workspace-scoped credentials and actual MCP client linking. Validate the proposed operational persistence contract at the same time.
2. Implement only the shared request/context/answer/progress loop and a minimal human response view. Prove retry, stale-answer and conflicting-response behavior.
3. Connect a Claude worker through the native or environment listener route. Return an answer after the worker becomes idle and observe pickup without a human check prompt. Stop/replace the session and recover its authorized work.
4. Exercise the selected ChatGPT route and the portable listener instructions in a real second runtime. Prove correct destination, access limits and duplicate delivery handling.
5. Demonstrate one independent overdue-item detection with the configured listener, then finish useful four-entry onboarding, personal-dashboard deployment and submission-ready plugin exports.

Start with the smallest proof that can falsify the architecture. Do not build the full dashboard first. Official marketplace submission is a separate release outcome; product proof does not reserve a name or grant publishing access.

Next handoff: review these decisions, incorporate the selected architecture into the written specification, then write the executable implementation plan. Unresolved live provider/client contracts remain explicit implementation acceptance gates rather than claims of existing support.
