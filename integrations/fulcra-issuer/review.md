# Issuer source review and disposition

A fresh read-only whole-branch review covered upstream `8d0d768c07eb41c59ccc15366ba1fbfc51638c85` through candidate `4feff358691d0813c08e18ad98d4dc7bbc7fcab9`, including the implementation plan, changed source, tests and pinned MCP SDK boundaries. The reviewer independently ran all 77 added focused tests successfully and reproduced two Important issues. No Critical or separate Minor issues were identified. Assessment: ready with fixes.

One fix pass, recorded in the manifest's corrected source commit, addressed both:

- **Lost native renewal response:** replacement recovery previously required an already-persisted receipt. It now reconciles the exact frozen native intent using known owner access, revalidates the owned project through the bridge and checks the active root family before publication. It creates no new intent and performs no upstream credential refresh. Tests reproduce lost responses and termination before receipt persistence, then recover the same grant with its remaining expiry. Unknown source receipts stay unresolved.
- **Public-client disconnect:** the pinned SDK required a nullable `client_secret` form field even for registered public clients. The new branch supplies an empty default to that SDK handler. Its registered client authentication and token ownership checks remain in force. Actual HTTP tests cover secretless public DCR/issuance/revocation/later renewal denial, confidential missing/wrong-secret denial, foreign-client isolation and unresolved native readback returning 503 before eventual 200.

Regression evidence: the new failure cases first produced three failures with 27 passes; the corrected focused suite passed 30 tests. The full corrected locked source suite passed 435 tests, with 16 inherited skips, five inherited expected failures and one inherited Starlette warning. A clean checkout applied the patch and matched every resulting file digest, then passed the same full suite. Both Python 3.13.13 and 3.14.7 passed that clean-apply suite; CI reproduces both supported Python versions.

The review also recommended proving native descendant denial rather than relying only on the issuer fixture's revoked set. The existing canonical `web/tests/unblock-api.test.js` ancestry test was run successfully: three generations, scope rejection, descendant identity denial and later renewal denial after ancestor revocation, including an expired parent lease. This is local native-service evidence; real overlapping deployed calls remain unverified.

The review declined to judge actual GCS CAS/IAM/retention, upstream login/callback, second-account ownership, live multi-instance recovery, combined upstream/worker expiry, ChatGPT web discovery/reconnect/revocation/replacement, persistent receivers/MCP Events, shared-service deployment authority, official publisher/license/listing acceptance or namespace availability. These remain acceptance gates. No shared issuer was deployed or enabled, and this source patch does not establish ChatGPT web acceptance.


## Operator tooling follow-up

One fresh whole-branch review covered the operations extension from `cda62ed` through `d5e44b7`. The reviewer ran 63 focused tests successfully and reproduced three Important issues: the prepared report's directory entry was not synced before external effects; replacement acceptance compared agreeing readers without checking exact submitted winner/history; repeated cleanup overwrote the original probe status.

One fix pass added parent-directory synchronization after exclusive creation and atomic replacement, exact complete CAS/claim row comparison against the successful submitted transition, and preservation of the first `prior_status`. Six new regression cases first failed, then passed. The final 35 operator/probe/report cases and full 470-test locked suite passed (16 inherited skips, five expected failures, one warning). The original private source report is retained; this section records the complete actionable disposition. No second fresh review was run for those same findings.

These tools remain operator-only and one-shot. Real GCS/ADC/IAM, actual shared-service login/ChatGPT, automatic namespace discovery and an installed persistent receiver remain unverified. The documented decision is to supply explicit scoped operations first; an authorized operator still must supply record keys and integrate its actual runtime ticks. Runtime flags and public HTTP endpoints are unchanged.

## Returned automated review: completed publication validation

[PR15 review4300369840](https://github.com/ashfulcra/unblock-any-agent/pull/15#discussion_r4300369840) identified one further Important issue: empty completed `checkpoints`/`result` dictionaries were accepted as checked. A separate corrective batch validates required native receipt, refresh token, native intent, timing and result fields, including their derived token-key and expiry references, before either reporting completion or attempting requested cleanup. It emits no raw state or credential data.

Thirty-eight malformed-state regressions first failed. Forty added cases now cover those corruptions with and without requested recovery, the exact empty-dictionary CLI returning nonzero and a structurally valid expired journal remaining checkable. The locked source suite passes 510 tests (16 inherited skips, five expected failures, one warning). This is retained publication structure validation, not a proof of live lease validity, remote backing-object availability or deployment acceptance.
