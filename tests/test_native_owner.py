import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import os
import subprocess
import threading
import unittest
from unittest.mock import patch
from unblock.store import DomainError
try:
    from unblock.native_owner import NativeOwner,cli_access_token
except ImportError:
    NativeOwner=None;cli_access_token=None

class NativeOwnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(NativeOwner,'Fixed owner transport is missing')
        self.seen=[];self.mode='normal';test=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):self.handle_request()
            def do_POST(self):self.handle_request()
            def handle_request(self):
                body=self.rfile.read(int(self.headers.get('Content-Length','0')))
                test.seen.append({'path':self.path,'method':self.command,'cookie':self.headers.get('Cookie'),'bearer':self.headers.get('Authorization'),'origin':self.headers.get('Origin'),'body':body})
                if test.mode=='redirect':
                    self.send_response(302);self.send_header('Location',test.url+'/forbidden');self.end_headers();return
                if test.mode=='expired':self.send_response(401);self.end_headers();return
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'kind':'owner','id':'fixture-owner','visibility':'pending'}).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
        self.url=f'http://127.0.0.1:{self.server.server_port}'
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def test_owner_credential_uses_fixed_cookie_and_saved_origin_without_proxy(self):
        client=NativeOwner(self.url,'fixture-secret')
        with patch.dict(os.environ,{'http_proxy':'http://127.0.0.1:1'}):
            self.assertEqual(client.call('identity')['kind'],'owner');client.call('enroll',{'intent_id':'fixed'})
        self.assertEqual([r['path'] for r in self.seen],['/api/unblock/identity','/api/unblock/enroll'])
        self.assertTrue(all(r['cookie']=='fulcra_access_token=fixture-secret' and r['bearer'] is None for r in self.seen))
        self.assertEqual(self.seen[-1]['origin'],self.url);self.assertEqual(json.loads(self.seen[-1]['body']),{'intent_id':'fixed'})
        for operation in ('answer','revoke','progress','https://foreign.invalid'):
            with self.assertRaises(ValueError):client.call(operation,{})
    def test_redirect_and_expired_auth_are_errors_never_forwarded_or_quiet(self):
        client=NativeOwner(self.url,'fixture-secret')
        for mode in ('redirect','expired'):
            self.mode=mode
            with self.assertRaises(DomainError) as error:client.call('attention')
            self.assertNotIn('fixture-secret',str(error.exception))
        self.assertEqual(len(self.seen),2);self.assertTrue(all(r['path']!='/forbidden' for r in self.seen))
    def test_existing_cli_token_is_captured_only_with_fixed_argv(self):
        with patch('shutil.which',return_value='/fixture/fulcra-api'),patch('subprocess.run') as run:
            run.return_value.returncode=0;run.return_value.stdout='fixture-secret\n';run.return_value.stderr=''
            self.assertEqual(cli_access_token(),'fixture-secret')
            self.assertEqual(run.call_args.args[0],['/fixture/fulcra-api','auth','print-access-token'])
            self.assertTrue(run.call_args.kwargs['capture_output'])
            run.return_value.returncode=1;run.return_value.stderr='fixture-secret'
            with self.assertRaises(DomainError) as error:cli_access_token()
            self.assertNotIn('fixture-secret',str(error.exception))

if __name__=='__main__':unittest.main()
