import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from unblock.client import Client,private_write,private_read

class PrivateWriteTests(unittest.TestCase):
    def test_interrupted_write_never_publishes_partial_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'grant.json'
            with patch('unblock.client.json.dump',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):private_write(target,{'id':'one'})
            self.assertFalse(target.exists(),'Partial credentials/artifact must not be published')
            self.assertEqual(list(Path(temporary).iterdir()),[])

    def test_publication_does_not_replace_an_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            target=Path(temporary)/'artifact.json'
            private_write(target,{'one':1})
            with self.assertRaises(FileExistsError):private_write(target,{'two':2})
            self.assertEqual(private_read(target),{'one':1})
            self.assertEqual(len(list(Path(temporary).iterdir())),1)

    def test_loopback_credential_never_reaches_configured_proxy(self):
        import os,threading
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        seen=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*_):pass
            def do_GET(self):
                seen.append((self.server.server_port,self.headers.get('Authorization')))
                self.send_response(200);self.end_headers();self.wfile.write(b'{"ok":true}')
        destination=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        proxy=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threads=[threading.Thread(target=server.serve_forever,daemon=True) for server in (destination,proxy)]
        for thread in threads:thread.start()
        try:
            with patch.dict(os.environ,{'http_proxy':f'http://127.0.0.1:{proxy.server_port}','no_proxy':''}),patch('urllib.request.proxy_bypass',return_value=False):
                self.assertEqual(Client(f'http://127.0.0.1:{destination.server_port}','local-secret').call('GET','/api/me'),{'ok':True})
            self.assertEqual(seen,[(destination.server_port,'Bearer local-secret')])
        finally:
            for server in (destination,proxy):server.shutdown();server.server_close()
            for thread in threads:thread.join()

if __name__=='__main__':unittest.main()
