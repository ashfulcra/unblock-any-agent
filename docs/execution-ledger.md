# Execution ledger

2026-10-16: Ash requested an exit check every turn and continuous safe execution. The maintainer’s private exit check now includes addressed replies as well as V5 work. Four regression checks passed. The live authorized exit read also passed: owned work remained active, addressed replies were checked, and the prior Tycho review had an evidence-backed resolution. This is bounded identity-specific coverage, not a fleet-wide all-clear.

Decision: proceed inline in the clean checkout on a local feature branch. No other agent is editing this repository; avoid unnecessary worktree setup. Shared backend is a provisional choice, not a user preference. Local SQLite and owner bootstrap auth are limited to the loopback proof, not a claim of production or marketplace readiness.

Plan: [first local loop](superpowers/plans/2026-10-16-first-local-loop.md). Spec: [first release](superpowers/specs/2026-10-16-unblock-first-release.md).

Task 1 complete: 10 durable-core tests failed for the missing store, then passed against the implementation. Verified account/agent isolation, environment listener scope, credential revocation, concurrent request convergence, retry conflicts, stale answers, retained conflicting answers, replacement recovery and uncertain-action reconciliation. Local store has no V5 dependency.

Task 2 complete: real loopback HTTP tests cover authentication, revoked credentials, identity isolation, Host/Origin checks, bounded JSON, owner cookie/logout and private-path rejection. The response UI renders pending answers and observed recent progress separately.

Task 3 local route complete: real subprocess workers prove delayed pickup, wrong-agent/environment isolation, failed-route replacement, queued-without-ack behavior and restart recovery. A resource-leak regression failed, then passed after explicitly closing listener database connections. Full suite: 23 passed. These are synthetic worker tests, not yet evidence of native Claude or ChatGPT pickup.

Independent-process smoke passed: listener started before the synthetic human answer; worker acknowledged, wrote one local decision artifact, and reported resumed without a check prompt. Suite: 25 passed. Browser QA verified synthetic sign-in, answer submission and waiting-for-pickup display. Native Claude attempts remain under investigation; initial heredoc permission failure prompted a safer UUID-only command adapter. No bypass flag is used.

Native Claude independent-process smoke passed after replacing the ambiguous heredoc with a single UUID-only CLI command. Claude Code 2.1.301, normal permission checks, safe/restricted modes, explicit fresh synthetic session, three-turn and USD 0.50 bounds. A separate listener process existed before the answer; it dispatched, and the actual worker reported acknowledged then resumed with recovered context. This proves the local restricted-session route, not a marketplace plugin or arbitrary desktop session wake.

Fresh independent review: [raw report](reviews/2026-10-16-local-loop-review.md). Six Important findings were reproduced with failing regressions, then fixed in one pass:

| Finding | Resolution |
| --- | --- |
| Late old-answer progress hides a newer answer | Transactional answer-set revision check; multiple answers require an explicitly reviewed snapshot. |
| Uncertain actions disappear after resumed | Attention includes uncertain actions independently of request status; dashboard shows the outstanding verification. |
| Replacement cannot discover open requests | Agent attention includes its unanswered obligations; listeners still dispatch only current answers. |
| Retry launches overlapping workers | Exclusive request-level execution claims, conservative crash recovery with retained evidence, and stale-completion protection. Shared ledger required. |
| Settlement never releases blocked pickup | Action reconciliation changes the delivery key and permits a fresh attempt. |
| Partial artifact falsely proves continuation | Atomic no-overwrite publication and validation against the current work before resumed progress. |

Additional checks cover active/expired claim recovery, stale completion against a replacement claim, atomic credential publication, and direct loopback transport without environment proxies. Verification: 37 tests passed; independent synthetic CLI smoke passed; bounded real Claude smoke passed again after the fixes. Both smoke runs observed authenticated acknowledged → resumed progress and verified recovered context. Browser QA used a disposable synthetic owner; its preview server was stopped afterward.

Review scope judgment: the source review does not certify native permissions, production OAuth/MCP, ChatGPT pickup, hosting, marketplaces or visuals. Separate parent evidence establishes only the narrow local Claude route and synthetic browser flow described above. All production integration and public distribution acceptance remains open.


Local entry-point slice: [implementation plan](superpowers/plans/2026-10-16-local-plugin-entrypoints.md). MCP tests first failed for the absent module; three real stdio integration tests now pass, including replacement-process recovery, authorization/revocation and copied runtime execution outside the checkout. Package test first failed for the missing builder, then passed for both exports. Full suite with MCP SDK: 41 tests passed. Dependency is isolated to the local bridge; core proof remains standard-library only.

The skill baseline could not load an absent entry point. A fresh agent then exercised the completed reference skill against a disposable authorized fixture: recovered current context/answer, wrote and read back the approved marker, retained action evidence, reported acknowledged/resumed/completed and preserved a new unanswered prerequisite. It correctly reported absent listener coverage. Parent independently read back the completed state, marker and remaining obligation. One discovered CLI-reference gap was corrected with the actual declare/settle mapping. Metadata validation passed.

Both development exports passed Claude strict validation and the current portable plugin/MCP schemas. The Claude validator gave nonblocking advice to include a marketplace install line; no unverified marketplace was invented. Official documentation now also exposes an approved-partner OpenAI local-MCP submission route; no eligibility or installed-host claim is made.


Independent entry-point review: [raw report](reviews/2026-10-16-local-entrypoints-review.md), no actionable findings. Reviewer independently ran all 41 tests and checked agent-role rejection, ten foreign-principal operation denials and disconnected-service errors. Parent subsequently exercised both actual manifest launch commands with a clean dependency cache; seven tools and harmless authenticated recovery passed. This closes the package-process evidence gap, while actual host installation, portal eligibility and production integration remain unverified.


Canonical repository created at https://github.com/ashfulcra/unblock-any-agent. Source commit `74bdde04bd6ce2743227a1880ac5aa9b1e7c642e` was read back through GitHub; README, canonical skill, MCP bridge and CI file matched local bytes. [Initial CI](https://github.com/ashfulcra/unblock-any-agent/actions/runs/38909810022) passed on Linux/Python 3.13 and 3.14. Source scan found no excluded state or credential-like values in the 45 source files checked.

Added the requested prominent Create your own dashboard entry to the local web view and [fork/account/deploy/update instructions](personal-dashboard.md), with source and optional stars directed to the canonical repository. Native browser readback confirmed the visible link and exact canonical guide destination. Six HTTP checks passed after the change. Hosted deployment is expressly pending the real service boundary, not inferred from the local page.

Remaining live gates are recorded in [live integration prerequisites](live-integration.md). Production OAuth client/origin and public runtime/durable store configuration are absent from this checkout/environment; they are linked owned prerequisites rather than replaced with invented values or personal tokens. Official host/portal acceptance and clean-account hosted deployment remain open. The maintainer exit check now also reads its private local checkpoint, refuses quiet on missing/mismatched checkpoint data, and notices released prerequisite tasks; seven focused exit-check tests passed.

Local implementation and entry-point work were completed on the maintainer's own V5 fold with verified publication readback and positive applied acceptance. Two linked owned prerequisite tasks retain the exact missing production OAuth registration and public runtime/store setup. Remaining installation, remote web, detection, agent-to-agent help and official release acceptance is not claimed complete. The continuation checkpoint retains these prerequisites and will trigger new work if they are released.


Correction from Ash: the declared new-OAuth-client gate was an implementation mistake. The official Svelte template already supplies the public Fulcra client/device-flow configuration, and the web-app skill includes Fulcra-managed deployment. The earlier custom gateway/store choices do not block the web baseline. Updated the specification and live-integration/fork instructions, initialized the Fulcra web harness workspace, and resumed M1. The prior blocked V5 items will be resolved as withdrawn prerequisites, not falsely recorded as new clients or databases provisioned.


M1 Fulcra baseline complete at https://unblock-any-agent.my.fulcra.ai. The earlier OAuth/custom-runtime prerequisite tasks were withdrawn with accepted V5 readback, not fulfilled by provisioning new infrastructure. Official template authentication remains intact; a saved Fulcra deploy project hosts the app. Independent evaluation found no blocking issues: anonymous/non-owner denials, actual authenticated data, device-flow startup and build/check passed. Browser checks through a read-only QA proxy showed real run evidence and the final completed M1 state. REVIEW, MARK_COMPLETE and RUN_COMPLETE events were written and read back exactly; the dashboard then displayed M1 complete and M2 pending. Interactive owner sign-in confirmation remains nonblocking. Four low inherited cookie advisories remain tracked; compatible updates removed high/moderate findings. See the [raw review](reviews/2026-10-16-fulcra-baseline-review.md). Next: Fulcra-native needs, answers and continuity.
