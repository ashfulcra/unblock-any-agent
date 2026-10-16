# Plugin source candidates

Canonical skills, product source, issues, contributions and stars: [ashfulcra/unblock-any-agent](https://github.com/ashfulcra/unblock-any-agent).

| Source path | Use | Current status |
| --- | --- | --- |
| [claude/unblock](claude/unblock) | Complete Claude Code plugin directory; a GitHub commit and this subdirectory can be reviewed by the official directory. | Development candidate, version 0.4.0. |
| [openai/unblock](openai/unblock) | Complete portable Agent Plugins directory with local stdio MCP. | Development candidate, version 0.4.0; desktop-only submission needs the documented partner route. |

Each directory is self-contained and generated from the canonical runtime and `skills/unblock`. Do not edit generated files. From the repository root, build to a new private output directory with `python3 scripts/build_plugins.py --out <fresh-directory>`, then replace the corresponding candidate trees with those exact outputs. CI rebuilds and compares every file, so changes to canonical runtime or skills must regenerate both candidates.

For Claude Code 2.1.275 or later, the source-catalog install command is `/plugin install unblock --marketplace ashfulcra/unblock-any-agent`. This installs from the canonical GitHub source catalog; it is separate from official directory acceptance and reserves no global namespace. Configure the private worker profile first.

For temporary Claude Code loading from a clone, set `UNBLOCK_AGENT_CONFIG` to your existing private enrolled worker profile outside this repository, then run `claude --plugin-dir /absolute/path/to/unblock-any-agent/plugins/claude/unblock`. Use `/unblock:unblock`; the package does not reserve bare `/unblock`. See [setup and actual host evidence](../docs/local-plugins.md) and the contained setup reference.

Source publication does not select a project license, verify a publisher, reserve a namespace, install a persistent listener or establish an official listing. Publisher/license decisions and actual portal checks remain required. The portable local package is not a ChatGPT web connection; remote authorization and event pickup remain separate work. See [official release plan](../docs/marketplace-release-plan.md).
