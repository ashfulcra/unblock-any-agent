"""Exercise actual exported stdio launch commands with disposable local state."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil
import tempfile
import threading
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from unblock.client import private_write
from unblock.server import create_server
from unblock.store import Store
from scripts.build_plugins import build


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--clean-cache',action='store_true',help='Acquire SDK dependencies in a fresh uv cache; requires network access')
    args=parser.parse_args()
    if not shutil.which('uv'):raise SystemExit('uv is required')
    with tempfile.TemporaryDirectory(prefix='unblock-package-proof-') as temporary:
        root=Path(temporary);store=Store(root/'work.db')
        owner=store.authenticate(store.bootstrap_owner('Synthetic package proof')['token'])
        workspace=store.create_workspace(owner,'Synthetic team')['id'];grant=store.enroll(owner,workspace,'Synthetic worker','agent','proof')
        server=create_server(store,port=0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        config=root/'agent.json';private_write(config,{'url':f'http://127.0.0.1:{server.server_port}',**grant})
        exports=build(root/'exports')
        async def verify():
            outcomes=[]
            for platform,folder in exports.items():
                manifest=json.loads((folder/('.mcp.json' if platform=='claude' else 'mcp.json')).read_text())['mcpServers']['unblock']
                env={'UNBLOCK_AGENT_CONFIG':str(config)}
                if args.clean_cache:env['UV_CACHE_DIR']=str(root/'uv-cache')
                arguments=[value.replace('${CLAUDE_PLUGIN_ROOT}',str(folder)).replace('${PLUGIN_ROOT}',str(folder)) for value in manifest['args']]
                params=StdioServerParameters(command=manifest['command'],args=arguments,env=env,cwd=str(root))
                async with Client(params) as client:
                    tools=(await client.list_tools()).tools
                    recovered=await client.call_tool('recover_work',{})
                    if recovered.is_error or recovered.structured_content!={'work':[]} or len(tools)!=7:raise RuntimeError('Export failed discovery/recovery')
                    outcomes.append({'platform':platform,'manifest_launch':True,'tools':len(tools),'recovery':'verified'})
            return outcomes
        try:outcomes=asyncio.run(verify())
        finally:server.shutdown();server.server_close();thread.join()
        print(json.dumps({'passed':True,'synthetic':True,'clean_dependency_cache':args.clean_cache,'exports':outcomes,'host_install_claimed':False},indent=2))

if __name__=='__main__':main()
