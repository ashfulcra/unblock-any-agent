# Local skill and plugin entry points

The canonical workflow is [skills/unblock](../skills/unblock/SKILL.md). One source produces separate Claude and portable Agent Plugins development exports. These are local packages, not official listings or a ChatGPT web connection.

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements-mcp.txt
.venv/bin/python -m unittest discover -s tests -v
python3 scripts/build_plugins.py --out .state/plugins-dev
claude plugin validate --strict .state/plugins-dev/claude/unblock
.venv/bin/python scripts/verify_exports.py --clean-cache
```

Choose a fresh output directory on every build. The builder refuses to replace an existing export and copies an explicit source allowlist. No credentials, delivery ledgers, symlinks, repository history or cached dependencies are exported. Both outputs include the runtime, skill and contained setup reference; `uv` resolves the pinned MCP SDK at startup.

Set `UNBLOCK_AGENT_CONFIG` to the absolute path of an enrolled agent's private 0600 config **outside** the package. The loopback service must already be running; see [local proof](local-proof.md). The MCP process verifies the credential's actual agent role. Tools cannot enroll an owner, select another sender, provide an arbitrary URL or execute commands. Revocation remains enforced by the application service.

For Claude Code, load the complete Claude export with the host's `--plugin-dir` option. The current standard invocation is `/unblock:unblock`; a bare `/unblock` mod registration remains separate work. For another compatible local host, use the portable export and its `mcp.json`. Verify tool discovery and a harmless `recover_work` call in the actual host before declaring installation complete. A GUI host may need its environment configured explicitly.

A local bridge is also runnable directly:

```sh
UNBLOCK_AGENT_CONFIG=/PRIVATE/agent.json uv run --no-project --with mcp==2.3.0 python scripts/run_mcp.py
```

Its stdout is MCP protocol traffic. A separate listener or supported scheduled check must notice answers after the MCP/host session ends; installation alone provides no background wake.

Observed verification on 2026-10-16: real stdio clients discovered the seven tools, submitted a need, recovered it in a replacement process, read the human answer and reported authenticated progress. Neighbor reads, malformed work references and revoked credentials stayed errors. Both copied exports ran outside the source checkout. Their actual manifest launch commands also passed discovery and recovery using a fresh dependency cache. Claude strict validation and both portable schema checks passed. This does not establish an installed Claude/ChatGPT plugin or directory acceptance.

The reference skill also passed a fresh-context behavioral test: an agent used the documented Python CLI to recover an existing answer, write and verify a synthetic marker, declare/reconcile its action, report progress and preserve a new missing prerequisite. It accurately retained manual-only pickup when no listener existed. Private fixture identifiers and credentials are excluded from source.

See [marketplace plan](marketplace-release-plan.md) for actual publishing routes. OpenAI now documents a separate approved-partner route for local MCP submissions; that route requires organization allowlisting and clean desktop-install evidence. The broader ChatGPT web goal still needs an authenticated remote HTTPS endpoint. [Official desktop-only submission instructions](https://developers.openai.com/plugins/deploy/desktop-only)
