import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from unblock.client import private_write
from unblock.native_client import NativeClient
from unblock.store import DomainError


class NativeClientTests(unittest.TestCase):
    def setUp(self):
        self.seen=[];self.behavior='normal'
        test=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):
                test.seen.append((self.path,self.headers.get('Authorization')))
                if test.behavior=='redirect':
                    self.send_response(302);self.send_header('Location',test.foreign_url);self.end_headers();return
                status=503 if test.behavior=='offline' else 200
                data=json.dumps({'error':'source unavailable'} if status==503 else {'kind':'agent','id':'alpha','requests':[],'source':'checked'}).encode()
                self.send_response(status);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                test.seen.append((self.path,self.headers.get('Authorization'),body))
                data=json.dumps({'visibility':'pending','record_id':'receipt'}).encode();self.send_response(202);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.origin=f'http://127.0.0.1:{self.server.server_port}';self.client=NativeClient(self.origin,'narrow-fixture-token')
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def test_fixed_native_operations_use_private_profile_and_keep_pending_receipts(self):
        path=Path(self.temp.name)/'agent.json';private_write(path,{'transport':'fulcra-native','url':self.origin,'token':'narrow-fixture-token'})
        client=NativeClient.from_file(path)
        with patch.dict(os.environ,{'http_proxy':'http://127.0.0.1:1','HTTP_PROXY':'http://127.0.0.1:1','no_proxy':'','NO_PROXY':''}):
            self.assertEqual(client.call('identity')['id'],'alpha')
        result=client.call('request',{'intent_id':'stable','need':'help'})
        self.assertEqual(result['visibility'],'pending');self.assertEqual(self.seen[-1],('/api/unblock/request','Bearer narrow-fixture-token',{'intent_id':'stable','need':'help'}))
        with self.assertRaises(ValueError):client.call('answer',{'answer':'not an agent operation'})
        with self.assertRaises(ValueError):client.call('attention?url=https://foreign.invalid')
        with self.assertRaises(ValueError):client.call('recover',{'request_id':'not-a-uuid'})

    def test_redirect_cannot_forward_credential_and_failed_source_cannot_be_quiet(self):
        received=[]
        class Foreign(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):received.append(self.headers.get('Authorization'));self.send_response(200);self.end_headers()
        foreign=ThreadingHTTPServer(('127.0.0.1',0),Foreign);threading.Thread(target=foreign.serve_forever,daemon=True).start();self.addCleanup(foreign.server_close);self.addCleanup(foreign.shutdown)
        self.foreign_url=f'http://127.0.0.1:{foreign.server_port}/steal';self.behavior='redirect'
        with self.assertRaises(DomainError):self.client.call('attention')
        self.assertEqual(received,[])
        self.behavior='offline'
        with self.assertRaises(DomainError) as failure:self.client.call('attention')
        self.assertEqual(failure.exception.code,'source_unavailable_work_remains_pending')

    def test_malformed_origin_or_untrusted_profile_is_rejected_before_network(self):
        for origin in ['http://remote.invalid','https://a.invalid/path','https://u:p@a.invalid','https://a.invalid?x=1','https://a.invalid/#fragment']:
            with self.assertRaises(ValueError):NativeClient(origin,'token')
        path=Path(self.temp.name)/'public.json';path.write_text(json.dumps({'transport':'fulcra-native','url':self.origin,'token':'test'}));path.chmod(0o644)
        with self.assertRaises(ValueError):NativeClient.from_file(path)

if __name__=='__main__':unittest.main()
