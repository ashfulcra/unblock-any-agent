import test from 'node:test';
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { createService } from '../src/lib/server/unblock-api.js';

// External Fulcra processing is represented by accepted and then visible records;
// all authority, sealing, scope, projection and pending/readback logic is real.
function fixture() {
 /** @type {any[]} */ let visible=[];
 /** @type {any[]} */ let accepted=[];
 let offline=false;
 const owner='owner-account';
 const token='header.'+Buffer.from(JSON.stringify({exp:2000})).toString('base64url')+'.signature';
 const service=createService({ownerId:owner,annotation:'MomentAnnotation/11111111-1111-4111-a111-111111111111',key:randomBytes(32).toString('hex'),now:()=>1000,fetch:async(/** @type {string} */ url,/** @type {any} */ options)=>{
   const path=new URL(url).pathname;
   if(path==='/user/v1alpha1/info') return Response.json({userid:options.headers.Authorization==='Bearer '+token ? owner:'foreign'});
   if(offline) return new Response('unavailable',{status:503});
   if(path.startsWith('/data/')) return Response.json(visible);
   if(path==='/ingest/v1/record/MomentAnnotation') {const row=JSON.parse(options.body);if(!accepted.some(x=>x.id===row.id))accepted.push(row);return Response.json({upload_id:'accepted'},{status:201});}
   throw Error('Unexpected upstream path '+path);
 }});
 return {service,token,publish:()=>{visible=[...accepted]},fail:()=>{offline=true}};
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
