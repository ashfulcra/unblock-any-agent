import asyncio
from pathlib import Path
import sys
import unittest

try:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
except ImportError:Client=None


FIXTURE='''
from unblock.human_mcp import build_server
class Inbox:
 def inbox(self,*args):return {'source':'checked','checked_at':'2026-10-19T12:00:00Z','counts':{'needs_you':1,'with_agents':0,'done':0},'pending_answers':[],'items':[{'request_id':'11111111-1111-4111-a111-111111111111','agent_id':'alpha','agent_name':'Alpha designer','created_at':'2026-10-17T12:00:00Z','state':'needs_you','decision':'Pick the preview label','context':'Synthetic UX fixture'}]}
 def get_decision(self,rid):return {'source':'checked','agent_name':'Alpha designer','reviewed_snapshot':'0'*64,'can_answer':True,'request':{'id':rid,'created_at':None,'state':'needs_you','revisions':[{'id':'22222222-2222-4222-a222-222222222222','payload':{'need':'Pick the preview label','context':'Synthetic UX fixture','recommendation':'Mint','next_action':'Read marker'}}],'answers':[],'uncertain_actions':[]}}
 def answer_decision(self,*args):return {'visibility':'visible','progress':'awaiting_pickup','current_question':True,'intent_id':args[-1]}
 def get_work_update(self,eid):return {'source':'checked','agent_name':'Alpha designer','expectation':{'id':eid,'state':'due','revisions':[{'payload':{'summary':'Deliver the inbox','evidence':'Missing work visibility reproduced','next_action':'Inspect the installed panel','status':'working','next_update_at':1792669200}}],'history':[],'observations':[]}}
build_server('/not-used',client=Inbox()).run(transport='stdio')
'''


@unittest.skipIf(Client is None,'Install requirements-mcp.txt for MCP integration tests')
class HumanMCPTests(unittest.TestCase):
    def test_human_tools_resource_and_text_fallback_have_no_worker_mutations(self):
        async def scenario():
            params=StdioServerParameters(command=sys.executable,args=['-c',FIXTURE],cwd=str(Path.cwd()))
            async with Client(params) as client:
                tools=(await client.list_tools()).tools
                self.assertEqual({t.name for t in tools},{'show_inbox','get_decision','answer_decision','get_work_update'})
                shown=next(t for t in tools if t.name=='show_inbox')
                self.assertTrue(shown.meta['ui']['resourceUri'].startswith('ui://unblock/'))
                self.assertEqual(shown.meta['openai/ui']['entrypoints'],[{'type':'global'},{'type':'thread'}])
                result=await client.call_tool('show_inbox',{})
                self.assertFalse(result.is_error);self.assertIn('Alpha designer',result.content[0].text)
                self.assertIn('Synthetic UX fixture',result.content[0].text)
                self.assertEqual(result.structured_content['source'],'checked')
                resource=await client.read_resource(shown.meta['ui']['resourceUri'])
                self.assertEqual(resource.contents[0].mime_type,'text/html;profile=mcp-app')
                self.assertIn('ui/initialize',resource.contents[0].text)
                self.assertIn('answer_decision',resource.contents[0].text)
                self.assertNotIn('fulcra_access_token',resource.contents[0].text)
                self.assertNotIn('fetch(',resource.contents[0].text)
                work=await client.call_tool('get_work_update',{'expectation_id':'11111111-1111-4111-a111-111111111111'})
                self.assertIn('Missing work visibility reproduced',work.content[0].text)
                self.assertIn('Inspect the installed panel',work.content[0].text)
                self.assertEqual(work.structured_content['expectation']['state'],'due')
                self.assertTrue(next(t for t in tools if t.name=='get_work_update').annotations.read_only_hint)
                decision=await client.call_tool('get_decision',{'request_id':'11111111-1111-4111-a111-111111111111'})
                self.assertIn('Recommendation: Mint',decision.content[0].text)
                answer=await client.call_tool('answer_decision',{'request_id':'11111111-1111-4111-a111-111111111111','revision':'22222222-2222-4222-a222-222222222222','reviewed_snapshot':'0'*64,'answer':'Use mint for the synthetic fixture','intent_id':'test-stable'})
                self.assertFalse(answer.is_error);self.assertIn('not proof',answer.content[0].text)
        asyncio.run(scenario())


if __name__=='__main__':unittest.main()
