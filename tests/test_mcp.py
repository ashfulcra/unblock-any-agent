import asyncio
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unblock.client import private_write
from unblock.server import create_server
from unblock.store import Store
try:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
except ImportError:
    Client=None

@unittest.skipIf(Client is None,'Install requirements-mcp.txt for MCP integration tests')
class MCPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.store=Store(self.root/'work.db')
        self.owner=self.store.authenticate(self.store.bootstrap_owner('Owner')['token'])
        workspace=self.store.create_workspace(self.owner,'Team')['id']
        self.grant=self.store.enroll(self.owner,workspace,'Worker','agent','local')
        self.agent=self.store.authenticate(self.grant['token'])
        self.other=self.store.authenticate(self.store.enroll(self.owner,workspace,'Other','agent','local')['token'])
        self.server=create_server(self.store,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
        self.config=self.root/'agent.json';private_write(self.config,{'url':f'http://127.0.0.1:{self.server.server_port}',**self.grant})
        self.params=StdioServerParameters(command=sys.executable,args=['-m','unblock.mcp_bridge'],env={'UNBLOCK_AGENT_CONFIG':str(self.config)},cwd=str(Path.cwd()))
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def test_real_stdio_discovery_help_and_continuity_progress(self):
        async def scenario():
            async with Client(self.params) as client:
                tools={tool.name for tool in (await client.list_tools()).tools}
                self.assertEqual(tools,{'ask_for_help','recover_work','get_work','revise_need','record_progress','begin_action','reconcile_action'})
                response=await client.call_tool('ask_for_help',{'key':'mcp-need','need':'A or B?','context':{'goal':'Finish pilot','next_action':'Apply decision'}})
                self.assertFalse(response.is_error)
                work=response.structured_content
                self.assertEqual(work['agent_id'],self.agent.id)
                self.assertEqual(self.store.get_request(self.agent,work['id'])['context']['goal'],'Finish pilot')
            # Replacement MCP process can discover the unanswered obligation.
            async with Client(self.params) as replacement:
                recovered=await replacement.call_tool('recover_work',{})
                self.assertEqual(recovered.structured_content['work'][0]['id'],work['id'])
                answer=self.store.answer_request(self.owner,work['id'],work['revision'],'A','answer')
                current=(await replacement.call_tool('get_work',{'request_id':work['id']})).structured_content
                progress=await replacement.call_tool('record_progress',{'request_id':work['id'],'response_id':answer['id'],'answer_revision':current['answer_revision'],'state':'resumed','evidence':'Applied A in synthetic local test'})
                self.assertFalse(progress.is_error)
                self.assertEqual(self.store.get_request(self.agent,work['id'])['status'],'resumed')
        asyncio.run(scenario())
    def test_exported_stdio_runtime_works_outside_the_source_checkout(self):
        from scripts.build_plugins import build
        exported=build(self.root/'exports')
        async def scenario():
            for root in exported.values():
                params=StdioServerParameters(command=sys.executable,args=[str(root/'scripts/run_mcp.py')],env={'UNBLOCK_AGENT_CONFIG':str(self.config)},cwd=str(self.root))
                async with Client(params) as client:
                    result=await client.call_tool('recover_work',{})
                    self.assertFalse(result.is_error)
                    self.assertEqual(result.structured_content,{'work':[]})
        asyncio.run(scenario())

    def test_wrong_request_and_revoked_credentials_remain_errors(self):
        neighbor=self.store.request_help(self.other,'neighbor','Private need',{})
        async def scenario():
            async with Client(self.params) as client:
                for rid in (neighbor['id'],'../../api/enroll'):
                    result=await client.call_tool('get_work',{'request_id':rid})
                    self.assertTrue(result.is_error)
                    self.assertNotIn('Private need',str(result.content))
                self.store.revoke(self.owner,self.agent.id)
                result=await client.call_tool('recover_work',{})
                self.assertTrue(result.is_error)
                self.assertNotIn(self.grant['token'],str(result.content))
        asyncio.run(scenario())

if __name__=='__main__':unittest.main()
