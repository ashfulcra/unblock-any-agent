# Run a live Unblock demo

Use the existing [personal dashboard](https://unblock-any-agent.my.fulcra.ai/) and [private plugin](https://chatgpt.com/plugins/plugins_6ad28048f1e08191b3cf37f769d80877). These links require the owner's existing access; the private plugin is not a public listing.

## A three-minute demonstration

1. Open the dashboard or ask the connected human inbox: **Show my agent decisions.** Sign in through the normal Fulcra flow if the browser session expired.
2. Open a fresh **DEMO** question. Read the agent's actual name, question, recommendation and next action. Rehearsal answers are explicitly labeled **SIMULATED REVIEW**; leave fresh live questions unanswered until the presenter chooses.
3. Choose an answer. The card should first show that the answer awaits pickup. A saved answer is not completed agent work.
4. In the responsible agent's existing chat, say: **Recover your Unblock work through your own assigned profile and continue the disposable demo report. Check the current question, every answer and uncertain effects before acting.** This demonstration uses explicit prompted pickup.
5. Show the card's verified progress and the responsible agent's report. Check its report path, content and source evidence. Completion requires that agent's source-checked progress, not a launcher receipt or another agent's claim.

Keep one completed rehearsal available as a fallback if a live host or network becomes unavailable. Explain any failed or expired connection honestly; retain its pending question and effects for recovery.

## Connect another agent

The owner enrolls **Agent worker** from **Connect an agent** on the dashboard using a stable agent ID, display name and environment. Save its sealed credential in a private 0600 profile outside the package. Give that agent only its own profile path. Do not give it the owner's Fulcra authentication or another agent's profile.

For a supported local host, use the complete generated package and set `UNBLOCK_AGENT_CONFIG` for that host's MCP process. GUI hosts may not inherit shell variables. [Setup reference](../skills/unblock/references/setup.md) describes both native and loopback transports; [local packages](local-plugins.md) describes the generated exports. Verify tool discovery and a harmless `recover_work` call in the actual host.

A worker can also use the native Python CLI from an approved source checkout:

```sh
python3 -m unblock.native_client --config /PRIVATE/own-agent.json attention
```

Give the agent this starter instruction:

> Use your own assigned Unblock profile. Recover pending questions, all revisions and answers, uncertain effects and declared work before starting. For a disposable demo only, ask me whether your report should use bullets or a short paragraph. Preserve its exact report destination and a stable intent. After I answer and prompt you to continue, recover the current snapshot; declare and read back the action, write and verify your report, settle the actual effect and source-check resumed/completed. Keep pending work in your exit check. A source failure is unknown work, not an empty inbox.

Native enrollments expire within an hour. A separate trusted owner operator can renew only explicitly selected scopes using [native renewal](native-renewal.md). The worker package does not start renewal, monitoring or background wake. An expired credential needs that authorized owner workflow; never switch global CLI ownership or move owner credentials into a worker.

## What the demonstration establishes

A source-verified question, separately supplied answer, actual responsible-agent recovery and verified report establish that bounded local workflow. Explicitly label simulated review and prompted pickup. API checks, export tests and package installation alone do not establish model continuation. ChatGPT web connection, broad automatic wake, arbitrary desktop model replacement and official marketplace acceptance require their own actual evidence.

## Verification on November 6

Two actual existing local Codex sessions completed separate disposable report rehearsals through their own narrow native profiles after labeled simulated owner review and explicit recovery prompts. A second same-session rehearsal revised its question, rejected an old owner answer snapshot at the hosted service, then recovered across a deliberate turn boundary after an unsettled report effect. The report hash and modification time remained unchanged while one original action was settled. This establishes that cooperative recovery case, not arbitrary model replacement. Fresh live questions are separate from completed rehearsals.

The existing maintainer heartbeat is configured to inspect only its explicitly assigned demo routes and relay actual answers to their responsible existing chats. Configuration is separate from a verified scheduled invocation and model continuation. For an immediate presentation, ask the maintainer to check the demo answers now.

A separate November 6 rehearsal observed a genuine maintainer heartbeat, a supported relay to the original local Codex session, and that responsible agent’s source-checked completed report without another human check prompt. The report had one action/settlement and no uncertain effect. Full continuation missed its original 20-minute window, so it does not establish timely automatic pickup. This is a local scheduled relay followed by prompted model recovery; retain the immediate presentation prompt above as the verified interactive path.

The owner’s main in-app dashboard was subsequently authenticated through the normal Google/Fulcra flow and checked against the live native source. Both fresh live cards, full report-only contexts, recommendations and empty decision controls were inspected without submitting an answer. An earlier different-account attempt was correctly denied; no owner configuration or credential transfer was used to resolve it.
