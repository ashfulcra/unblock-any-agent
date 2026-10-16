"""Explicit trusted-operator transport. Never exported to worker plugins."""
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from .native_client import NativeClient
from .store import DomainError

READ=('identity','attention','prepare_enrollment')


def cli_access_token():
    executable=shutil.which('fulcra-api')
    if not executable:raise DomainError('owner_cli_unavailable_reconnect_operator',503)
    try:result=subprocess.run([executable,'auth','print-access-token'],capture_output=True,text=True,timeout=30)
    except (OSError,subprocess.TimeoutExpired):raise DomainError('owner_cli_unavailable_reconnect_operator',503) from None
    token=result.stdout.strip()
    if result.returncode or not 1<=len(token)<=20000 or not re.fullmatch(r'[A-Za-z0-9_.-]+',token):raise DomainError('owner_cli_auth_failed_reconnect_operator',401)
    return token


class NativeOwner(NativeClient):
    def __init__(self,url,token):
        super().__init__(url,token)
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',token):raise ValueError('Invalid owner token')

    def call(self,operation,data=None):
        if operation not in (*READ,'enroll'):raise ValueError('Unsupported owner renewal operation')
        if operation in READ:
            if data is not None:raise ValueError('Owner reads do not accept query input')
            body=None
        else:
            if not isinstance(data,dict):raise ValueError('Enrollment requires a JSON object')
            body=json.dumps(data).encode()
            if len(body)>65536:raise ValueError('Enrollment exceeds request limit')
        request=urllib.request.Request(self.url+'/api/unblock/'+operation,data=body,method='GET' if body is None else 'POST',headers={'Cookie':'fulcra_access_token='+self.token,'Origin':self.url,'Content-Type':'application/json'})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*_):return None
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        try:
            with opener.open(request,timeout=20) as response:
                payload=response.read(4*1024*1024+1)
                if len(payload)>4*1024*1024:raise DomainError('owner_source_too_large_pending_retained',503)
                return json.loads(payload)
        except urllib.error.HTTPError as error:
            with error:status=error.code
            code='owner_auth_failed_reconnect_operator' if status==401 else 'owner_source_unavailable_pending_retained' if status>=500 else 'owner_redirect_refused' if 300<=status<400 else 'owner_operation_rejected'
            raise DomainError(code,status) from None
        except (ValueError,UnicodeError):raise DomainError('owner_source_invalid_pending_retained',503) from None
