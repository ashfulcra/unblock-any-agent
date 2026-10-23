"""Agent-bound stdio tools for the deployed native Fulcra pilot."""
import hashlib
import json
from pathlib import Path
from typing import Any, Literal
import urllib.error
import uuid

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from .native_client import NativeClient
from .store import DomainError


def reference(value):
    try:return str(uuid.UUID(value))
    except (ValueError,TypeError,AttributeError):raise ToolError('invalid_request_or_revision') from None


def intent(label,payload):
    return label+'-'+hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def build_server(config):
    if not Path(config).is_absolute():raise ValueError('Native config must be an absolute private file path')
    client=NativeClient.from_file(config)
    if client.call('identity')['kind']!='agent':raise ValueError('A worker agent credential is required; listener credentials are read-only')
    server=MCPServer('unblock',version='0.5.1',instructions='This profile uses native Fulcra persistence. Recover current work before making requests or acting. Native writes may return pending: verify the exact record in recovery before claiming visibility. Question revision and complete answer IDs must be those actually reviewed; stale progress remains historical. Reconcile known actions before repeating them. Credentials expire with the originating session; renewal requires a separately configured trusted owner operator or owner reconnection. This MCP process does not start or acquire owner authentication. A separate environment listener or host tick is required after this MCP session ends.',log_level='ERROR')
    read=ToolAnnotations(read_only_hint=True,destructive_hint=False,open_world_hint=False)
    write=ToolAnnotations(read_only_hint=False,destructive_hint=False,open_world_hint=False)

    def call(operation,data=None):
        try:return client.call(operation,data)
        except DomainError as error:raise ToolError(error.code) from None
        except ValueError:raise ToolError('invalid_native_request_check_current_work') from None
        except (urllib.error.URLError,TimeoutError,OSError):raise ToolError('source_unavailable_work_remains_pending') from None

    @server.tool(annotations=write)
    def ask_for_help(key:str,need:str,context:str,recommendation:str,next_action:str)->dict[str,Any]:
        """Save an agent-owned need with useful context and a stable need key. Repeat identical fields on retry; changed fields retain a conflicting variant. A pending receipt is not persisted/answered/resumed proof."""
        return call('request',{'intent_id':key,'need_key':key,'need':need,'context':context,'recommendation':recommendation,'next_action':next_action,'parents':[]})

    @server.tool(annotations=read)
    def recover_work()->dict[str,Any]:
        """Read owned requests, answers, corrected context, action evidence, expected updates and missed-update investigations. A failed source remains unknown."""
        return call('attention')

    @server.tool(annotations=write)
    def record_work_update(key:str,summary:str,context:str,evidence:str,next_action:str,parent_revisions:list[str],status:Literal['working','completed','cancelled'],next_update_at:int|None,request_id:str|None=None)->dict[str,Any]:
        """Declare or update expected work without inventing a human need. Working needs a future Unix-second deadline; terminal states need null. Review explicit current parent revisions and retain conflicts. Completion closes this expectation only, never a linked question or uncertain action. Independent detection needs a separate scoped monitor."""
        payload={'work_key':key,'summary':summary,'context':context,'evidence':evidence,'next_action':next_action,'parents':sorted(reference(r) for r in parent_revisions),'status':status,'next_update_at':next_update_at,'request_id':reference(request_id) if request_id is not None else None}
        return call('work_update',{'intent_id':intent('work-update',payload),**payload})

    @server.tool(annotations=read)
    def get_work(request_id:str)->dict[str,Any]:
        """Recover one owned need and its retained history; request/revision/action IDs are immutable UUID references."""
        return call('recover',{'request_id':reference(request_id)})['requests'][0]

    @server.tool(annotations=write)
    def revise_need(request_id:str,parent_revisions:list[str],need:str,context:str,recommendation:str,next_action:str)->dict[str,Any]:
        """Save corrected context against the exact parent revisions actually reviewed. Concurrent unreviewed revisions remain conflicts; this does not silently select the latest question."""
        work=call('recover',{'request_id':reference(request_id)})['requests'][0]
        payload={'need_key':work['revisions'][0]['payload']['need_key'],'need':need,'context':context,'recommendation':recommendation,'next_action':next_action,'parents':sorted(reference(r) for r in parent_revisions)}
        return call('request',{'intent_id':intent('revise',payload),**payload})

    @server.tool(annotations=write)
    def record_progress(request_id:str,revision:str,answer_ids:list[str],stage:Literal['acknowledged','resumed','completed','withdrawn'],evidence:str,reconciled:bool=False)->dict[str,Any]:
        """Report observed work using the exact reviewed question and complete current answer set. Withdraw an obsolete own request with evidence when no human action is needed; only withdrawn permits zero answers and it cannot conceal uncertain effects. Set reconciled only after actually resolving multiple answers. New answers invalidate older snapshots; already-recorded retries stay historical."""
        payload={'request_id':reference(request_id),'revision':reference(revision),'answers':sorted(reference(a) for a in answer_ids),'stage':stage,'evidence':evidence,'reconciled':reconciled}
        return call('progress',{'intent_id':intent('progress',payload),**payload})

    @server.tool(annotations=write)
    def begin_action(request_id:str,key:str,description:str)->dict[str,Any]:
        """Retain a stable consequential-action intent before acting. Wait for its actual readback; this does not execute the action or grant authority."""
        return call('action',{'request_id':reference(request_id),'intent_id':key,'effect':description})

    @server.tool(annotations=write)
    def reconcile_action(request_id:str,action_id:str,evidence:str)->dict[str,Any]:
        """Record an actual checked action result. Known settled history remains available to replacements; never repeat an uncertain external action blindly."""
        payload={'request_id':reference(request_id),'action':reference(action_id),'evidence':evidence}
        return call('settle',{'intent_id':intent('settle',payload),**payload})
    return server
