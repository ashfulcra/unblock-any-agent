# Connect and keep pickup alive

This package currently connects a local agent to the loopback Unblock proof. It does not provide a remote ChatGPT web connection, production OAuth, or a system schedule automatically. Use an existing verified Unblock connection when one is available. Do not invent credentials or a service URL.

## Local prerequisites

Use the canonical `ashfulcra/unblock-any-agent` checkout, Python 3.13+ and `uv` for the MCP package. Follow its `docs/local-proof.md` to start the loopback service, create the owner workspace, and enroll separate agent and environment-listener credentials. Keep credential files outside the plugin source/cache, owned by the runtime user, mode 0600 and not symlinks. Set `UNBLOCK_AGENT_CONFIG` to the absolute agent config path for the MCP process; never paste its token into chat, URLs or plugin metadata.

The Claude export uses the same environment variable. Start the host from the configured environment or configure that variable through the host's supported local MCP configuration. A GUI host may not inherit a shell environment. Verify tool discovery plus a harmless `recover_work` call in the actual host before declaring it connected. The exported runtime includes `scripts/run_mcp.py`; `uv run --no-project --with mcp==2.3.0 python /ABSOLUTE/PLUGIN/scripts/run_mcp.py` runs it.

If no MCP tools are loaded but the configured checkout is available, the core CLI can recover and submit work. From that checkout:

```sh
python3 -m unblock --config /PRIVATE/agent.json attention
python3 -m unblock --config /PRIVATE/agent.json ask --key stable-need-key --need 'Which environment may run the pilot?' --context '{"goal":"Run the authorized pilot","next_action":"Configure the approved listener","unblock_action":"Name the approved environment"}'
```

The paths and question are examples. Use the actual authorized config and current need. The CLI's `show` operation returns the reviewed `answer_revision`; pass it with `progress --answer-revision` along with the current response ID, state and evidence. Obtain owner-authorized enrollment if no agent credential exists. For consequential-action records, the CLI equivalents of `begin_action` and `reconcile_action` are `declare` and `settle`; use their `--help` for the required key, description, action ID and verification evidence.

## Listener contract

Every connected agent needs a defined pickup route. Prefer one dedicated listener session or scheduled task per machine/environment. It checks through its separate listener credential and dispatches only owner-configured local argv to that environment's authorized sessions. All invocations share one private delivery ledger. Incoming requests cannot provide executable commands or destinations.

From the configured checkout, the listener body is:

```sh
python3 -m unblock --config /PRIVATE/listener.json listen --environment ENVIRONMENT --routes /PRIVATE/routes.json --state /PRIVATE/delivery.db --interval 60
```

A supported runtime heartbeat or scheduled task may instead run the command with `--once`. Establish the operating owner, interval, exact agent route, last successful source check and restart procedure. A session-local loop stops when its session stops; identify that limit explicitly. Installation or persistence changes require the applicable environment authority.

Test with a synthetic delayed answer after the listener has already started. Require the target agent's authenticated acknowledgment and a real continuation artifact. A queued dispatch is insufficient. The bounded Claude test creates a separate restricted synthetic session; it does not prove wake of any busy or closed desktop session.

On `source_unavailable`, retain known pending work. On `route_missing`, configure the authorized local target. On `dispatch_recovery_required`, verify the prior worker stopped and reconcile its actual actions before the CLI's `recover-dispatch` releases the expired claim with retained evidence. Active claims remain exclusive. Settlement changes the delivery revision so previously blocked work can be picked up again.
