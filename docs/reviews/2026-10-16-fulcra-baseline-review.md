# Independent M1 review — Fulcra hosted baseline

Reviewer: independent Evaluator (`evaluate_fulcra_baseline`). Date: 2026-10-16.

Verdict: **PASS — M1 evaluation gate**. Independent source, local/production API and build/check results are combined with the parent’s retained deployed browser observations below. Coordinator/Nurse closure still requires writing and reading back REVIEW completed and terminal events, refreshing the overview, and confirming the completed result in the dashboard; this report does not claim those future actions already happened.

## Tested targets and authority

- Source: `web/` in `ashfulcra/unblock-any-agent`, reviewed against the official cached Svelte template commit `613a3d817df7933e73b6fb9cbda86fd7377b8e6b` and the current Fulcra web-app skill/reference components.
- Local live app: `http://127.0.0.1:6173`.
- Production live app: `https://unblock-any-agent.my.fulcra.ai` (parent confirmed successful deployment at this returned domain).
- M1 spec: the current private Fulcra workspace cache; required baseline, preserved auth, owner-only populated harness, live API/UI evidence, access denials, and build/check. This report does not claim M2 needs/responses or M3 host pickup are complete.
- Run: `ebf9e98f-faed-4f8a-85b5-18017ac305a7`.
- Annotation: retained in the private Fulcra workspace (binding omitted from public copy).

Read repository and web AGENTS instructions, `docs/live-integration.md`, workspace plan/spec/decisions/progress/issues, Fulcra web-app skill, harness-control-flow and dashboard acceptance instructions.

## Source review

The official template supplies the public Auth0 client and Fulcra API configuration. There is no newly registered OAuth client or custom database prerequisite for this baseline. The selected app uses the template device-flow routes, HTTP-only cookie/session path and authenticated Fulcra backend proxy.

`api/auth/token`, `revoke`, `check`, `device/code` and `device/token` are byte-identical to the cached official template. `api/auth/user` differs only by an Error type cast. `auth0-device-flow.js`, `user.js` and `api-client.js` add type annotations and equivalent explicit defaults; `JSON.parse(null)` becomes `JSON.parse('null')`. The initial auth client becomes a typed variable before initialization; the normal initialization order remains unchanged. LoginDeviceFlow differs in app branding/placeholder visibility and typing; its click handlers, synchronous popup opening and polling flow remain intact.

OwnerNav and the server owner check are byte-identical to the supplied skill references. Harness API and dashboard changes from those references are typing-only. Owner identity stays in server-only configuration. All three harness data routes check for a cookie and owner claim before querying Fulcra. Browser components obtain owner status through the backend and request runs/files through backend endpoints. Markdown is rendered through DOMPurify. No hardcoded demonstration events were found.

## Independently executed checks

Python standard-library HTTP requests captured `fulcra-api auth print-access-token` into memory and supplied it only as the `fulcra_access_token` cookie to the two app origins. For the negative owner check, only a copy of the userid claim was changed. No credential, cookie, full user record, private environment value or deployment binding was retained in this report.

At 16:26:20Z locally and 16:26:47Z in production, the observed matrix was:

| Request identity | owner endpoint | runs | overview | issues |
| --- | --- | --- | --- | --- |
| Anonymous | 200, isOwner false | 401 | 401 | 401 |
| Altered non-owner claim | 200, isOwner false | 403 | 403 | 403 |
| Authenticated owner | 200, isOwner true | 200 | 200 | 200 |

`api/auth/check` returned authenticated false without a cookie and true for the owner on both origins. `api/user/info` returned 401 anonymously and valid JSON with 200 for the owner; private response contents were discarded.

Local runs returned four actual M1 events. Production runs returned six: RUN_START started, FIND_MILESTONE completed, GENERATE started twice, GENERATE completed, and REVIEW started. All matched this run and had parseable JSON string notes with nonempty evidence. In particular production returned REVIEW detail “Evaluate the actual Fulcra-hosted baseline and owner harness”. This independently correlates the newly recorded evaluation event with the live backend.

Production overview and outstanding-issues text were nonempty and matched their workspace cache files byte-for-byte. SHA-256 values were `0e86f3b51e7af2e42b163cd375cdbfb33a9bfa1a50ca25209583003167582ad7` and `23e13e9300287db3f60f92b189500e3aafe74b4fb7b22aeb2c8750022ce3da22`, respectively.

Independent commands in `web/`:

- `npm run check`: exit 0; 0 errors and 2 inherited `on:click` deprecation warnings in LoginDeviceFlow.
- `npm run build`: exit 0; generated client and server output. The generic adapter-auto local environment notice is not proof of deployment; production API checks above independently establish the live target.

One first HTTP evidence script stopped when it attempted to JSON-parse an anonymous denial body. The corrected script handled status before decoding and completed the full matrix; this was an evaluator script error, not an app failure.

## Findings and remaining evidence

No blocking source or API finding was identified for the tested M1 behavior. The owner check follows the supplied reference: it reads an unverified JWT claim while Fulcra validates the forwarded credential for data reads. The altered-claim test verifies the documented owner gate, not a separate account enrollment workflow or a broader authentication security audit.

The parent supplied browser observations retained at private `web-baseline/browser-evidence.json`, timestamped 16:29:24Z. I read that sanitized evidence and received the parent’s explicit action/results report. The parent used Cua against an ephemeral read-only loopback QA proxy to the actual deployed app; the proxy injected the current CLI credential server-side. No production source/auth change was made. This verifies deployed content and the authenticated UI, while direct-origin API checks above separately verify production backend behavior. It is not a claim of direct-origin browser cookie behavior or a completed interactive consent flow; no screenshot evidence is claimed.

The observed owner UI initialized to “Connected to Fulcra.” with global Home/Harness Dashboard navigation and Owner label. The parent clicked Harness Dashboard and observed `/harness` with this run’s exact ID, in-progress status, GENERATE completed, REVIEW started, the visible nonempty REVIEW evidence, overview “Unblock web baseline”, and Outstanding Issues. Fork/source links remained canonical. The alternate token-copy browser view had zero owner navigation and zero Harness Dashboard headings; the direct production API denial matrix independently establishes data denial.

The parent’s direct production device-flow startup POST returned 200 with a verification URI using the supplied client. The parent reported successful CLI write/readback of the real REVIEW progress event. Its exact detail was “Live baseline API and owner navigation verified; checking event rendering”; the browser displayed that event and its evidence. At 16:29:46Z I independently GET-read the production runs endpoint again and verified this same progress event’s run ID, REVIEW step, started status, detail and nonempty evidence. Thus this review includes a real recorded event correlated across CLI readback, deployed backend and rendered dashboard, not merely a build or publication receipt.

No M1 blocking finding remains in the tested acceptance scope. Final post-review and terminal event display belongs to the Coordinator/Nurse closure gate and must be read back after it happens.

Interactive owner sign-in confirmation remains nonblocking under the Fulcra skill and is already recorded in outstanding issues.

## Declined scope

No source edits, V5 operations, host/plugin installations, model invocations, deployments, account mutations, new OAuth registrations or database provisioning were performed. No annotation writes were performed by this evaluator; the parent operates recording and supplies that write/readback evidence. The review does not certify real owner interactive consent, clean-account host pickup, remote MCP authorization, marketplace acceptance, M2 persistence guarantees, or M3 packaging/integration. A passing M1 must not be represented as completion of those later milestones.

Public-copy note: the exact annotation binding was removed before source publication; the original reviewer report is retained privately. Coordinator subsequently wrote/read back REVIEW completed, MARK_COMPLETE and RUN_COMPLETE, then observed the completed run and M1-complete overview in the deployed owner dashboard.
