"""Narrow native HTTP transport; credentials stay in owned private profiles."""
import argparse
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit, urlencode
import urllib.error
import urllib.request
import uuid

from .client import private_read
from .store import DomainError

READ=('identity','attention','recover')
WRITE=('request','progress','action','settle','delivery')


class NativeClient:
    def __init__(self,url,token):
        parsed=urlsplit(url)
        loopback=parsed.scheme=='http' and parsed.hostname in ('localhost','127.0.0.1','::1')
        if not (parsed.scheme=='https' or loopback) or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:
            raise ValueError('Native profile requires an HTTPS origin or explicit loopback development origin')
        if not isinstance(token,str) or not token or len(token)>20000 or '\n' in token or '\r' in token:
            raise ValueError('Invalid native credential')
        self.url,self.token=url.rstrip('/'),token

    @classmethod
    def from_file(cls,path):
        cfg=private_read(path)
        if cfg.get('transport')!='fulcra-native':raise ValueError('Expected fulcra-native profile')
        return cls(cfg['url'],cfg['token'])

    def call(self,operation,data=None):
        if operation not in READ+WRITE:raise ValueError('Unsupported native agent operation')
        path='/api/unblock/'+operation
        if operation in READ:
            if data:
                if operation!='recover' or set(data)!={'request_id'}:raise ValueError('Unexpected native query')
                rid=str(uuid.UUID(data['request_id']));path+='?'+urlencode({'request_id':rid})
            body=None
        else:
            if not isinstance(data,dict):raise ValueError('Native writes require a JSON object')
            body=json.dumps(data).encode()
            if len(body)>65536:raise ValueError('Native write exceeds request limit')
        request=urllib.request.Request(self.url+path,data=body,method='GET' if operation in READ else 'POST',headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*_):return None
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        try:
            with opener.open(request,timeout=20) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                status=error.code
                if status==401:code='native_enrollment_expired_or_revoked'
                elif status>=500:code='source_unavailable_work_remains_pending'
                elif 300<=status<400:code='native_redirect_refused'
                else:code='native_operation_rejected'
            raise DomainError(code,status) from None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',required=True,help='Owned 0600 native credential profile')
    parser.add_argument('operation',choices=READ+WRITE)
    parser.add_argument('--file',help='JSON input file; writes default to stdin')
    parser.add_argument('--request-id',help='Owned request UUID for recovery')
    args=parser.parse_args()
    try:
        client=NativeClient.from_file(args.config)
        data={'request_id':args.request_id} if args.request_id else None
        if args.operation in WRITE:data=json.loads(Path(args.file).read_text()) if args.file else json.load(sys.stdin)
        print(json.dumps(client.call(args.operation,data),indent=2))
    except (ValueError,KeyError,OSError,DomainError):
        print(json.dumps({'error':'native_operation_failed_check_profile_source_and_pending_work'}),file=sys.stderr)
        raise SystemExit(1) from None

if __name__=='__main__':main()
