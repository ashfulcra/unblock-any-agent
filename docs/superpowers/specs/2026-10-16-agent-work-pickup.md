# Agent work pickup

Status: proposed design supplement, 2026-10-16. Requirement R17 is confirmed; the implementation mechanisms below require live verification. This supplements the first-release spec and does not approve product implementation.

## The failure to prevent

Tycho returned the requested Fable review, but the maintainer retrieved it only after Ash said “Check response.” The request, report, and addressed response were durable. That did not cause this idle maintainer to run. The maintainer's own V5 exit checks covered its authorized work projection; the response arrived through a different delivery surface. No automatic receiver for that surface was installed by the maintainer enrollment. This is an observed missing pickup contract, not proof of a particular router fault.

The product must close this gap for human answers, returned reviews, agent results, assignments, and released dependencies. The human should not become the message relay or repeatedly remind agents to check. Receiving work grants no new action authority.

## Proposed approach

Use native plugin integrations for pickup where current hosts support them. Use one shared durable work context so a different authorized session can recover when the original session is unavailable. Keep skills as the portable instructions and onboarding layer. Separate detecting available work, causing execution, and reconciling that work once execution starts.

| Approach | Benefit | Limit |
| --- | --- | --- |
| Native plugin receiver | Uses host-supported triggers and session context; lowest extra operating burden where available. | Support differs across host, account and distribution channel. |
| Authorized external runtime | Can run independently of the original session and recover work into a supported runtime. | Requires a verified launcher, credential custody, operating owner and explicit scope. It must not impersonate an arbitrary existing chat. |
| Check at startup or explicit Continue | Broad portability and useful recovery. | Does not solve idle automatic pickup on its own. |

Recommended combination: native receivers first; an external runtime only for a demonstrated missing capability; startup reconciliation and explicit recovery on every entry point. This is not a mandate for a new bus, polling daemon, scheduler, or legacy actor binding.

## Current mechanism evidence

Checked against primary documentation on 2026-10-16; none has yet passed this product's live integration tests.

| Target | Candidate | Required verification |
| --- | --- | --- |
| ChatGPT Work on web or desktop Cloud; dots | MCP Events subscriptions through the product's remote MCP server. | Actual supported account/surface, authorized subscription, callback delivery, correct work context, execution and progress report; paused/expired/revoked subscription behavior. |
| Live Claude Code session in a supported mod host | Background job calls `$.prompt.submit`; the API waits for idle before starting a turn. | Actual mod loading, bounded quiet checks or verified change feed, correct session, busy handling and preserved sender attribution. A mod does not itself restore a closed session. |
| Claude Code channel | Push into a running session. | Preview availability, effective plugin allowlist and per-session enablement. Do not make public-release pickup depend on development-only enablement. |
| Local Codex | Host-native delivery or an authorized independent task/runner, to be selected. | A lifecycle hook runs only when its event occurs; no unattended local wake is established by the Work MCP Events documentation. Verify actual supported entry and package distribution. |
| Claude chat/Cowork and bare skills | Shared tools and context; additional supported runtime route where available. | Do not infer mod support, background execution, or scheduling from skill installation. Report the actual capability or the manual recovery requirement. |

MCP Events is particularly relevant: it can invoke configured work when a matching event arrives on supported Work surfaces. The application still needs an actual source of events, including when a result arrives through an external agent connection. A scheduled check for an overdue obligation remains a separate detector requirement.

OpenAI's public submission rules currently exclude lifecycle-hook packages. This does not exclude the documented remote MCP Events route. Keep the public export and any separately installed local capabilities distinct, and verify directory acceptance rather than assuming local support implies public eligibility.

## Receiver contract for each agent

Onboarding must identify the authenticated agent and authorized work, select a real execution destination, and enable the matching receiver or subscription. Test it before calling the agent automatically reachable. Product identity persists across sessions; a display label or a guessed last-used session is insufficient routing evidence.

Record the supported host/surface, operating owner, trigger permissions, enabled status, last successful pickup, expected pickup deadline, and behavior when busy or offline. Expose these to the human in plain language. Do not show an installed plugin or saved route as a healthy receiver without a successful test.

When an answer or result becomes available, retain it before attempting delivery. Send only enough authorized context to identify the work; the receiving agent fetches and reconciles current content and permissions. External text remains source material, not additional instructions or authority. Preserve real sender attribution.

Show result availability, delivery acceptance, agent acknowledgment of the relevant work revision, and useful continuation separately. A webhook success, queued prompt, notification badge, or generic heartbeat proves neither acknowledgment nor continuation. The acknowledgment must refer to the actual item; the subsequent progress must explain what happened or what remains blocked.

While busy, preserve the item until the supported safe execution point; do not disrupt unrelated authorized work. After a restart or replacement, reconcile unresolved work even if a prior delivery was accepted. Concurrent sessions and repeated callbacks must not cause duplicate consequential actions. Retain failed attempts and retry within configured bounds. If no acknowledgment arrives by the declared deadline, show the pickup failure and its exact recovery action, then use an already authorized escalation route.

If a session is closed, use a separately verified authorized launcher/replacement route, or show that automatic pickup is unavailable and retain the work for recovery. Manual recovery keeps an entry point useful but does not pass its automatic-pickup claim. The shared view must retain work that the receiver has not handled; reading an inbox or marking a notification seen must not erase the responsibility.

## Acceptance and evidence

Use the Tycho scenario as an early integration test before the full dashboard: the requester becomes idle; the reviewer returns its result later; the intended worker starts without a human check prompt, retrieves the exact report and performs its next safe action. Record time of availability, delivery, acknowledgment and continuation, the actual host/version, and the selected route. Set the test deadline from the configured route rather than inventing one universal latency target.

Repeat for an agent busy with other work; a disconnected/reconnected receiver; a closed/replacement session; duplicated or out-of-order notifications; and a result written through each entry point. Disable the receiver and revoke access in negative tests. The product must expose those failures, preserve the work, and avoid unauthorized execution. Verify quiet periods do not invoke models unnecessarily.

At least one real automatic pickup route for each advertised automatic host must pass. Validate the portable fallback separately. Track independent stall detection separately, because a functioning receiver cannot invent an event for an obligation whose deadline nobody checks.

## Sources

- [OpenAI MCP Events](https://developers.openai.com/plugins/build/mcp-events): supported Work surfaces, protocol, subscriptions, signed callbacks and asynchronous processing.
- [OpenAI public submission](https://developers.openai.com/plugins/deploy/submission): lifecycle-hook package restriction.
- [OpenAI plugin support](https://learn.chatgpt.com/docs/plugins): host-dependent hooks and installed components.
- [Claude mod API](https://code.claude.com/docs/en/plugins/mods/api): background prompt submission and session-message receipts.
- [Claude channels](https://code.claude.com/docs/en/channels): live-session push and preview/allowlist restrictions.
- [Claude scheduling](https://code.claude.com/docs/en/scheduled-tasks): session-local tasks versus independent Desktop/cloud scheduling.

These sources establish candidate mechanisms. They do not establish that this maintainer, this repository, or a future install is already subscribed, listening, or automatically reachable.
