# Native renewal review — 2026-10-16

A separate, explicit trusted operator renews selected native worker/listener connections through the existing Fulcra CLI. It uses fixed owner operations and captures the owner access token in memory. Worker exports omit the owner transport and renewal modules. No new OAuth client, copied refresh token, database or persistent scheduler is required or installed.

## Observed behavior

- The deployed service denied expired original grants and accepted renewed grants with identical roles, environments and explicit agent scopes.
- Stopping the operator let replacements expire. The independent listener reported source unavailable and retained the same pending request. Restarting the operator restored that same source, identity and ledger; the synthetic request was then completed.
- The actual preparation command derived enrollment IDs from verified private profiles without manual copying or enrolling another identity.
- Parent expiry left a valid child authorized. Revoking a predecessor denied its descendant, stopped the operator and preserved the managed profile.
- Evaluation processes were stopped and dedicated grant families revoked. The owner token was absent from the tested profiles, state and logs. Two initial harness errors were retained; evaluation resumed the same saved request and enrollments.
- The completed synthetic renewal obligation was observed in the deployed dashboard through the bounded authenticated QA proxy. This does not assert a fresh interactive sign-in at the production origin.

## Independent review and fixes

A fresh whole-branch reviewer inspected the four-commit branch against its plan, spec and private evidence. It found no Critical issues, two Important issues and no Minor issues. Both Important findings were accepted and fixed in one pass:

1. Retiring an exact visible expired pending grant previously skipped it as the next predecessor. The operator now retains that predecessor, checks its revocation and includes the exact parent in readback verification.
2. A crash immediately after profile publication followed by restart after expiry previously discarded the candidate while retaining an old file hash. Recovery now recognizes its exact already-installed candidate, records its hash without rewriting it, and permits the next bounded renewal.

Both combined regressions failed before the fixes and passed afterwards. The author verified the fixes; the reviewer was not asked to repeat its review.

## Validation and remaining limits

The complete Python suite passed **77 tests**; all **21 web tests** passed. Svelte check reported zero errors and two inherited template warnings, and the production build passed. Both copied manifest commands discovered seven tools and recovered work with a fresh dependency cache; Claude strict package validation passed. Version 0.3.0 exports exclude operator/owner modules. Private-binding source scanning passed.

The CLI returns structured status: inspect `checked`, `pending` and `errors`, not process exit alone. An unseen expired enrollment remains pending until exact readback or owner reconciliation. Same-account OS compromise and measured large-history optimization remain outside this pilot's demonstrated boundary.

This proves bounded explicit renewal and recovery, not a forced upstream refresh-token exchange, indefinite access, persistent scheduling, remote ChatGPT authorization, marketplace acceptance, clean second-account setup or arbitrary-host wake. Those release outcomes remain separate obligations. See [operator setup](../native-renewal.md).
