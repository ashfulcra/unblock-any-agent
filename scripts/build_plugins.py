"""Build self-contained local development exports without private state."""
import argparse
import json
from pathlib import Path
import shutil

SOURCE=Path(__file__).resolve().parents[1]
VERSION='0.1.0'
REPOSITORY='https://github.com/ashfulcra/unblock-any-agent'
RUNTIME=('__init__.py','__main__.py','client.py','server.py','store.py','listener.py','claude_route.py','mcp_bridge.py')
SKILL=('SKILL.md','references/setup.md')


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
        for name in RUNTIME:copy(Path('unblock')/name,root/'unblock'/name)
        for name in ('index.html','app.js','style.css'):copy(Path('unblock/static')/name,root/'unblock/static'/name)
        for name in SKILL:copy(Path('skills/unblock')/name,root/'skills/unblock'/name)
        copy(Path('scripts/run_mcp.py'),root/'scripts/run_mcp.py')
        copy(Path('requirements-mcp.txt'),root/'requirements-mcp.txt')
        manifest={'name':'unblock','version':VERSION,'description':'Request human help, recover continuity, and verify that an agent continued.','author':{'name':'ashfulcra'},'repository':REPOSITORY,'homepage':REPOSITORY,'keywords':['agents','continuity','human-in-the-loop']}
        server={'command':'uv','args':['run','--no-project','--with','mcp==2.3.0','python',('${CLAUDE_PLUGIN_ROOT}' if platform=='claude' else '${PLUGIN_ROOT}')+'/scripts/run_mcp.py']}
        if platform=='claude':
            manifest['displayName']='Unblock Any Agent'
            write_json(root/'.claude-plugin/plugin.json',manifest)
            write_json(root/'.mcp.json',{'mcpServers':{'unblock':server}})
        else:
            manifest['$schema']='https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
            manifest['extensions']={'com.openai':{'interface':{'displayName':'Unblock Any Agent','shortDescription':'Help agents keep moving','longDescription':'Local development tools for human decisions, continuity recovery, and verified agent progress. Requires a configured local Unblock service and a separate environment listener.','developerName':'ashfulcra','category':'Productivity','capabilities':[]}}}
            write_json(root/'plugin.json',manifest)
            write_json(root/'mcp.json',{'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'unblock':{'type':'stdio',**server}}})
        (root/'README.md').write_text(f'''# Unblock Any Agent — local development package

Canonical source, shared skills, contributions and stars: {REPOSITORY}

This self-contained {platform} export includes the `unblock` skill and agent-bound stdio MCP bridge. It needs Python 3.13+, `uv`, a running loopback Unblock service, and `UNBLOCK_AGENT_CONFIG` set to the absolute path of the enrolled agent's private 0600 config. Keep that file outside the plugin. `uv` resolves the pinned MCP SDK when starting the bridge; the first run needs package-network access. The agent config selects its identity and loopback service; tools cannot enroll an owner or choose another sender.

Read `skills/unblock/references/setup.md` for setup, CLI fallback and listener requirements. The runtime is included: its CLI can run with `python3 -m unblock` from this directory. On Claude Code, load this directory with `--plugin-dir`; the standard skill is namespaced as `/unblock:unblock`. No bare `/unblock` registration or namespace reservation is claimed. Test actual tool discovery and a harmless recovery call in your host.

This package does not install a persistent listener, connect ChatGPT web, implement remote OAuth or prove marketplace eligibility. The local MCP bridge ends with its host session; configure a separate environment listener or supported scheduled check for later answers. Public submission requires the remaining authentication, endpoint, host, listing and license decisions documented in the canonical repository. No project license has been selected for public distribution.
''')
    return exports


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
    args=parser.parse_args()
    print(json.dumps({platform:str(path) for platform,path in build(args.out).items()},indent=2))

if __name__=='__main__':main()
