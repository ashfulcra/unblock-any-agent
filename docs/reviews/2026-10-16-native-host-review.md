# Native host pickup review and evidence

Review snapshot: `cb441e94c57125e9692961032c30951022b6ef86`, base `0c54e3c1008ab71a617b048ffe0e4666e6e6c6b9`. Independent fresh-context reviewer: `review_native_host`. Initial verdict: **with fixes**, two Important findings, no Critical or Minor findings. The reviewer independently ran all 57 Python and 18 web tests and inspected the retained live evidence; it did not use account credentials or rerun production operations.

## Findings and maintainer resolution

1. **A failed authorization/source check did not stop the remaining cached dispatch batch.** A two-item fixture began returning 401 after the first launcher, yet both items launched. The listener now revalidates identity and current scoped work before every launch, stops the batch on post-dispatch or receipt-publication source failure, reports the check as unknown and preserves pending IDs plus exact receipt outbox bodies. Regression `test_multi_item_authorization_or_source_loss_stops_the_dispatch_batch` reproduced RED, then passed for 401 and503 at both failure boundaries.
2. **The published native profile could not launch the Claude adapter.** The adapter required local-only `kind`/`id` fields even though native setup specifies only `transport`, `url`, `token`. It now derives native role/addressed identity from authenticated `identity`, retaining the separate local path. Entry-point regression `test_native_entry_point_uses_documented_profile_and_authenticated_identity` reproduced RED, then passed for minimal native profiles, denied listener/neighbor roles and expired authorization. Domain failures stop before Claude launch.

Both Important findings were fixed in one evidence-backed pass. The dependency-complete suite then passed **59 tests**, with **18 web tests** also green. No second reviewer or unverified acceptance claim substitutes for those regressions.

## Actual bounded acceptance

The deployed [native pilot](https://unblock-any-agent.my.fulcra.ai) uses unchanged supplied Fulcra sign-in, native annotation persistence and one saved deployment project. No separately registered OAuth client or external database was provisioned.

- Both copied development exports ran their actual manifest commands outside the checkout with a fresh dependency cache, discovered seven tools and recovered their native agent's scoped work. Strict Claude validation passed. This proves package processes, not an installed host or official listing.
- The first MCP process submitted a synthetic need and ended. An independent native listener process returned a checked pending request before the owner browser submitted its answer. The trusted route launched a dedicated restricted Claude session. Its deduplicated transcript contains the one expected Bash invocation of the native synthetic worker. The worker recovered context and approval, declared/read back its intent, wrote/read the private blue marker, settled it and reported authenticated `resumed`.
- After the profile fix, the real Claude adapter ran successfully using exactly the published three-field native profile. Its worker verified existing artifacts with unchanged hashes, modification times and action count.
- Marker SHA256: `d514fde0329fbe404afb2f79a3ff0f82cb26d6de41a384d69a81547d789608bf`. A replacement recovered the current work and verified the same artifact with unchanged modification time/hash and action count. No existing effect was repeated.
- The listener was stopped. A second question generation and browser answer remained `awaiting_pickup`, with no current progress or new artifact. A deliberately failed trusted route reported failure without progress. A repaired dedicated restricted Claude session then resumed, and native readback preserved failed and queued route observations separately from authenticated continuation.
- Owner browser verification used a bounded authenticated QA proxy forwarding to the actual deployed app. Direct production native API reads verified scope/state separately. The browser showed resumed evidence plus a queued-only route report. No direct-origin interactive browser sign-in claim is made.
- A fresh-context skill baseline failed with the old loopback-only recipe and retained unknown work. After the contained native recipe was added, a fresh evaluator used only the skill/reference plus the actual native CLI to check identity, attention and request recovery. It correctly retained resumed obligations and unknown future listener/expiry/host coverage.

Live evidence and credentials remain in private state outside source. Source scanning against actual server keys, private account/annotation bindings and test credentials found no hits. Build passed; Svelte check had zero errors and two inherited template deprecation warnings. The local independent-listener smoke also passed.

## Scope decisions retained

The reviewer set aside actual installed-host/remote ChatGPT integration, marketplace acceptance and second-account deployment; unattended renewal and persistent startup coverage; general tasks, busy arbitrary sessions and non-idempotent external effects; a credentialed live rerun/private transcript inspection; and full M3 completion. The maintainer retains each as open acceptance work or an explicit proof limit. Existing live evidence covers the bounded synthetic route only. Shipping it must not imply those broader capabilities; the cost of ignoring these limits would be a false automatic-pickup or public-release claim.

The implementation reuses tested local route/claim/process cleanup mechanics while keeping native persistence and its HTTP/MCP contract separate. Listener delivery observations are required for accurate human status and never grant agent progress authority. Production synthetic fixtures stay private; a new account must establish its own enrolled fixtures instead of replaying ours. Canonical skills and contribution/star links remain in `ashfulcra/unblock-any-agent`.

**Full M3 and the first public release remain incomplete.** Remaining outcomes include the selected ChatGPT/other actual host path, bounded credential renewal, clean installed-host and second-account fork checks, and official package/submission eligibility. No persistent scheduler, bare command reservation or marketplace acceptance is claimed.
