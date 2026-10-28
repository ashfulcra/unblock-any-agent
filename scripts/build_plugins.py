"""Build self-contained local development exports without private state."""
import argparse
import json
from pathlib import Path
import shutil

SOURCE=Path(__file__).resolve().parents[1]
VERSION='0.7.4'
REPOSITORY='https://github.com/ashfulcra/unblock-any-agent'
RUNTIME=('__init__.py','__main__.py','client.py','server.py','store.py','listener.py','claude_route.py','mcp_bridge.py','native_client.py','native_mcp.py','native_listener.py','native_worker.py','native_monitor.py','human_inbox.py','human_mcp.py')
SKILL=('SKILL.md','references/setup.md','references/human-inbox.md')


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def copy(relative,destination):
    source=SOURCE/relative
    if source.is_symlink() or any(parent.is_symlink() for parent in source.parents if parent!=SOURCE.parent) or not source.is_file():
        raise ValueError('Export sources must be contained regular files')
    if not source.resolve().is_relative_to(SOURCE):raise ValueError('Source escapes repository')
    destination.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,destination)


def build(output):
    output=Path(output).absolute()
    # Never overwrite a prior export or copy a whole checkout/cache recursively.
    output.mkdir(parents=True,exist_ok=False)
    exports={platform:output/platform/'unblock' for platform in ('claude','openai')}
    for platform,root in exports.items():
        root.mkdir(parents=True)
        for name in ('LICENSE','THIRD_PARTY_NOTICES'):copy(Path(name),root/name)
        for name in RUNTIME:copy(Path('unblock')/name,root/'unblock'/name)
        for name in ('index.html','app.js','style.css'):copy(Path('unblock/static')/name,root/'unblock/static'/name)
        for name in SKILL:copy(Path('skills/unblock')/name,root/'skills/unblock'/name)
        copy(Path('scripts/run_mcp.py'),root/'scripts/run_mcp.py')
        copy(Path('scripts/run_inbox_mcp.py'),root/'scripts/run_inbox_mcp.py')
        copy(Path('unblock/ui/inbox.html'),root/'unblock/ui/inbox.html')
        copy(Path('requirements-mcp.txt'),root/'requirements-mcp.txt')
        manifest={'name':'unblock','version':VERSION,'description':'Request human help, recover continuity, and verify that an agent continued.','author':{'name':'Fulcra Dynamics'},'license':'Apache-2.0','repository':REPOSITORY,'homepage':REPOSITORY,'keywords':['agents','continuity','human-in-the-loop']}
        server={'command':'uv','args':['run','--no-project','--with','mcp==2.3.0','python',('${CLAUDE_PLUGIN_ROOT}' if platform=='claude' else '${PLUGIN_ROOT}')+'/scripts/run_mcp.py']}
        if platform=='claude':
            manifest['displayName']='Unblock Any Agent'
            write_json(root/'.claude-plugin/plugin.json',manifest)
            write_json(root/'.mcp.json',{'mcpServers':{'unblock':server}})
        else:
            manifest['$schema']='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
            manifest['extensions']={'com.openai':{'interface':{'displayName':'Unblock Any Agent','shortDescription':'Help agents keep moving','longDescription':'Local development tools for human decisions, continuity recovery, and verified agent progress. Connects an enrolled Fulcra-native pilot or loopback proof profile and a separately configured environment listener. An optional separate human inbox offers an interactive decision view.','developerName':'Fulcra Dynamics','category':'Productivity','capabilities':['Interactive']}}}
            write_json(root/'plugin.json',manifest)
            write_json(root/'mcp.json',{'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'unblock':{'type':'stdio',**server}}})
        (root/'README.md').write_text(f'''# Unblock Any Agent — local development package

Canonical source, shared skills, contributions and stars: {REPOSITORY}

This self-contained {platform} export includes the `unblock` skill and agent-bound stdio MCP bridge. It needs Python 3.13+, `uv`, an enrolled native pilot or running loopback proof service, and `UNBLOCK_AGENT_CONFIG` explicitly configured in the host MCP server environment as the absolute path of the enrolled agent's private 0600 config. Keep that file outside the plugin. `uv` resolves the pinned MCP SDK when starting the bridge; the first run needs package-network access. A shell-process export does not configure an app-managed plugin automatically. Keep personal host environment settings outside this canonical source. The agent config selects its authorized identity, source and transport; tools cannot enroll an owner or choose another sender.

Read `skills/unblock/references/setup.md` for setup, CLI fallback and listener requirements. The runtime is included. Native profiles use `python3 -m unblock.native_client`; the separate loopback proof uses `python3 -m unblock`. On Claude Code, load this directory with `--plugin-dir`; the standard skill is namespaced as `/unblock:unblock`. No bare `/unblock` registration or namespace reservation is claimed. Test actual tool discovery and a harmless recovery call in your host.

This package does not install a persistent listener, connect ChatGPT web, implement remote OAuth or prove marketplace eligibility. The stdio MCP bridge ends with its host session; configure a separate environment listener or supported scheduled check for later answers. Native expected-update checks use the separate `python3 -m unblock.native_monitor` process; it records concerns and executes no agent commands. Publisher: Fulcra Dynamics. Original project contributions use Apache-2.0; see LICENSE and THIRD_PARTY_NOTICES. Public submission still requires applicable host authentication, publisher verification, installation and actual listing checks documented in the canonical repository.

The optional human inbox uses `scripts/run_inbox_mcp.py` and an explicit private `UNBLOCK_HUMAN_CONFIG` profile. It is separate from this default worker connection and is never selected automatically. It checks the current human account and its fixed owned deployment before using existing Fulcra CLI sign-in. It exposes only inbox/review/answer tools and an MCP Apps view; it cannot enroll, renew or execute agent work. See the contained setup reference. UI availability and installation must be verified in the actual host.
''')
        if platform=='claude':
            with (root/'README.md').open('a') as readme:
                readme.write('\nInstall this source candidate in Claude Code 2.1.275 or later with `/plugin install unblock --marketplace ashfulcra/unblock-any-agent`. This GitHub source catalog is separate from an official directory listing and reserves no global namespace.\n')
    return exports


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
    args=parser.parse_args()
    print(json.dumps({platform:str(path) for platform,path in build(args.out).items()},indent=2))

if __name__=='__main__':main()
