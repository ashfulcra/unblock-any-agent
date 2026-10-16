# Connect and keep pickup alive

Use the actual authorized connection. The deployed Fulcra-native pilot and loopback proof use different profiles and CLI contracts. Neither installing this skill nor starting MCP installs a background listener. The native web app uses the supplied Fulcra template sign-in; a new registered OAuth client or external database is not its prerequisite. Remote ChatGPT web connections and official marketplace acceptance remain separate work.

## Runtime and credentials

Use Python 3.13+ and the canonical `ashfulcra/unblock-any-agent` checkout or self-contained plugin export. The stdio MCP bridge also needs `uv`, which resolves pinned `mcp==2.3.0` on first launch. Keep profiles outside the source/plugin/cache, owned by the runtime user, mode 0600, regular files without symlinks. Never print their tokens, paste them into chat, put them in URLs or commit them.

Set `UNBLOCK_AGENT_CONFIG` to the absolute agent profile path for the host's MCP process. GUI hosts may not inherit your shell environment. Both exports include `scripts/run_mcp.py`; their manifests launch it with `uv run --no-project --with mcp==2.3.0 python /ABSOLUTE/PLUGIN/scripts/run_mcp.py`. The bridge selects the explicit profile transport and verifies the actual agent role. Listener credentials cannot start worker MCP tools. Verify discovery and harmless recovery in the actual host before declaring it connected. Manifest-command tests alone do not establish installed-host coverage.

## Fulcra-native pilot

Use the owner's saved dashboard origin, never an invented service URL. Sign in, expand **Connect an agent**, select **Agent worker**, and enroll its stable ID, display name and environment. Obtain owner-authorized enrollment if none exists. Save the displayed sealed credential privately in this shape:

```json
{"transport":"fulcra-native","url":"https://YOUR-SAVED-DASHBOARD.my.fulcra.ai","token":"PRIVATE-SEALED-CREDENTIAL"}
```

The server verifies identity/scope; labels in a file or incoming message cannot change them. Grants expire with the originating Fulcra session, within one hour. Renew through owner enrollment and replace the private file under the same identity/scope. No refresh token is stored, and unattended renewal is not implemented. A replacement session can recover the same stable agent with an unexpired credential. Revocation takes effect after native readback. Keep source failures and expired/revoked access as unknown pending work, never quiet.

Without MCP tools, from the configured checkout/export:

```sh
python3 -m unblock.native_client --config /PRIVATE/native-agent.json identity
python3 -m unblock.native_client --config /PRIVATE/native-agent.json attention
python3 -m unblock.native_client --config /PRIVATE/native-agent.json recover --request-id REQUEST-UUID
python3 -m unblock.native_client --config /PRIVATE/native-agent.json request --file /PRIVATE/need.json
```

`attention`/`recover` return an object with `source: checked` and `requests`; inspect all retained obligations, including unanswered requests, historical progress, actions and settlements. A native request JSON contains stable `intent_id`, `need_key`, `need`, `context` **string**, `recommendation`, `next_action`, and `parents: []`. Reuse identical fields/intent after uncertainty; to revise, keep `need_key`, use a new intent and explicitly name the reviewed parent revision IDs.

A native progress JSON contains `intent_id`, `request_id`, the sole current `revision`, the **complete** current `answers` ID array, `stage` (`acknowledged`, `resumed`, `completed`) and actual `evidence`. Multiple answers require actual reconciliation and `reconciled: true`. Use operation `progress --file /PRIVATE/progress.json`. Declare intent with `action` (`intent_id`, `request_id`, `effect`) before consequential work; reconcile with `settle` (`intent_id`, `request_id`, `action` record ID, observed `evidence`). These operations only record evidence; they do not execute the effect.

MCP uses the same seven tool names on both transports, but follow the loaded schema: native `record_progress` takes `revision` and `answer_ids`; native `revise_need` takes explicit `parent_revisions`. Do not pass local `answer_revision` to native tools. Mutation `visibility: pending` is an ingestion receipt. Read back the exact `record_id` in retained recovery history before relying on it. Preserve the original body/intent after an uncertain write. A rejected later retry cannot erase an earlier uncertain attempt.

## Separate loopback proof

Follow the canonical [local proof](https://github.com/ashfulcra/unblock-any-agent/blob/main/docs/local-proof.md) to start its service and enroll separate worker/listener credentials. A profile without native transport selects this local HTTP proof. Do not send a native HTTPS profile to this CLI:

```sh
python3 -m unblock --config /PRIVATE/local-agent.json attention
python3 -m unblock --config /PRIVATE/local-agent.json ask --key stable-need-key --need 'Which environment may run the pilot?' --context '{"goal":"Run the authorized pilot","next_action":"Configure the approved listener","unblock_action":"Name the approved environment"}'
```

Local `show` returns `answer_revision`; local `progress` requires that value with the current response ID, state and evidence. Local action commands are `declare` and `settle`; consult their `--help`. Keep this contract distinct from native immutable revision/answer-set fields.

## Listener contract

Prefer one dedicated listener process/session or scheduled task per machine/environment. For the native pilot, the owner enrolls **Environment listener** with its own stable ID, environment and explicit enrolled worker IDs. Its separate credential can read those agents and publish its own delivery observations; it cannot answer, change context, report agent progress or act as a worker. Each worker route uses that worker's separate agent profile.

Configure a private route file mapping stable agent IDs to exactly `{"argv":["/ABSOLUTE/EXECUTABLE","ARGUMENT"],"cwd":"/ABSOLUTE/DIRECTORY","timeout":150}`. Commands come from trusted local configuration. Incoming work supplies references only. Verify the configured command actually reaches the intended agent; a successful launcher exit is only queued delivery.

```sh
python3 -m unblock.native_listener --config /PRIVATE/native-listener.json --environment ENVIRONMENT --routes /PRIVATE/routes.json --state /PRIVATE/delivery.db listen --interval 60
```

For the loopback proof, use `python3 -m unblock --config /PRIVATE/local-listener.json listen --environment ENVIRONMENT --routes /PRIVATE/routes.json --state /PRIVATE/delivery.db --interval 60`. Do not share one ledger across transports. All listener invocations for the same environment/source must share its private ledger to enforce exclusive dispatch. The ledger also binds the exact dashboard origin. Do not change source/identity/scope or replace that ledger to clear an unresolved claim. A pre-release ledger without an origin needs explicit evidence-backed migration, preserving claims, pending items and receipts.

A supported scheduler/heartbeat can run the relevant command with `--once`; establish its actual owner, cadence, next firing, access, lifetime and restart procedure. A session loop ends with the session. No scheduler or startup persistence is installed by these commands. Native profiles are reopened each tick to accept explicit renewal; expiry still stops source checks/dispatch.

Test a synthetic delayed answer after the listener starts. Require authenticated **fresh** agent progress and a real continuation artifact. Route reports remain separate from progress. The tested Claude route creates a dedicated restricted synthetic session; it does not prove wake of any busy/closed desktop session or general arbitrary-task execution. Other runtime routes need their own supported mechanism and live proof.

Source failure retains known pending work. Missing routes need the exact authorized local target. Native retries are bounded to three per work/route snapshot. Repair the route or reconcile the work instead of repeatedly launching the same failure. Definitively rejected delivery receipts remain in the private rejected-receipt ledger and appear as `receipt_errors`; inspect native history and reconcile them, including any earlier uncertainty. They do not block unrelated authorized work. Authorization/source failure still stops the entire dispatch batch. For `dispatch_recovery_required`, first verify the previous process stopped and reconcile effects, then run native `recover --request-id REQUEST-UUID --evidence 'ACTUAL VERIFICATION'` with the same listener flags before the subcommand. The local equivalent is `recover-dispatch`. Active claims cannot be released. Read the [listener guide](https://github.com/ashfulcra/unblock-any-agent/blob/main/docs/listener-setup.md) for host coverage limits and recovery responsibilities.
