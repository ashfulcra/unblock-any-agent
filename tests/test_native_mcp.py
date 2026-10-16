import asyncio
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unblock.client import private_write
try:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
except ImportError:Client=None

@unittest.skipIf(Client is None,'Install requirements-mcp.txt for MCP integration tests')
class NativeMCPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.calls=[];self.work=[];self.role='agent';test=self
        self.rid='11111111-1111-4111-a111-111111111111'
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def reply(self,data,status=200):
                body=json.dumps(data).encode();self.send_response(status);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
            def do_GET(self):
                if self.path=='/api/unblock/identity':self.reply({'kind':test.role,'id':'alpha','environment':'pilot'});return
                self.reply({'source':'checked','requests':test.work,'principal':{'kind':test.role,'id':'alpha'}})
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));test.calls.append((self.path,data))
                if self.path=='/api/unblock/request':test.work=[{'id':test.rid,'agent_id':'alpha','state':'needs_you','revisions':[{'id':'revision-a','payload':data}],'answers':[],'actions':[],'settlements':[]}]
                self.reply({'request_id':test.rid,'record_id':'record-a','visibility':'pending'},202)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=self.server.serve_forever,daemon=True).start();self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.config=self.root/'native.json';private_write(self.config,{'transport':'fulcra-native','url':f'http://127.0.0.1:{self.server.server_port}','token':'narrow-fixture-token'})
        self.params=StdioServerParameters(command=sys.executable,args=['scripts/run_mcp.py'],env={'UNBLOCK_AGENT_CONFIG':str(self.config)},cwd=str(Path.cwd()))

    def test_native_stdio_tools_and_replacement_use_native_contract(self):
        async def scenario():
            async with Client(self.params) as client:
                self.assertEqual({t.name for t in (await client.list_tools()).tools},{'ask_for_help','recover_work','get_work','revise_need','record_progress','begin_action','reconcile_action'})
                result=await client.call_tool('ask_for_help',{'key':'stable','need':'Pick color','context':'Synthetic page','recommendation':'Blue','next_action':'Apply and read back'})
                self.assertFalse(result.is_error);self.assertEqual(result.structured_content['visibility'],'pending')
            async with Client(self.params) as replacement:
                result=await replacement.call_tool('recover_work',{});self.assertFalse(result.is_error);self.assertEqual(result.structured_content['requests'][0]['id'],self.rid)
                bad=await replacement.call_tool('get_work',{'request_id':'../../enroll'});self.assertTrue(bad.is_error)
            path,body=self.calls[0];self.assertEqual(path,'/api/unblock/request');self.assertEqual(body['need_key'],'stable');self.assertEqual(body['context'],'Synthetic page');self.assertNotIn('agent_id',body)
        asyncio.run(scenario())

    def test_both_copied_plugin_exports_support_native_profiles(self):
        from scripts.build_plugins import build
        exports=build(self.root/'exports')
        async def scenario():
            for root in exports.values():
                params=StdioServerParameters(command=sys.executable,args=[str(root/'scripts/run_mcp.py')],env={'UNBLOCK_AGENT_CONFIG':str(self.config)},cwd=str(self.root))
                async with Client(params) as client:
                    result=await client.call_tool('recover_work',{});self.assertFalse(result.is_error);self.assertEqual(result.structured_content['requests'],[])
        asyncio.run(scenario())

if __name__=='__main__':unittest.main()
