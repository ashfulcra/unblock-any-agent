# Fulcra native pilot

The first hosted needs/answer/continuity slice uses the official Fulcra sign-in and native annotation persistence. No new OAuth client or external database is required. This is a single-owner pilot; an explicit trusted renewal operator has passed bounded live checks. Persistent startup, marketplace installation, other host pickup routes and a second account’s clean fork remain separate acceptance checks.

## Connect an agent

Sign in to your dashboard, expand **Connect an agent**, and enroll its stable ID, display name and environment, using the Agent worker role. Save the displayed credential in that agent's private credential storage. It is encrypted and scoped by the server to that agent. Do not give the agent your browser cookie or Fulcra access token. Enrollment is pending until its record appears in the dashboard. The owner UI prepares a fixed expiry and retains the same enrollment intent across uncertain/pending retries. Direct owner integrations first GET `prepare_enrollment`, then POST `enroll` with that fixed `expires_at`, identity and stable intent; requested expiry cannot exceed the upstream session or one hour.

A pilot credential expires with the originating Fulcra access token, within one hour. Sign in and enroll again when it expires. No refresh token is stored or embedded in these grants. A separately configured [trusted owner operator](native-renewal.md) can renew the same existing scopes using the existing CLI login; this is an explicit opt-in workflow, not automatic installation or perpetual-authentication coverage. A replacement session can use an unexpired credential for the same agent; enrolling another ID creates another agent. Revoke an enrollment in the dashboard; native processing is asynchronous, so revocation is confirmed only after readback. Rotating the server sealing key invalidates all outstanding credentials and makes old signed pilot records unavailable unless the key is retained; keep it private and backed up.

## Agent HTTP contract

The pilot endpoint is `/api/unblock/<operation>` on your saved dashboard origin. Agent requests use `Authorization: Bearer <private credential>`. Keep secrets out of shell arguments/logs; use your runtime's secret-capable HTTP client or a private request configuration. Owner browser operations use the supplied HTTP-only session cookie and same-origin JSON requests. An enrolled agent cannot answer as a human or enroll another agent.

| Operation | Method and input |
| --- | --- |
| `identity` | GET; returns the verified role, stable ID, environment and permitted agent IDs. |
| `enrollment` | GET; an authenticated worker/listener can read its own verified grant ID, role/scope and actual expiry, without exposing a token. Existing `identity` shape stays unchanged. |
| `attention` | GET; returns all of this agent's current requests, retained context, answers, progress and uncertain actions. A source failure is an error, never a quiet result. |
| `recover` | GET with `request_id`; permits only this agent's request. |
| `request` | POST JSON: stable `intent_id`, `need_key`, `need`, `context`, `recommendation`, `next_action`, `parents: []`. Identity comes from the credential. Same agent/need key converges across sessions. |
| `request` update | Same key and full corrected context, a new intent, and `parents` containing the revision IDs superseded. Concurrent incompatible versions remain visible. |
| `progress` | POST JSON: `intent_id`, `request_id`, current `revision`, complete current `answers` ID array, `stage` (`acknowledged`, `resumed`, `completed`) and observed `evidence`. Multiple answers also require `reconciled: true`; the agent must actually reconcile them before reporting it. |
| `action` | POST JSON: `intent_id`, `request_id`, intended `effect`, before an external action. Does not execute it. |
| `settle` | POST JSON: `intent_id`, `request_id`, `action` record ID and actual observed `evidence`. Check the real result before repeating an uncertain action. |

Errors explicitly distinguish `outcome: rejected` before ingestion from `outcome: uncertain` after an attempted write. Keep the original intent after any uncertain attempt, even when a later retry is rejected. An already-recorded identical progress retry succeeds as historical evidence without resolving newer work.

Mutation results include the physical `record_id`, logical `request_id` where relevant, and `visibility`: `pending` means accepted for ingestion, not persisted, delivered or acted upon. Read attention/recovery until the exact event appears. Retry an uncertain publication with identical fields and intent; do not invent a new intent just because readback is delayed. A changed payload is retained as a separate physical record. An answer names the immutable question revision shown to the human. Old or conflicting answers remain history rather than silently resolving a newer question.

The human view distinguishes needs, answers awaiting pickup and observed continuation. A stored answer never claims that a worker ran. Configure and verify a [listener](listener-setup.md) before advertising automatic pickup; the native listener now has a tested restricted Claude route. Its scoped `delivery` records report only `queued`, `failed`, `blocked` or `unknown`, with evidence; they cannot assert acknowledgment or progress. Historical delivery observations remain retained, and only observations matching the current question and full answer set appear on the current card.

## Native CLI, MCP and pickup

The [shared skill setup](../skills/unblock/references/setup.md) contains native profile, CLI, MCP and listener commands. `transport: fulcra-native` selects the hosted protocol; do not send that profile to the separate loopback CLI. Both copied development exports have run their real manifest commands against native persistence with seven tools. The initiating process closed before the delayed owner answer, and a separate environment listener routed it into a dedicated restricted Claude session. That session recovered current context, declared/read back an intent, wrote/read a private synthetic blue marker, settled it and reported authenticated `resumed`. A replacement verified the same file with unchanged hash, modification time and action count. This proves the bounded route, not arbitrary sessions or marketplace installation.

A listener uses its own enrollment role, environment and explicit permitted agent IDs. Worker progress/actions still require separate worker credentials. Start it before advertising coverage. Shared private dispatch claims prevent overlapping workers; an interrupted expired claim requires evidence-backed operator reconciliation. Three attempts without fresh continuation become a route gap. Acknowledgment alone does not resolve the obligation. Credential expiry/revocation or failed source checks retain last known pending work.

## Fork configuration

Follow [personal dashboard setup](personal-dashboard.md) and `web/README.md`. Keep `UNBLOCK_ANNOTATION_ID` (a dedicated product annotation), `UNBLOCK_AGENT_KEY` (32 random bytes in hex) and `OWNER_USER_ID` in private server configuration. Reuse the existing harness annotation and deploy project; do not mix product events into the harness. The server validates account identity through Fulcra before accepting a human session or using an agent's sealed upstream access token. Product records are MAC-verified; unknown or corrupt records fail closed. This pilot reads complete retained history rather than using a rolling time window that could forget unanswered requests.

Native persistence is eventually visible. The protocol retains conflicts and avoids overwriting history; it does not claim transactional isolation or universal exactly-once external actions. Server key custody, session-bound expiry and asynchronous revocation are deliberate pilot limits to evaluate before public plugin release.

The optional [native HTTP MCP endpoint](native-http-mcp.md) serves the same seven worker tools for MCP clients using existing narrow grants. Its protocol transport is distinct from an OAuth-connected ChatGPT plugin or event-driven host pickup.
