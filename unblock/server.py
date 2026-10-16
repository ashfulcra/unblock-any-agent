"""Loopback-only HTTP transport for the local proof."""
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import time
from urllib.parse import urlsplit

from .store import DomainError


STATIC = Path(__file__).parent / 'static'


def create_server(store, host='127.0.0.1', port=8765):
    if host != '127.0.0.1':
        raise ValueError('This proof only binds to 127.0.0.1; production OAuth is not implemented.')
    sessions = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not put credentials or user context into access logs.

        def reply(self, status, value, content_type='application/json', headers=None):
            body = json.dumps(value, allow_nan=False).encode() if content_type=='application/json' else value
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            for key,val in (headers or {}).items():
                self.send_header(key,val)
            self.end_headers()
            self.wfile.write(body)

        def boundary(self):
            expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            host_header=self.headers.get('Host','')
            if host_header not in expected:
                raise DomainError('host_forbidden',403)
            origin=self.headers.get('Origin')
            if origin is not None and origin!='http://'+host_header:
                raise DomainError('origin_forbidden',403)
            return origin

        def actor(self, writing=False):
            auth=self.headers.get('Authorization','')
            if auth.startswith('Bearer '):
                return store.authenticate(auth[7:])
            cookie=SimpleCookie()
            try:
                cookie.load(self.headers.get('Cookie',''))
            except Exception:
                raise DomainError('invalid_session',401) from None
            key=cookie.get('unblock_session')
            session=sessions.get(key.value) if key else None
            if not session or session[1]<time.time():
                raise DomainError('authentication_required',401)
            if writing and self.headers.get('Origin')!='http://'+self.headers.get('Host',''):
                raise DomainError('origin_required',403)
            return store.authenticate(session[0])

        def body(self):
            if self.headers.get_content_type()!='application/json':
                raise DomainError('json_required',415)
            try:
                size=int(self.headers.get('Content-Length','0'))
            except ValueError:
                raise DomainError('invalid_content_length') from None
            if size<0 or size>65536:
                raise DomainError('body_too_large',413)
            try:
                result=json.loads(self.rfile.read(size),parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
            except (ValueError,UnicodeDecodeError):
                raise DomainError('invalid_json') from None
            if not isinstance(result,dict):
                raise DomainError('json_object_required')
            return result

        def fields(self, body, required):
            if set(body)!=set(required):
                raise DomainError('invalid_fields')
            return body

        def do_GET(self):
            try:
                self.boundary()
                path=urlsplit(self.path).path
                assets={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','application/javascript'),'/style.css':('style.css','text/css')}
                if path in assets:
                    filename,mime=assets[path]
                    return self.reply(200,(STATIC/filename).read_bytes(),mime)
                actor=self.actor()
                if path=='/api/me':
                    return self.reply(200,{'id':actor.id,'kind':actor.kind,'workspace_id':actor.workspace_id,'environment':actor.environment})
                if path=='/api/attention':
                    return self.reply(200,store.get_attention(actor))
                if path=='/api/recent':
                    return self.reply(200,store.get_recent(actor))
                parts=path.strip('/').split('/')
                if len(parts)==3 and parts[:2]==['api','requests']:
                    return self.reply(200,store.get_request(actor,parts[2]))
                raise DomainError('not_found',404)
            except DomainError as error:
                self.reply(error.status,{'error':error.code})

        def do_POST(self):
            try:
                self.boundary()
                path=urlsplit(self.path).path
                body=self.body()
                if path=='/api/session':
                    self.fields(body,['token'])
                    actor=store.authenticate(body['token'])
                    if actor.kind!='owner':
                        raise DomainError('owner_session_required',403)
                    now=time.time()
                    for expired in [key for key,value in sessions.items() if value[1]<now]:
                        sessions.pop(expired,None)
                    session=secrets.token_urlsafe(32)
                    sessions[session]=(body['token'],now+3600)
                    return self.reply(200,{'signed_in':True},headers={'Set-Cookie':f'unblock_session={session}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600'})
                actor=self.actor(writing=True)
                if path=='/api/logout':
                    self.fields(body,[])
                    cookie=SimpleCookie(self.headers.get('Cookie',''))
                    if 'unblock_session' in cookie:
                        sessions.pop(cookie['unblock_session'].value,None)
                    return self.reply(200,{'signed_out':True},headers={'Set-Cookie':'unblock_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'})
                if path=='/api/workspaces':
                    self.fields(body,['name'])
                    result=store.create_workspace(actor,**body)
                elif path=='/api/enroll':
                    self.fields(body,['workspace_id','name','kind','environment'])
                    result=store.enroll(actor,**body)
                elif path=='/api/revoke':
                    self.fields(body,['principal_id'])
                    result=store.revoke(actor,**body)
                elif path=='/api/requests':
                    self.fields(body,['key','need','context'])
                    result=store.request_help(actor,**body)
                else:
                    parts=path.strip('/').split('/')
                    if len(parts)!=4 or parts[:2]!=['api','requests']:
                        raise DomainError('not_found',404)
                    rid,operation=parts[2:]
                    methods={
                        'answers':(store.answer_request,['revision','answer','key']),
                        'revise':(store.revise_request,['need','context']),
                        'progress':(store.report_progress,['response_id','state','evidence']),
                        'actions':(store.declare_action,['key','description']),
                        'settle':(store.settle_action,['action_id','evidence']),
                    }
                    if operation not in methods:
                        raise DomainError('not_found',404)
                    method,fields=methods[operation]
                    self.fields(body,fields)
                    result=method(actor,rid,**body)
                self.reply(201,result)
            except DomainError as error:
                self.reply(error.status,{'error':error.code})
            except (TypeError,ValueError,OverflowError):
                self.reply(400,{'error':'invalid_value'})

    server=ThreadingHTTPServer((host,port),Handler)
    server.daemon_threads=True
    return server


def serve(store, host='127.0.0.1', port=8765):
    server=create_server(store,host,port)
    print(f'Unblock local proof: http://127.0.0.1:{server.server_port}',flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
