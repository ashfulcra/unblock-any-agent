# Independent native-loop review — 2026-10-16

Decision: **revise before accepting M2**. The implemented single-owner journey has real production evidence, and the automated checks pass, but three source defects weaken safe replacement and stale-answer handling. This is the independent evaluator's initial review of the working tree against `c81f05d`, before the maintainer's proposed fix pass.

## Scope and method

Read root/web AGENTS.md, the native-loop implementation plan, first-release specification, native pilot guide, changed tracked files and all new web source/tests. Reviewed credential scope, upstream identity validation, event integrity/readback, immutable revision and answer conflicts, continuation, actions, and the human interface. Did not change implementation, V5, deployment, or native records.

Independently ran:

- `npm test`: 9 passed, 0 failed.
- `npm run check`: 0 errors; two existing LoginDeviceFlow event-directive warnings.
- `npm run build`: passed; the same existing warnings and an unused import warning.

These checks validate the covered cases; they do not prove the failures below are absent.

## Findings

### [P1] Preserve settled actions and their evidence in replacement recovery

Location: `web/src/lib/server/unblock-core.js:53-60`; recovery returns this projection in `unblock-api.js:59-61`.

The projection removes a settled action from `uncertain_actions` and returns neither the original action nor its settlement/evidence. `history` contains only request revisions, so there is no other route in either attention or recover to retrieve those records. A replacement therefore cannot distinguish an effect already performed and settled from an effect never attempted, or inspect the result evidence before deciding whether to repeat it. Native storage retaining the records is insufficient when the scoped recovery API discards them.

Independent deterministic adapter reproduction: create request → action → settle with evidence → recover. The recovery has zero uncertain actions, but its serialized payload includes neither the known action record ID nor the settlement evidence. The same omission was independently observed in the actual deployed Alpha recovery payload after the maintainer's synthetic action was settled.

Return retained action and settlement history, including evidence and identities, alongside the current uncertain-action projection. Preserve useful historical progress when revisions or answer sets change as well. Verify replacement recovery can identify the settled effect and result without access to the owner's native bearer token.

### [P2] Make an identical settlement retry converge after readback

Location: `web/src/lib/server/unblock-api.js:108-111`.

Settlement accepts only an entry in `request.uncertain_actions`. Once the original settlement becomes visible, retrying the identical intent/action/evidence fails with `Uncertain action not found`. This occurs precisely when a client loses the response or crashes after ingestion and retries during recovery; it violates the documented identical-intent retry contract.

Independent deterministic adapter reproduction: first settlement returns `visibility: visible`; an identical second call throws `Uncertain action not found`. Validate ownership and existence against all retained action events, then allow identical publication to converge. Retain distinct modified settlement evidence rather than overwriting history. A focused lost-response/visible-retry case is sufficient.

### [P2] Bind answer drafts to the revision the human composed against

Location: `web/src/lib/components/NeedsDashboard.svelte:13,20,43-47`.

Draft text is keyed only by logical request ID. The five-second refresh replaces that request's current revision, while retaining the existing text. At Send answer, the component obtains the revision from the newly refreshed row and pairs it with the old draft. A human can compose for revision A, receive revision B during typing, and submit an answer falsely attributed to B. The API then treats it as current; immutable server revisions alone do not prevent this path.

Bind draft text to its initial displayed revision, or explicitly invalidate/reconfirm it when that revision changes. Retain an A-bound submission as historical rather than silently promoting it to B. Test the bounded sequence A → begin draft → refresh to B → submit. This finding is source-derived; no writes or browser state manipulations were performed by this evaluator.

## Positive evidence and boundaries

The server seals credentials with AES-256-GCM and keeps the upstream access token inside the encrypted short-lived grant; no refresh-token storage was added. Agent identity comes from the opened grant, enrollment/revocation is read before authorization, and every request validates the upstream account against the configured pilot owner. Owner-only operations and neighboring-request checks are present. Signed native rows and deterministic physical IDs support exact readback and retain semantic variants. Tests exercise pending visibility, account denial, agent scope, revocation, conflicting answers, stale progress and uncertain actions. The template authentication/device-flow files were not changed.

The maintainer supplied private `native-recovery-evidence.json`, which this evaluator read: a fresh replacement Python subprocess recovered context and the human answer, wrote/read a disposable blue marker with SHA256 `a0bee6616b5e5eae6799cb4525a884a82e7161614f11122bbdf4383b2ac05998`, recorded/read back action intent, settled with evidence, and reported observed continuation.

This evaluator separately made only GET requests to the actual deployment, using the Alpha credential in memory: `attention` returned HTTP 200, `source: checked`, one Alpha request in `resumed`, one answer, one progress and zero uncertain actions; scoped `recover` returned HTTP 200 for the same request and state. Neither response exposed action/settlement history. No credential, full user information, .env or private binding was printed or saved in this report.

Human UI evidence is **maintainer-observed**, not an independent browser observation: CUA rendered actual production through a bounded localhost QA proxy that injected the authenticated CLI cookie server-side and restricted answer POSTs to the disposable pilot request. The maintainer observed the question/context, sent the answer, then observed resumed state plus the actual continuation evidence/hash. This tests production rendering and the answer path through that proxy; it does not establish interactive device-flow sign-in or direct-origin browser-cookie behavior. The unchanged template auth path and direct-origin API checks are separate evidence. The maintainer also reported a stale generic “checking native persistence” notice after the card showed resumed; derive or clear that notice when exact readback is observed.

## Acceptance follow-up

Fix the three findings, run the targeted regression checks and normal test/check/build, and read back the deployed result. Preserve the real journey evidence and add actual permission-negative outcomes before closing M2. This review does not certify automatic host pickup, unattended renewal, installed Claude/ChatGPT plugins, a second account, public distribution, or clean-fork deployment.

The evaluator was assigned no V5 identity/binding and was explicitly restricted from V5/record mutations; the maintainer retains its own registered work and exit-check obligations.


## Maintainer fix-pass resolution and deployed checks

The initial report above is preserved. All three findings were reproduced with failing tests and corrected in one pass: recovery returns all actions/settlements and historical progress; settlement retries validate retained action identity and converge; drafts capture the first-edited question revision and require explicit review when it changes. Eleven tests pass and type checking reports zero errors/two inherited warnings. The corrected source was redeployed through the same saved Fulcra project.

Parent direct production checks read retained action+settlement evidence and historical progress, then retried the original settlement: HTTP 200 and the identical record ID. Beta attention showed zero Alpha requests; Beta recovery of Alpha and human-answer attempts returned 400; anonymous attention returned 401. Revocation was initially misclassified as a source error; ordering the authentication classification fixed it, and a revoked Beta credential then returned 401. No valid second human account was tested.

Parent CUA using the bounded authenticated production QA proxy composed a draft for revision A, updated context through the real agent API to B, and observed the new question plus retained old draft, an explicit changed-question warning, and disabled Send answer. Clicking the explicit review control and composing a fresh answer allowed submission; readback then appeared. A second fresh subprocess recovered the corrected context, new answer, historical answer/progress and settled action evidence, verified the existing marker hash without repeating the action, and reported completed. The deployed UI displayed completed, the exact current answer, the historical-answer count and the observed continuation evidence. The generic pending notice also changed after readback. Browser/proxy and interactive sign-in limitations above still apply; no screenshot is claimed.

This resolves the initial findings for the bounded M2 pilot. It does not certify automatic host pickup, unattended credential renewal, a second account, marketplace installation/publication or full release acceptance.

## Returned PR review follow-up (M2-1)

Greptile subsequently returned three additional findings on [PR #2](https://github.com/ashfulcra/unblock-any-agent/pull/2): [rejected editor lock](https://github.com/ashfulcra/unblock-any-agent/pull/2#discussion_r4297164581), [enrollment retry expiry](https://github.com/ashfulcra/unblock-any-agent/pull/2#discussion_r4297164588), and [historical progress retry](https://github.com/ashfulcra/unblock-any-agent/pull/2#discussion_r4297164597). Each was checked against source and reproduced by a failing regression before its fix. Listener integration was preserved in a named local stash while this follow-up ran through the existing harness.

The UI checks the 16,000-character answer limit before entering pending state. Explicit server outcomes distinguish a rejection before ingestion from an uncertain attempted publication. A first definite rejection restores editing; any prior uncertain attempt retains the same pending intent until exact readback. Late HTTP results cannot recreate a pending answer already cleared by polling. Owner enrollment prepares a fixed bounded expiry and retains its intent across pending retries; identical pending/visible retries now share one record/expiry. Grant rows use immutable record IDs for rendering. An exact already-recorded progress event is recognized before current-snapshot validation; it remains historical and cannot satisfy a newer question or answer set.

Fifteen web tests pass. Direct deployed checks verified same enrollment record/expiry before and after readback, one grant row per intent, a historical progress retry returning 200 with the same ID, new stale progress rejection, overlong-answer rejection before ingestion, and unchanged current completed state. Source tests also cover a lost readback after ingestion retaining an uncertain outcome.

Maintainer CUA used a bounded production QA proxy for the disposable synthetic request. For one request it supplied a deliberately wrong Origin, causing the real deployed route to reject before ingestion; this made the existing protection stricter for that test and changed no production auth code. The browser displayed the rejection while keeping the draft, textarea and Send editable. Reload restored the editable draft. Editing and submitting normally then reached pending/native readback. Two current answers remained visible as answer_conflict until an authorized worker explicitly reconciled both, verified the existing settled marker without repeating its action, and reported completed. The browser/proxy/interactive-sign-in limitations stated above remain in effect.

The maintainer also exercised the actual owner enrollment form through a proxy restricted to one disposable agent ID: prepared expiry, submitted enrollment, observed the real enrolled row, verified that the displayed credential had the sealed format without printing it, then hid it before DOM readback. The disposable grant was revoked afterward through the actual owner API. The enrollment notice now updates when readback appears.
