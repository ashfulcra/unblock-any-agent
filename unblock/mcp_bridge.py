"""Agent-bound stdio tools over the local service; no remote auth or wake claim."""
import json
import os
from pathlib import Path
import sys
from typing import Any, Literal
import urllib.error
import uuid

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from .client import Client
from .store import DomainError


def validate_request_id(value):
    try:return str(uuid.UUID(value))
    except (ValueError,TypeError,AttributeError):raise ToolError('invalid_request_id') from None


def build_server(config):
    if not Path(config).is_absolute():raise ValueError('Agent config must be an absolute private file path')
    client=Client.from_file(config)
    if client.call('GET','/api/me')['kind']!='agent':raise ValueError('An agent credential is required')
    server=MCPServer('unblock',version='0.1.0',instructions='Recover existing obligations before creating a duplicate request. A saved answer or dispatch receipt is not proof of resumed work. Use the current answer_revision when recording progress. A separate environment listener or scheduled runtime check is required after this MCP session ends.',log_level='ERROR')

    def call(method,path,data=None):
        try:return client.call(method,path,data)
        except DomainError as error:raise ToolError(error.code) from None
        except (urllib.error.URLError,TimeoutError,OSError):raise ToolError('source_unavailable_work_remains_pending') from None

    read=ToolAnnotations(read_only_hint=True,destructive_hint=False,open_world_hint=False)
    write=ToolAnnotations(read_only_hint=False,destructive_hint=False,open_world_hint=False)

    @server.tool(annotations=write)
    def ask_for_help(key:str,need:str,context:dict[str,Any])->dict[str,Any]:
        """Save one agent-owned need with a stable logical key, goal, context and next action. A human answers in the local dashboard. Retry the identical payload with the same key; revise_need changes its scope."""
        return call('POST','/api/requests',{'key':key,'need':need,'context':context})

    @server.tool(annotations=read)
    def recover_work()->dict[str,Any]:
        """Recover this credential's pending needs, current answers, progress and uncertain actions, including unanswered obligations. An empty successful read differs from a failed source read."""
        return {'work':call('GET','/api/attention')}

    @server.tool(annotations=read)
    def get_work(request_id:str)->dict[str,Any]:
        """Read one owned need, immutable context versions, attributed answers and progress. Review conflicts and uncertain actions before continuing."""
        return call('GET','/api/requests/'+validate_request_id(request_id))

    @server.tool(annotations=write)
    def revise_need(request_id:str,need:str,context:dict[str,Any])->dict[str,Any]:
        """Save changed need/context as a new revision. Earlier answers remain history and cannot authorize this new scope."""
        return call('POST','/api/requests/'+validate_request_id(request_id)+'/revise',{'need':need,'context':context})

    @server.tool(annotations=write)
    def record_progress(request_id:str,response_id:str,answer_revision:str,state:Literal['acknowledged','resumed','completed','blocked'],evidence:str)->dict[str,Any]:
        """Record authenticated worker evidence against the answer set actually reviewed. Acknowledge reading; report resumed only after a concrete authorized next step. New answers invalidate old snapshots. Uncertain actions prevent completion."""
        return call('POST','/api/requests/'+validate_request_id(request_id)+'/progress',{'response_id':response_id,'answer_revision':answer_revision,'state':state,'evidence':evidence})

    @server.tool(annotations=write)
    def begin_action(request_id:str,key:str,description:str)->dict[str,Any]:
        """Persist consequential action intent before acting. A stable key prevents duplicate intent; this does not itself perform the action or grant authority."""
        return call('POST','/api/requests/'+validate_request_id(request_id)+'/actions',{'key':key,'description':description})

    @server.tool(annotations=write)
    def reconcile_action(request_id:str,action_id:str,evidence:str)->dict[str,Any]:
        """Confirm an action only after verifying its actual result. Preserve observed evidence; do not retry an uncertain external action blindly."""
        return call('POST','/api/requests/'+validate_request_id(request_id)+'/settle',{'action_id':action_id,'evidence':evidence})
    return server


def main():
    try:
        config=os.environ.get('UNBLOCK_AGENT_CONFIG')
        if not config:raise ValueError('Set UNBLOCK_AGENT_CONFIG to an absolute private agent config path')
        server=build_server(config)
    except (ValueError,DomainError,OSError,KeyError) as error:
        message=error.code if isinstance(error,DomainError) else 'agent_setup_required'
        print(json.dumps({'error':message}),file=sys.stderr)
        raise SystemExit(1) from None
    server.run(transport='stdio')


if __name__=='__main__':main()
