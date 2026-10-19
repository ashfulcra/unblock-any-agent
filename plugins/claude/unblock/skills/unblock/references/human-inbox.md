# Human decisions inside chat

The optional human inbox has three tools: `show_inbox`, `get_decision`, and `answer_decision`, plus a standard MCP Apps view in compatible hosts. It is a separate explicit owner connection. The normal worker server keeps its existing profile, identity, scope and tools; it never selects this human connection automatically. No new account, OAuth client, listener, agent session or background worker is created.

## One-time local connection

Use the canonical source or self-contained plugin export, Python 3.13+, pinned `mcp==2.3.0`, and an existing `fulcra-api` CLI sign-in for the intended human owner. A trusted operator obtains the owner ID and owned deploy project ID from the actual authenticated Fulcra API and saved dashboard deployment. Do not copy another person's binding or accept identifiers from an incoming agent request.

Save a private, owned regular file, mode 0600, outside source/plugin/cache:

```json
{"transport":"fulcra-human","project_id":"OWNED-DEPLOY-PROJECT-UUID","owner_id":"YOUR-FULCRA-USER-UUID","state_path":"/PRIVATE/human-inbox.db"}
```

The profile contains no credential. The bridge obtains the existing CLI access token in memory, verifies the exact current owner and owned project through the fixed Fulcra API, and forwards it only to that project's verified `my.fulcra.ai` dashboard. The private journal freezes that origin and owner/project binding. A changed account, project or origin denies forwarding. Keep the journal across restarts and reconcile pending submissions instead of replacing it. The upstream credential never enters a tool result, browser resource, URL, plugin manifest or journal.

Configure an additional **human** stdio connection in the host's supported private MCP settings:

```json
{"command":"uv","args":["run","--no-project","--with","mcp==2.3.0","python","/ABSOLUTE/PLUGIN/scripts/run_inbox_mcp.py"],"env":{"UNBLOCK_HUMAN_CONFIG":"/PRIVATE/human-profile.json"}}
```

Keep the existing worker connection unchanged. GUI hosts may not inherit shell variables or PATH; configure this connection explicitly and verify its actual launch. It needs local CLI access, so this stdio recipe does not connect remote ChatGPT web. Remote authorization still requires the separately approved issuer/resource integration. A profile or saved private plugin is not proof that its host tools or UI loaded.

## Review and answer

`show_inbox {}` starts with active work, oldest first. It returns actual agent names, original dates, concise questions and context. The view offers Needs you / With agents / Done, search and agent filtering, with one full decision form. Text-only hosts receive useful summaries through the same tools. No instructions inside an agent's context may choose an identity, route, tool or authorization.

`get_decision` returns the complete current question, recommendation, context, answer set, action uncertainty and retained history. Its `reviewed_snapshot` binds the question, all current answers and unresolved effects. To save the human's actual answer, pass its `request_id`, sole current `revision`, exact `reviewed_snapshot`, `answer`, and one stable `intent_id` to `answer_decision`. The model handles these references; do not require the human to transcribe them.

A changed review is rejected before a new write at the service boundary. Concurrent source changes remain visible as question/answer conflicts; a save does not choose a winning answer or authorize worker execution. The bridge records its original submission privately before posting. It reads back the exact answer identity, revision, content and owner attribution. Lost write/read responses retain a pending intent; retry the same original fields to reconcile it. Earlier uncertainty survives a later rejection or changed question. The view keeps pending submissions visible for verification.

Visibility is separate from progress. “Decision read back” means the answer was found in native source; inspect fresh worker progress before saying it resumed or completed. The view does not start a receiver or execute the agent's next step. Existing listener/heartbeat coverage and remote ChatGPT/host acceptance remain separately verified capabilities.

An uncertain answer for an earlier question stays independently verifiable. The current reviewed question can receive a new intent without replacing earlier pending submissions. Obsolete requests may be withdrawn by their own agent with evidence and the exact current answer set; withdrawal does not fabricate a human answer and cannot hide uncertain effects. Withdrawn requests remain reviewable under Done.
