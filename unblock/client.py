"""Local client. Credentials stay in private files, never in a URL."""
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
import urllib.error
import urllib.request

from .store import DomainError


def private_write(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,temporary=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(value,stream,indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        # Publish a complete file atomically, without replacing an existing target.
        os.link(temporary,path)
        directory=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(directory)
        finally:os.close(directory)
    finally:
        os.unlink(temporary)


def private_read(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Private config must be a regular file')
    info=path.stat()
    if info.st_uid!=os.getuid() or info.st_mode&0o077:
        raise ValueError('Private config must be owned by this user and mode 0600')
    return json.loads(path.read_text())


class Client:
    def __init__(self,url,token):
        parsed=urlsplit(url)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost') or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment:
            raise ValueError('Local proof client requires a loopback HTTP origin')
        self.url,self.token=url.rstrip('/'),token

    @classmethod
    def from_file(cls,path):
        cfg=private_read(path)
        return cls(cfg['url'],cfg['token'])

    def call(self,method,path,data=None):
        if not path.startswith('/api/') or '?' in path or '#' in path or '\\' in path:
            raise ValueError('Expected a local API path')
        req=urllib.request.Request(self.url+path,method=method,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*_):
                return None
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(req,timeout=15) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            with error:
                try:
                    code=json.load(error).get('error','http_error')
                except ValueError:
                    code='http_error'
            raise DomainError(code,error.code) from None
