import http.cookiejar
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unblock.store import Store
try:
    from unblock.server import create_server
except ImportError:
    create_server=None

class HttpTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(create_server,'Loopback API is missing')
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'work.db')
        self.owner_grant=self.store.bootstrap_owner('Human'); self.owner=self.store.authenticate(self.owner_grant['token'])
        self.workspace=self.store.create_workspace(self.owner,'Team')['id']
        self.agent_grant=self.store.enroll(self.owner,self.workspace,'Agent','agent','here')
        self.server=create_server(self.store,port=0); self.thread=threading.Thread(target=self.server.serve_forever,daemon=True); self.thread.start()
        self.addCleanup(self.close_server); self.url=f'http://127.0.0.1:{self.server.server_port}'

    def close_server(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def call(self,path,token=None,data=None,headers=None,raw=None,opener=None):
        h={'Content-Type':'application/json',**(headers or {})}
        if token:h['Authorization']='Bearer '+token
        body=raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        req=urllib.request.Request(self.url+path,data=body,headers=h)
        try:
            with (opener.open if opener else urllib.request.urlopen)(req,timeout=3) as response:return response.status,json.load(response),response.headers
        except urllib.error.HTTPError as error:
            with error: return error.code,json.load(error),error.headers

    def test_real_http_loop_and_revocation(self):
        a=self.agent_grant['token'];o=self.owner_grant['token']
        status,work,_=self.call('/api/requests',a,{'key':'http-1','need':'Pick A or B','context':{'goal':'Test pickup'}})
        self.assertEqual(status,201)
        status,response,_=self.call('/api/requests/'+work['id']+'/answers',o,{'revision':work['revision'],'answer':'A','key':'answer-http'})
        self.assertEqual(status,201)
        status,pending,_=self.call('/api/attention',a);self.assertEqual(len(pending),1)
        status,_,_=self.call('/api/requests/'+work['id']+'/progress',a,{'response_id':response['id'],'state':'resumed','evidence':'Applied A and started a safe test'})
        self.assertEqual(status,201)
        recent=self.call('/api/recent',o)
        self.assertEqual(recent[0],200)
        self.assertEqual(recent[1][0]['status'],'resumed')
        self.store.revoke(self.owner,self.agent_grant['id'])
        self.assertEqual(self.call('/api/attention',a)[0],401)

    def test_absent_invalid_and_other_account_credentials(self):
        self.assertEqual(self.call('/api/attention')[0],401)
        self.assertEqual(self.call('/api/attention','made-up')[0],401)
        work=self.store.request_help(self.store.authenticate(self.agent_grant['token']),'private','Need help',{})
        other=self.store.bootstrap_owner('Other')['token']
        self.assertEqual(self.call('/api/requests/'+work['id'],other)[0],404)

    def test_host_origin_and_impersonation_rejected(self):
        a=self.agent_grant['token']
        self.assertEqual(self.call('/api/attention',a,headers={'Host':'evil.example'})[0],403)
        self.assertEqual(self.call('/api/attention',a,headers={'Origin':'https://evil.example'})[0],403)
        self.assertEqual(self.call('/api/requests',a,{'key':'x','need':'Need','context':{},'agent_id':self.owner.id})[0],400)

    def test_malformed_and_oversized_requests_are_bounded(self):
        a=self.agent_grant['token']
        self.assertEqual(self.call('/api/requests',a,raw=b'{bad')[0],400)
        self.assertEqual(self.call('/api/requests',a,raw=b'x'*70000)[0],413)
        self.assertEqual(self.call('/api/requests',a,{'need':'missing key'})[0],400)

    def test_browser_owner_session_and_logout(self):
        jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        status,_,headers=self.call('/api/session',data={'token':self.owner_grant['token']},headers={'Origin':self.url},opener=opener)
        self.assertEqual(status,200)
        self.assertIn('HttpOnly',headers['Set-Cookie']);self.assertIn('SameSite=Strict',headers['Set-Cookie'])
        self.assertEqual(self.call('/api/attention',opener=opener)[0],200)
        self.assertEqual(self.call('/api/logout',data={},opener=opener)[0],403)
        self.assertEqual(self.call('/api/logout',data={},headers={'Origin':self.url},opener=opener)[0],200)
        self.assertEqual(self.call('/api/attention',opener=opener)[0],401)
        self.assertEqual(self.call('/api/session',data={'token':self.agent_grant['token']})[0],403)

    def test_refuse_public_binding_and_path_traversal(self):
        with self.assertRaises(ValueError):create_server(self.store,host='0.0.0.0',port=0)
        with urllib.request.urlopen(self.url,timeout=3) as response:
            self.assertIn('Needs you',response.read().decode())
            self.assertIn("default-src 'self'",response.headers['Content-Security-Policy'])
        try:
            urllib.request.urlopen(self.url+'/../store.py',timeout=3)
            self.fail('Traversal path must fail')
        except urllib.error.HTTPError as error:
            with error: self.assertIn(error.code,(401,404))

if __name__=='__main__':unittest.main()
