import test from 'node:test';
import assert from 'node:assert/strict';
import {Client,StreamableHTTPClientTransport} from '@modelcontextprotocol/client';
import {createNativeMcp} from '../src/lib/server/unblock-mcp.js';
import {fixture} from './helpers/native-fixture.js';
import {createService} from '../src/lib/server/unblock-api.js';
import {sealAgent} from '../src/lib/server/unblock-core.js';
const origin='https://pilot.invalid';
/** @param {ReturnType<typeof fixture>} f */
async function enroll(f,id='alpha',kind='agent') {
 const a=await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'enroll-'+id,agent_id:id,name:id,kind,environment:'here',...(kind==='listener'?{agent_ids:['alpha']}: {})}});f.publish();return a;
}
/** @param {import('node:test').TestContext} t @param {ReturnType<typeof createNativeMcp>} h @param {()=>string} token */
async function connect(t,h,token,modern=true) {
 const methods=/** @type {string[]} */([]),client=new Client({name:'http-proof',version:'1'},modern?{versionNegotiation:{mode:'auto'}}:{});
 const transport=new StreamableHTTPClientTransport(new URL(origin+'/mcp'),{fetch:async(url,init)=>{const headers=new Headers(init?.headers);if(token())headers.set('authorization','Bearer '+token());const r=new Request(url,{...init,headers});if(r.method==='POST')methods.push((await r.clone().json()).method);return h.fetch(r);}});
 t.after(async()=>{await client.close();await h.close();});await client.connect(transport);return {client,methods};
}
/** @param {Client} c @param {string} name @param {any} [args] */
const call=(c,name,args={})=>c.callTool({name,arguments:args});
/** @param {any} r @returns {any} */
function data(r){assert.notEqual(r.isError,true,JSON.stringify(r.content));return r.structuredContent;}
const need={key:'http-proof',need:'Choose color',context:'Synthetic context',recommendation:'Blue',next_action:'Verify private marker only'};

test('modern SDK eight-tool loop retains pending/readback, revision and replacement history',async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client:c,methods}=await connect(t,h,()=>a.credential);
 assert.deepEqual((await c.listTools()).tools.map(x=>x.name).sort(),['ask_for_help','recover_work','get_work','revise_need','record_progress','begin_action','reconcile_action','record_work_update'].sort());assert.ok(methods.includes('server/discover'));assert.equal(c.getServerCapabilities()?.tools?.listChanged,false);
 const r=data(await call(c,'ask_for_help',need));assert.equal(r.visibility,'pending');assert.equal(data(await call(c,'recover_work')).requests.length,0);f.publish();assert.equal(data(await call(c,'get_work',{request_id:r.request_id})).agent_id,'alpha');
 assert.equal(data(await call(c,'get_work',{request_id:r.request_id.toUpperCase()})).agent_id,'alpha');
 const revised=data(await call(c,'revise_need',{request_id:r.request_id,parent_revisions:[r.record_id],need:'Updated question',context:'Corrected context',recommendation:'Blue',next_action:'Private marker'}));f.publish();await c.close();
 await f.service.handle('answer',{cookieToken:f.token,body:{intent_id:'answer',request_id:r.request_id,revision:revised.record_id,answer:'Only synthetic blue'}});f.publish();
 const {client:replacement}=await connect(t,h,()=>a.credential);const w=data(await call(replacement,'get_work',{request_id:r.request_id}));assert.equal(w.revisions[0].payload.context,'Corrected context');assert.equal(w.answers.length,1);
 const action=data(await call(replacement,'begin_action',{request_id:r.request_id,key:'marker',description:'Synthetic private marker'}));f.publish();data(await call(replacement,'reconcile_action',{request_id:r.request_id,action_id:action.record_id,evidence:'Fixture readback'}));f.publish();
 data(await call(replacement,'record_progress',{request_id:r.request_id,revision:revised.record_id,answer_ids:w.answers.map((/** @type {any} */ x)=>x.id),stage:'resumed',evidence:'Fixture readback observed'}));f.publish();const final=data(await call(replacement,'recover_work')).requests[0];assert.equal(final.state,'resumed');assert.equal(final.actions.length,1);assert.equal(final.settlements.length,1);
});
test('legacy SDK initialize reaches the same checked worker source',async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client,methods}=await connect(t,h,()=>a.credential,false);assert.ok(methods.includes('initialize'));assert.equal((await client.listTools()).tools.length,8);assert.equal(data(await call(client,'recover_work')).source,'checked');
});
test('cookies, owner tokens, anonymous and listener callers cannot enable worker tools',async()=>{
 const f=fixture(),a=await enroll(f),listener=await enroll(f,'listener','listener'),h=createNativeMcp({service:f.service,origin});
 try {for(const auth of /** @type {Record<string,string>[]} */([{},{cookie:'fulcra_access_token='+f.token},{authorization:'Bearer '+f.token},{authorization:'Bearer '+listener.credential},{authorization:'Basic secret'}])){const r=await h.fetch(new Request(origin+'/mcp',{method:'POST',headers:{'content-type':'application/json',...auth},body:'{}'}));assert.ok([401,403].includes(r.status));}
 const off=createNativeMcp({service:f.service,origin:''});assert.equal((await off.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+a.credential},body:'{}'}))).status,503);await off.close();}finally{await h.close();}
});
test('expiry or revocation after discovery denies the later call',async t=>{
 for(const mode of ['expire','revoke']){const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>a.credential);if(mode==='expire')f.advance(1100);else{await f.service.handle('revoke',{cookieToken:f.token,body:{intent_id:'revoke',grant_id:a.grant_id}});f.publish();}const denied=await h.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+a.credential,'content-type':'application/json'},body:'{}'}));assert.equal(denied.status,401);await assert.rejects(()=>call(client,'recover_work'));}
});
test('changing bearer on one client never reuses the earlier principal or leaks neighbor work',async t=>{
 const f=fixture(),a=await enroll(f),b=await enroll(f,'beta');let token=a.credential;const h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>token);const r=data(await call(client,'ask_for_help',need));f.publish();assert.equal(data(await call(client,'recover_work')).requests.length,1);token=b.credential;const work=data(await call(client,'recover_work'));assert.equal(work.principal.id,'beta');assert.equal(work.requests.length,0);assert.equal((await call(client,'get_work',{request_id:r.request_id})).isError,true);
});
test('source loss after discovery fails reads and writes rather than claiming quiet',async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>a.credential);f.fail();await assert.rejects(()=>call(client,'recover_work'));await assert.rejects(()=>call(client,'ask_for_help',need));
});
test('Host, Origin, methods, bad JSON/content type and streamed oversize fail before dispatch',async()=>{
 let calls=0;const h=createNativeMcp({origin,service:{handle:async()=>{calls++;return {kind:'agent',id:'alpha'};}}});const req=(headers={},body='{}')=>new Request(origin+'/mcp',{method:'POST',headers:{'content-type':'application/json',accept:'application/json, text/event-stream',authorization:'Bearer synthetic',...headers},body});
 try {assert.equal((await h.fetch(req({host:'neighbor.invalid'}))).status,403);assert.equal((await h.fetch(req({origin:'https://neighbor.invalid'}))).status,403);assert.equal((await h.fetch(new Request('https://neighbor.invalid/mcp',{method:'POST',body:'{}'}))).status,403);assert.equal((await h.fetch(new Request(origin+'/mcp'))).status,405);assert.equal(calls,0);
 const stream=new ReadableStream({start(c){c.enqueue(new Uint8Array(40000));c.enqueue(new Uint8Array(40000));c.close();}});assert.equal((await h.fetch(new Request(origin+'/mcp',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer synthetic'},body:stream,...{duplex:'half'}}))).status,413);assert.equal(calls,0);assert.equal((await h.fetch(req({'content-type':'text/plain'}))).status,415);assert.equal((await h.fetch(req({},'{'))).status,400);}finally{await h.close();}
});
test('retry intent matches Python Unicode oracle; schemas reject sender/reference injection without answer cap',async t=>{
 const captured=/** @type {any[]} */([]),service={handle:async(/** @type {string} */ op,/** @type {any} */ input)=>{if(op==='identity')return {kind:'agent',id:'alpha'};captured.push(input.body);return {record_id:'record',visibility:'pending'};}};const h=createNativeMcp({service,origin}),{client}=await connect(t,h,()=> 'synthetic');const args={request_id:'11111111-1111-4111-8111-111111111111',revision:'22222222-2222-4222-8222-222222222222',answer_ids:['33333333-3333-4333-8333-333333333333'],stage:'resumed',evidence:'Checked café 🧭\nline'};
 data(await call(client,'record_progress',args));assert.equal(captured[0].intent_id,'progress-c2d66f360e30e666506e2a749db75b557a99895e4a98cca9bf79a8174b094b0e');data(await call(client,'record_progress',{...args,answer_ids:Array.from({length:101},(_,i)=>`33333333-3333-4333-8333-${String(i).padStart(12,'0')}`)}));assert.equal(captured[1].answers.length,101);const before=captured.length;assert.equal((await call(client,'ask_for_help',{...need,agent_id:'neighbor'})).isError,true);assert.equal(captured.length,before);assert.equal((await call(client,'get_work',{request_id:'not-a-reference'})).isError,true);
});
test('post-ingestion failure preserves pending/uncertain retry guidance',async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>a.credential);f.failAfterWrite();const r=await call(client,'ask_for_help',need);assert.equal(r.isError,true);assert.match(JSON.stringify(r.content),/uncertain|pending|same intent/i);
});

for(const kind of ['network','timeout','json']){
 test(`upstream ${kind} failure during preflight preserves pending work without invalid-token challenge`,async t=>{
  const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin});t.after(()=>h.close());f.sourceFault(kind);
  const r=await h.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+a.credential,'content-type':'application/json'},body:'{}'}));
  assert.equal(r.status,503);assert.equal(r.headers.get('www-authenticate'),null);assert.deepEqual(await r.json(),{error:'source_unavailable_work_remains_pending'});
 });
 test(`upstream ${kind} failure after successful preflight preserves pending tool guidance`,async t=>{
  const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>a.credential);
  f.sourceFault(kind,2);const r=await call(client,'recover_work');assert.equal(r.isError,true);assert.match(JSON.stringify(r.content),/source_unavailable_work_remains_pending/);
 });
}

test('action key accepts the service boundary and rejects an overlong key before dispatch',async t=>{
 const f=fixture(),a=await enroll(f);let actions=0;
 const service={handle:async(/** @type {string} */ op,/** @type {any} */ input)=>{if(op==='action')actions++;return f.service.handle(op,input);}};
 const h=createNativeMcp({service,origin}),{client}=await connect(t,h,()=>a.credential);
 const request=data(await call(client,'ask_for_help',need));f.publish();
 const args={request_id:request.request_id,key:'k'.repeat(160),description:'Boundary-only synthetic action'};
 assert.equal(data(await call(client,'begin_action',args)).visibility,'pending');assert.equal(actions,1);
 assert.equal((await call(client,'begin_action',{...args,key:'k'.repeat(161)})).isError,true);assert.equal(actions,1);
});

for(const modern of [true,false])test(`declared update roundtrip uses checked native recovery (${modern?'modern':'legacy'})`,async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>a.credential,modern);
 const args={key:'review',summary:'Review work',context:'Synthetic context',evidence:'Review began',next_action:'Return report',parent_revisions:[],status:'working',next_update_at:1010,request_id:null};
 const saved=data(await call(client,'record_work_update',args));assert.equal(saved.visibility,'pending');f.publish();
 let work=data(await call(client,'recover_work'));assert.equal(work.expectations.length,1);assert.equal(work.requests.length,0);
 const row=work.expectations[0];data(await call(client,'record_work_update',{...args,parent_revisions:[saved.record_id],status:'completed',next_update_at:null,evidence:'Report checked and returned'}));f.publish();
 work=data(await call(client,'recover_work'));assert.equal(work.expectations[0].state,'completed');assert.equal(work.expectations[0].history.length,2);assert.equal(row.agent_id,'alpha');
});


for(const fault of ['unauthorized','network','timeout','invalid-json']) {
 for(const validity of ['expired','foreign-owner','unexpired']) {
  test(`known sealed validity precedes ${fault} source failure (${validity})`,async()=>{
   const key='a'.repeat(64),clock=1000;
   let sourceCalls=0;
   const credential=sealAgent({agent_id:'alpha',owner_id:validity==='foreign-owner'?'another-account':'owner-account',expires_at:validity==='expired'?clock:clock+100,upstream:'synthetic-upstream',grant_id:'synthetic-grant'},key);
   const service=createService({ownerId:'owner-account',annotation:'MomentAnnotation/11111111-1111-4111-a111-111111111111',key,now:()=>clock,fetch:async()=>{
    sourceCalls++;
    if(fault==='network')throw new TypeError('synthetic network failure');
    if(fault==='timeout')throw new DOMException('synthetic timeout','TimeoutError');
    return new Response(fault==='unauthorized'?'denied':'invalid JSON',{status:fault==='unauthorized'?401:200});
   }});
   const h=createNativeMcp({service,origin});
   try {
    const response=await h.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+credential,'content-type':'application/json'},body:'{}'}));
    assert.equal(response.status,validity==='unexpired'?503:401);
    assert.equal(sourceCalls,validity==='unexpired'?1:0);
    assert.equal((await response.json()).error,validity==='unexpired'?'source_unavailable_work_remains_pending':'native_enrollment_expired_or_revoked');
   } finally {await h.close();}
  });
 }
}
