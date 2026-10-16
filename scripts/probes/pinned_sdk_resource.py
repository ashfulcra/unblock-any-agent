"""Throwaway no-credential probe against the actual pinned SDK token handler."""
import asyncio,base64,hashlib,json,time
from urllib.parse import urlencode
from starlette.requests import Request
from mcp.server.auth.handlers.token import TokenHandler
from mcp.server.auth.provider import AuthorizationCode,RefreshToken
from mcp.shared.auth import OAuthClientInformationFull,OAuthToken
CLIENT=OAuthClientInformationFull(client_id='probe-client',redirect_uris=['https://client.invalid/callback'],grant_types=['authorization_code','refresh_token'])
VERIFIER='v'*43
CHALLENGE=base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip('=')
RESOURCE='https://dashboard.invalid/mcp'
class Auth:
    async def authenticate_request(self,request):return CLIENT
class Provider:
    def __init__(self):self.calls=[]
    async def load_authorization_code(self,client,code):return AuthorizationCode(code=code,client_id=client.client_id,scopes=['unblock:worker'],expires_at=int(time.time())+60,code_challenge=CHALLENGE,redirect_uri='https://client.invalid/callback',redirect_uri_provided_explicitly=True,resource=RESOURCE)
    async def exchange_authorization_code(self,client,code):
        self.calls.append({'grant':'authorization_code','provider_resource':code.resource})
        return OAuthToken(access_token='synthetic-unused',token_type='Bearer',expires_in=60)
    async def load_refresh_token(self,client,token):return RefreshToken(token=token,client_id=client.client_id,scopes=['unblock:worker'],expires_at=int(time.time())+60)
    async def exchange_refresh_token(self,client,token,scopes):
        self.calls.append({'grant':'refresh_token','provider_resource':None})
        return OAuthToken(access_token='synthetic-unused',token_type='Bearer',expires_in=60)
async def request(handler,form):
    body=urlencode(form).encode()
    async def receive():return {'type':'http.request','body':body,'more_body':False}
    req=Request({'type':'http','method':'POST','path':'/token','headers':[(b'content-type',b'application/x-www-form-urlencoded')],'query_string':b''},receive)
    return await handler.handle(req)
async def main():
    rows=[]
    for grant in ['authorization_code','refresh_token']:
        for resource in [RESOURCE,'https://other.invalid/mcp']:
            p=Provider();h=TokenHandler(p,Auth());form={'grant_type':grant,'client_id':CLIENT.client_id,'resource':resource}
            if grant=='authorization_code':form.update(code='synthetic-code',redirect_uri='https://client.invalid/callback',code_verifier=VERIFIER)
            else:form.update(refresh_token='synthetic-refresh')
            response=await request(h,form)
            rows.append({'grant':grant,'requested_resource_matches':resource==RESOURCE,'http_status':response.status_code,'provider_called':bool(p.calls),'provider_resource':p.calls[0]['provider_resource'] if p.calls else None})
    assert len(rows)==4 and all(r['http_status']==200 and r['provider_called'] for r in rows)
    result={'sdk':'mcp1.28.1','real_handler_exercised':True,'upstream_authentication':False,'production_changes':False,'cases':rows,'conclusion':'Pinned token handler parses resource but neither checks it nor passes requested resource to provider exchange. Explicit resource validation must run before token effects.'}
    print(json.dumps(result,indent=2))
asyncio.run(main())
