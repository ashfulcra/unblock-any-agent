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

Set `UNBLOCK_AGENT_CONFIG` to the absolute path of an enrolled agent's private 0600 config **outside** the package. For `transport: fulcra-native`, use an enrolled profile for the saved [native pilot](native-pilot.md) origin. Otherwise the loopback service must already be running; see [local proof](local-proof.md). The MCP process verifies the credential's actual agent role. Tools cannot enroll an owner, select another sender, provide an arbitrary URL or execute commands. Revocation remains enforced by the application service.

For Claude Code, load the complete Claude export with the host's `--plugin-dir` option. The current standard invocation is `/unblock:unblock`; a bare `/unblock` mod registration remains separate work. For another compatible local host, use the portable export and its `mcp.json`. Verify tool discovery and a harmless `recover_work` call in the actual host before declaring installation complete. A GUI host may need its environment configured explicitly.

A local bridge is also runnable directly:

```sh
UNBLOCK_AGENT_CONFIG=/PRIVATE/agent.json uv run --no-project --with mcp==2.3.0 python scripts/run_mcp.py
```

Its stdout is MCP protocol traffic. A separate listener or supported scheduled check must notice answers after the MCP/host session ends; installation alone provides no background wake.

Observed verification on 2026-10-16: real stdio clients discovered the seven tools, submitted a need, recovered it in a replacement process, read the human answer and reported authenticated progress. Neighbor reads, malformed work references and revoked credentials stayed errors. Both copied exports ran outside the source checkout. Their actual manifest launch commands also passed discovery and recovery using a fresh dependency cache. Claude strict validation and both portable schema checks passed. This does not establish an installed Claude/ChatGPT plugin or directory acceptance.

The reference skill also passed a fresh-context behavioral test: an agent used the documented Python CLI to recover an existing answer, write and verify a synthetic marker, declare/reconcile its action, report progress and preserve a new missing prerequisite. It accurately retained manual-only pickup when no listener existed. Private fixture identifiers and credentials are excluded from source.

See [marketplace plan](marketplace-release-plan.md) for actual publishing routes. OpenAI now documents a separate approved-partner route for local MCP submissions; that route requires organization allowlisting and clean desktop-install evidence. The broader ChatGPT web goal still needs an authenticated remote HTTPS endpoint. [Official desktop-only submission instructions](https://developers.openai.com/plugins/deploy/desktop-only)

The native transport is also exercised through both copied manifest commands with a fresh dependency cache. It preserves immutable question revisions, full answer sets, action evidence and scoped agent recovery. The distributed setup reference has native and loopback CLI recipes separately. A native environment listener has demonstrated delayed restricted Claude pickup after the originating MCP process ended. Native grants still expire within one hour of owner enrollment; a separate opt-in owner operator can renew those fixed scopes after readback. The package does not start that operator or establish a remote ChatGPT web connection.

Actual Claude host check: Claude Code loaded the complete version0.3.0 export using `--plugin-dir`, exposed `unblock:unblock`, discovered the deferred `recover_work` tool through ToolSearch and called it against the enrolled native identity. The response reported `source: checked` with an empty synthetic work set. An initial session with no discovery tool ended while MCP was pending and is retained as a failed check. Both test grants were revoked and read back. This proves a temporary host-loaded plugin read, alongside the separate delayed Claude route proof; it does not claim a persistent installation, bare `/unblock`, ChatGPT connection or official listing.

## Published source candidates

The canonical repository includes complete generated [Claude](../plugins/claude/unblock) and [portable OpenAI](../plugins/openai/unblock) version 0.7.4 directories, published by Fulcra Dynamics with Apache-2.0 and retained upstream notices. They require no build to obtain their runtime or skill files. CI rebuilds both from canonical source and rejects any content or file-tree drift. Keep worker profiles, tokens and listener ledgers outside these directories.

The Claude directory provides the immutable GitHub commit/subdirectory shape required for directory review and supports the temporary `--plugin-dir` loading flow above. The portable directory uses local stdio; it does not provide ChatGPT web OAuth or events. These are public development sources, not accepted official listings or submission-ready packages: publisher-account verification and the remaining platform requirements still apply. See [candidate maintenance](../plugins/README.md).

The repository also contains a validated Claude source catalog. On Claude Code 2.1.275 or later, `/plugin install unblock --marketplace ashfulcra/unblock-any-agent` selects this canonical repository's development candidate. Configure `UNBLOCK_AGENT_CONFIG` first. This source install is distinct from the requested official public directory listing; the latter remains pending. No persistent install was performed during source-candidate preparation.
