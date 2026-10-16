import test from 'node:test';
import assert from 'node:assert/strict';
import {Client,StreamableHTTPClientTransport} from '@modelcontextprotocol/client';
import {createNativeMcp} from '../src/lib/server/unblock-mcp.js';
import {fixture} from './helpers/native-fixture.js';
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

test('modern SDK seven-tool loop retains pending/readback, revision and replacement history',async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client:c,methods}=await connect(t,h,()=>a.credential);
 assert.deepEqual((await c.listTools()).tools.map(x=>x.name).sort(),['ask_for_help','recover_work','get_work','revise_need','record_progress','begin_action','reconcile_action'].sort());assert.ok(methods.includes('server/discover'));
 const r=data(await call(c,'ask_for_help',need));assert.equal(r.visibility,'pending');assert.equal(data(await call(c,'recover_work')).requests.length,0);f.publish();assert.equal(data(await call(c,'get_work',{request_id:r.request_id})).agent_id,'alpha');
 const revised=data(await call(c,'revise_need',{request_id:r.request_id,parent_revisions:[r.record_id],need:'Updated question',context:'Corrected context',recommendation:'Blue',next_action:'Private marker'}));f.publish();await c.close();
 await f.service.handle('answer',{cookieToken:f.token,body:{intent_id:'answer',request_id:r.request_id,revision:revised.record_id,answer:'Only synthetic blue'}});f.publish();
 const {client:replacement}=await connect(t,h,()=>a.credential);const w=data(await call(replacement,'get_work',{request_id:r.request_id}));assert.equal(w.revisions[0].payload.context,'Corrected context');assert.equal(w.answers.length,1);
 const action=data(await call(replacement,'begin_action',{request_id:r.request_id,key:'marker',description:'Synthetic private marker'}));f.publish();data(await call(replacement,'reconcile_action',{request_id:r.request_id,action_id:action.record_id,evidence:'Fixture readback'}));f.publish();
 data(await call(replacement,'record_progress',{request_id:r.request_id,revision:revised.record_id,answer_ids:w.answers.map((/** @type {any} */ x)=>x.id),stage:'resumed',evidence:'Fixture readback observed'}));f.publish();const final=data(await call(replacement,'recover_work')).requests[0];assert.equal(final.state,'resumed');assert.equal(final.actions.length,1);assert.equal(final.settlements.length,1);
});
test('legacy SDK initialize reaches the same checked worker source',async t=>{
 const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client,methods}=await connect(t,h,()=>a.credential,false);assert.ok(methods.includes('initialize'));assert.equal((await client.listTools()).tools.length,7);assert.equal(data(await call(client,'recover_work')).source,'checked');
});
test('cookies, owner tokens, anonymous and listener callers cannot enable worker tools',async()=>{
 const f=fixture(),a=await enroll(f),listener=await enroll(f,'listener','listener'),h=createNativeMcp({service:f.service,origin});
 try {for(const auth of /** @type {Record<string,string>[]} */([{},{cookie:'fulcra_access_token='+f.token},{authorization:'Bearer '+f.token},{authorization:'Bearer '+listener.credential},{authorization:'Basic secret'}])){const r=await h.fetch(new Request(origin+'/mcp',{method:'POST',headers:{'content-type':'application/json',...auth},body:'{}'}));assert.ok([401,403].includes(r.status));}
 const off=createNativeMcp({service:f.service,origin:''});assert.equal((await off.fetch(new Request(origin+'/mcp',{method:'POST',headers:{authorization:'Bearer '+a.credential},body:'{}'}))).status,503);await off.close();}finally{await h.close();}
});
test('expiry or revocation after discovery denies the later call',async t=>{
 for(const mode of ['expire','revoke']){const f=fixture(),a=await enroll(f),h=createNativeMcp({service:f.service,origin}),{client}=await connect(t,h,()=>a.credential);if(mode==='expire')f.advance(1100);else{await f.service.handle('revoke',{cookieToken:f.token,body:{intent_id:'revoke',grant_id:a.grant_id}});f.publish();}await assert.rejects(()=>call(client,'recover_work'));}
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
