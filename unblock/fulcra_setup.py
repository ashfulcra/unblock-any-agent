"""Verify a user's existing Fulcra resources and prepare private web configuration."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import uuid

from .client import private_read
from .human_inbox import cli_token, platform_request
from .native_renewal import replace_private
from .store import DomainError

SOURCE=Path(__file__).resolve().parents[1]


def reference(value):
    return str(uuid.UUID(str(value).removeprefix('MomentAnnotation/')))


def safe_path(value):
    path=Path(value)
    if not path.is_absolute() or any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('Use an absolute path without symlinks')
    return path


def private_text(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:
            raise ValueError('Existing configuration must be private, owned and unlinked')
        with os.fdopen(fd,'r') as stream:
            fd=None
            return stream.read()
    finally:
        if fd is not None:os.close(fd)


def write_env(path,text):
    """Create only; retain any prior output and reject conflicting contents."""
    try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    except FileExistsError:
        if private_text(path)!=text:raise ValueError('Existing environment differs; retain it and use another output path')
        return
    with os.fdopen(fd,'w') as stream:
        stream.write(text);stream.flush();os.fsync(stream.fileno())


@contextmanager
def setup_lock(state):
    state.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=state.with_name(state.name+'.lock')
    fd=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode&0o077 or info.st_nlink!=1:
            raise ValueError('Setup lock must be private and owned')
        fcntl.flock(fd,fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)


def configure(project_id,harness_annotation,product_annotation,state_path,env_path,workspace,*,check_only=False,token_provider=cli_token,platform=platform_request):
    project_id,harness,product=map(reference,(project_id,harness_annotation,product_annotation))
    if harness==product:raise ValueError('Use distinct harness and product annotations')
    state,environment=safe_path(state_path),safe_path(env_path)
    if state.is_relative_to(SOURCE) or state==environment or environment==state.with_name(state.name+'.lock'):
        raise ValueError('Keep a separate setup journal outside source')
    if not isinstance(workspace,str) or not re.fullmatch(r'workspace/[A-Za-z0-9][A-Za-z0-9/_-]{0,190}',workspace):
        raise ValueError('Use a workspace/name path')
    token=token_provider()
    user=platform(token,'/user/v1alpha1/info')
    if not isinstance(user,dict):raise ValueError('Current Fulcra owner is unverified')
    owner=reference(user.get('userid'))
    project=platform(token,'/user/v1/deploy/project/'+project_id)
    if not isinstance(project,dict) or project.get('id')!=project_id or not isinstance(project.get('domain'),str) or not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.my\.fulcra\.ai',project['domain']):
        raise ValueError('Owned Fulcra deploy project is unverified')
    annotations=platform(token,'/user/v1alpha1/annotation?fulcra_userid='+owner+'&annotation_type=moment')
    if not isinstance(annotations,list):raise ValueError('Owned annotations are unavailable')
    for ident in (harness,product):
        matches=[x for x in annotations if isinstance(x,dict) and x.get('id')==ident]
        if len(matches)!=1 or matches[0].get('fulcra_userid')!=owner or matches[0].get('annotation_type')!='moment' or matches[0].get('fulcra_source_id')!='com.fulcradynamics.annotation.'+ident or 'deleted_at' not in matches[0] or matches[0]['deleted_at'] is not None:
            raise ValueError('Use distinct active annotations owned by the current account')
    origin='https://'+project['domain']
    binding={'owner_id':owner,'project_id':project_id,'origin':origin,'harness_annotation':harness,'product_annotation':product,'workspace':workspace,'env_path':str(environment)}
    result={'origin':origin,'project_id':project_id,'environment':str(environment),'state':str(state),'check_only':check_only}

    def existing_state():
        value=private_read(state)
        if value.get('binding')!=binding or value.get('version')!=1 or not re.fullmatch(r'[0-9a-f]{64}',value.get('agent_key','')):
            raise ValueError('Setup journal belongs to different account/resources or is invalid')
        return value

    if check_only:
        if state.exists():existing_state()
        return result
    with setup_lock(state):
        # Recheck after acquiring the cross-process lock.
        safe_path(state);safe_path(environment)
        if state.exists():journal=existing_state()
        else:
            if environment.exists():
                private_text(environment)
                raise ValueError('Existing environment has no matching setup journal; retain it')
            journal={'version':1,'binding':binding,'agent_key':secrets.token_hex(32)}
            replace_private(state,journal)
        fields={'OWNER_USER_ID':owner,'PUBLIC_HARNESS_ANNOTATION_ID':'MomentAnnotation/'+harness,'PUBLIC_WORKSPACE_PATH':workspace,'UNBLOCK_ANNOTATION_ID':'MomentAnnotation/'+product,'UNBLOCK_AGENT_KEY':journal['agent_key'],'UNBLOCK_MCP_ORIGIN':origin}
        template=(SOURCE/'web/.env.example').read_text()
        output='\n'.join(key+'='+json.dumps(fields[key]) if (key:=line.partition('=')[0]) in fields else line for line in template.splitlines())+'\n'
        write_env(environment,output)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-id',required=True)
    parser.add_argument('--harness-annotation',required=True)
    parser.add_argument('--product-annotation',required=True)
    parser.add_argument('--state',required=True,help='Absolute private journal outside source; retain it on retry')
    parser.add_argument('--env-file',required=True,help='Absolute create-only private environment output')
    parser.add_argument('--workspace',default='workspace/unblock-any-agent')
    parser.add_argument('--check',action='store_true',help='Read-only live resource verification; write no configuration')
    args=parser.parse_args()
    try:
        result=configure(args.project_id,args.harness_annotation,args.product_annotation,args.state,args.env_file,args.workspace,check_only=args.check)
        print(json.dumps(result,indent=2))
    except (ValueError,OSError,DomainError):
        print('Setup not applied: check the current Fulcra account, owned resources and private paths; existing state is retained.',file=sys.stderr)
        raise SystemExit(1) from None

if __name__=='__main__':main()
