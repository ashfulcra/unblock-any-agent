import test from 'node:test';
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { createService } from '../src/lib/server/unblock-api.js';

// External Fulcra processing is represented by accepted and then visible records;
// all authority, sealing, scope, projection and pending/readback logic is real.
function fixture(expires=2000) {
 let clock=1000;
 /** @type {any[]} */ let visible=[];
 /** @type {any[]} */ let accepted=[];
 let offline=false,failAfterWrite=false;
 const owner='owner-account';
 const token='header.'+Buffer.from(JSON.stringify({exp:expires})).toString('base64url')+'.signature';
 const service=createService({ownerId:owner,annotation:'MomentAnnotation/11111111-1111-4111-a111-111111111111',key:randomBytes(32).toString('hex'),now:()=>clock,fetch:async(/** @type {string} */ url,/** @type {any} */ options)=>{
   const path=new URL(url).pathname;
   if(path==='/user/v1alpha1/info') return Response.json({userid:options.headers.Authorization==='Bearer '+token ? owner:'foreign'});
   if(offline) return new Response('unavailable',{status:503});
   if(path.startsWith('/data/')) return Response.json(visible);
   if(path==='/ingest/v1/record/MomentAnnotation') {const row=JSON.parse(options.body);if(!accepted.some(x=>x.id===row.id))accepted.push(row);if(failAfterWrite)offline=true;return Response.json({upload_id:'accepted'},{status:201});}
   throw Error('Unexpected upstream path '+path);
 }});
 return {service,token,corrupt:(/** @type {string} */ note)=>{visible=[{id:"bad",note}]},failAfterWrite:()=>{failAfterWrite=true},advance:(/** @type {number} */ seconds)=>{clock+=seconds},publish:()=>{visible=[...accepted]},fail:()=>{offline=true}};
}
const need={intent_id:'i1',need_key:'color',need:'Choose color',context:'Page work',recommendation:'Blue',next_action:'Apply color',parents:[]};

test('real native operation flow preserves pending receipt, scoped recovery and human attribution',async()=>{
 const f=fixture(),call=(/** @type {string} */ op,/** @type {any} */ body,cookie=f.token,token='')=>f.service.handle(op,{body,cookieToken:cookie,token});
 const a=await call('enroll',{intent_id:'enroll-a',agent_id:'alpha',name:'Alpha'});assert.equal(a.visibility,'pending');f.publish();
 const b=await call('enroll',{intent_id:'enroll-b',agent_id:'beta',name:'Beta'});f.publish();
 const created=await call('request',need,'',a.credential);assert.equal(created.visibility,'pending');f.publish();
 const recovery=await call('attention',{},'',a.credential);assert.equal(recovery.requests.length,1);assert.equal(recovery.requests[0].state,'needs_you');
 assert.equal((await call('attention',{},'',b.credential)).requests.length,0);
 const id=created.request_id,rev=created.record_id;
 await assert.rejects(()=>call('answer',{request_id:id,intent_id:'forged',revision:rev,answer:'Blue'},'',a.credential));
 await call('answer',{request_id:id,intent_id:'answer',revision:rev,answer:'Blue'});f.publish();
 const answered=(await call('recover',{request_id:id},'',a.credential)).requests[0];assert.equal(answered.answers[0].payload.responder,'owner-account');assert.equal(answered.state,'awaiting_pickup');
 await assert.rejects(()=>call('recover',{request_id:id},'',b.credential));
 await call('progress',{request_id:id,intent_id:'next',revision:rev,answers:answered.answers.map((/** @type {any} */ x)=>x.id),stage:'resumed',evidence:'Applied and read back marker'},'',a.credential);f.publish();
 assert.equal((await call('attention',{})).requests[0].state,'resumed');
 await call('revoke',{intent_id:'revoke-a',agent_id:'alpha',grant_id:a.grant_id});f.publish();
 await assert.rejects(()=>call('attention',{},'',a.credential));
});
test('read failures and unrelated accounts deny access instead of returning quiet',async()=>{
 const f=fixture();await assert.rejects(()=>f.service.handle('attention',{cookieToken:'foreign',body:{}}));f.fail();await assert.rejects(()=>f.service.handle('attention',{cookieToken:f.token,body:{}}));
});
test('agent cannot forge another agent on creation or alter a neighboring request',async()=>{
 const f=fixture(),owner=(/** @type {string} */ op,/** @type {any} */ body)=>f.service.handle(op,{cookieToken:f.token,body});
 const a=await owner('enroll',{intent_id:'a',agent_id:'alpha',name:'Alpha'});f.publish();const b=await owner('enroll',{intent_id:'b',agent_id:'beta',name:'Beta'});f.publish();
 const req=await f.service.handle('request',{token:a.credential,body:{...need,agent_id:'beta'}});f.publish();
 assert.equal((await owner('attention',{})).requests[0].agent_id,'alpha');
 await assert.rejects(()=>f.service.handle('progress',{token:b.credential,body:{request_id:req.request_id,intent_id:'steal',revision:req.record_id,answers:[],stage:'resumed',evidence:'no'}}));
});

test('settlement retries succeed after readback and preserve changed evidence variants',async()=>{
 const f=fixture();const e=await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'a',agent_id:'alpha',name:'Alpha'}});f.publish();
 const agent=(/** @type {string} */ op,/** @type {any} */ body)=>f.service.handle(op,{token:e.credential,body});
 const req=await agent('request',need);f.publish();const action=await agent('action',{intent_id:'act',request_id:req.request_id,effect:'Synthetic marker'});f.publish();
 const body={intent_id:'settled',request_id:req.request_id,action:action.record_id,evidence:'Observed marker hash'};
 const first=await agent('settle',body);f.publish();const retry=await agent('settle',body);assert.equal(retry.record_id,first.record_id);f.publish();
 assert.equal((await agent('attention',{})).requests[0].settlements.length,1);
 await agent('settle',{...body,evidence:'Additional observed evidence'});f.publish();assert.equal((await agent('attention',{})).requests[0].settlements.length,2);
});

test('enrollment retries use one stable expiry before and after ingestion visibility',async()=>{
 const f=fixture(20000),body={intent_id:'stable-enrollment',agent_id:'alpha',name:'Alpha',expires_at:4300};
 const enroll=()=>f.service.handle('enroll',{cookieToken:f.token,body});
 const first=await enroll();f.advance(10);const pendingRetry=await enroll();
 assert.equal(first.record_id,pendingRetry.record_id);assert.equal(first.expires_at,4300);f.publish();f.advance(10);const visibleRetry=await enroll();assert.equal(visibleRetry.record_id,first.record_id);
 assert.equal((await f.service.handle('attention',{cookieToken:f.token,body:{}})).grants.length,1);
 await assert.rejects(()=>f.service.handle('enroll',{cookieToken:f.token,body:{...body,intent_id:'bad',expires_at:999999}}));
});

test('recorded progress retries remain historical after answers or question revisions change',async()=>{
 const f=fixture();const owner=(/** @type {string} */ op,/** @type {any} */ body)=>f.service.handle(op,{cookieToken:f.token,body});
 const e=await owner('enroll',{intent_id:'a',agent_id:'alpha',name:'Alpha'});f.publish();
 const agent=(/** @type {string} */ op,/** @type {any} */ body)=>f.service.handle(op,{token:e.credential,body});
 const req=await agent('request',need);f.publish();const firstAnswer=await owner('answer',{intent_id:'answer-a',request_id:req.request_id,revision:req.record_id,answer:'Blue'});f.publish();
 const body={intent_id:'progress-a',request_id:req.request_id,revision:req.record_id,answers:[firstAnswer.record_id],stage:'resumed',evidence:'Observed blue marker'};
 const progress=await agent('progress',body);f.publish();
 await owner('answer',{intent_id:'answer-b',request_id:req.request_id,revision:req.record_id,answer:'Red'});f.publish();
 assert.equal((await agent('progress',body)).record_id,progress.record_id);assert.equal((await agent('attention',{})).requests[0].state,'answer_conflict');
 await assert.rejects(()=>agent('progress',{...body,intent_id:'new-stale-progress'}));
 await agent('request',{...need,intent_id:'new-question',context:'Changed question',parents:[req.record_id]});f.publish();
 assert.equal((await agent('progress',body)).record_id,progress.record_id);assert.equal((await agent('attention',{})).requests[0].state,'needs_you');
});

test('a lost readback after ingestion is an uncertain write rather than a definite rejection',async()=>{
 const f=fixture();const e=await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'a',agent_id:'alpha',name:'Alpha'}});f.publish();f.failAfterWrite();
 await assert.rejects(()=>f.service.handle('request',{token:e.credential,body:need}),(/** @type {any} */ error)=>error.publication_uncertain===true);
});

test('listener identity is environment-scoped and can only read its explicit agent set',async()=>{
 const f=fixture();const owner=(/** @type {string} */ op,/** @type {any} */ body)=>f.service.handle(op,{cookieToken:f.token,body});
 const alpha=await owner('enroll',{intent_id:'alpha',agent_id:'alpha',name:'Alpha'});f.publish();
 const beta=await owner('enroll',{intent_id:'beta',agent_id:'beta',name:'Beta'});f.publish();
 const a=await f.service.handle('request',{token:alpha.credential,body:need});f.publish();
 const b=await f.service.handle('request',{token:beta.credential,body:{...need,intent_id:'other'}});f.publish();
 const listener=await owner('enroll',{intent_id:'listener',agent_id:'local-listener',name:'Local listener',kind:'listener',environment:'machine-one',agent_ids:['alpha']});f.publish();
 const call=(/** @type {string} */ op,/** @type {any} */ body={})=>f.service.handle(op,{token:listener.credential,body});
 const who=await call('identity');assert.equal(who.kind,'listener');assert.equal(who.environment,'machine-one');assert.deepEqual(who.agent_ids,['alpha']);
 const attention=await call('attention');assert.equal(attention.requests.length,1);assert.equal(attention.requests[0].id,a.request_id);assert.equal(attention.principal.kind,'listener');
 await assert.rejects(()=>call('recover',{request_id:b.request_id}));
 for(const op of ['request','progress','answer','action','settle','enroll','revoke'])await assert.rejects(()=>call(op,{...need,intent_id:'forbidden',request_id:a.request_id}),/Listener/);
 await owner('revoke',{intent_id:'revoke-listener',grant_id:listener.grant_id});f.publish();await assert.rejects(()=>call('identity'));
});

test('listener delivery receipts are scoped observations and never become agent progress',async()=>{
 const f=fixture();const owner=(/** @type {string} */ op,/** @type {any} */ body)=>f.service.handle(op,{cookieToken:f.token,body});
 const alpha=await owner('enroll',{intent_id:'a',agent_id:'alpha',name:'Alpha'});f.publish();
 const request=await f.service.handle('request',{token:alpha.credential,body:need});f.publish();
 const listener=await owner('enroll',{intent_id:'l',agent_id:'listener',name:'Listener',kind:'listener',environment:'env',agent_ids:['alpha']});f.publish();
 const body={intent_id:'delivery-attempt',request_id:request.request_id,revision:request.record_id,answers:[],disposition:'queued',evidence:'Trusted local launcher returned zero; no agent progress asserted'};
 await f.service.handle('delivery',{token:listener.credential,body});f.publish();
 const work=(await owner('attention',{})).requests[0];assert.equal(work.state,'needs_you');assert.equal(work.progress.length,0);assert.equal(work.deliveries[0].payload.receiver,'listener');assert.equal(work.deliveries[0].payload.environment,'env');
 await assert.rejects(()=>f.service.handle('delivery',{token:alpha.credential,body}));
 await assert.rejects(()=>f.service.handle('delivery',{token:listener.credential,body:{...body,request_id:'foreign'}}));
});

test('malformed native source is sanitized as unavailable rather than user input rejection',async()=>{
 const f=fixture();f.corrupt('private-source-fragment');
 await assert.rejects(()=>f.service.handle('attention',{cookieToken:f.token}),error=>error instanceof Error && error.message.includes('unavailable') && !error.message.includes('private-source-fragment'));
});
