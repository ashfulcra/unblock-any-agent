import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from './helpers/native-fixture.js';
import {canonicalRecord,stableId} from '../src/lib/server/unblock-core.js';

test('renewal projection returns exact historical and pending grants beside large work history',async()=>{
 const f=fixture();
 const owner=(/** @type {string} */ op,/** @type {any} */ body={})=>f.service.handle(op,{cookieToken:f.token,body});
 const a=await owner('enroll',{intent_id:'original-a',agent_id:'alpha',name:'Alpha'});f.publish();
 const other=await owner('enroll',{intent_id:'original-b',agent_id:'beta',name:'Beta'});f.publish();
 const next=await owner('enroll',{intent_id:'pending-a',agent_id:'alpha',name:'Alpha',renewal_of:a.grant_id});f.publish();
 const text='x'.repeat(4000);
 f.seedEvents(Array.from({length:200},(_,i)=>canonicalRecord({
  schema:'unblock/1',intent_id:'large-'+i,kind:'request',agent_id:'alpha',
  request_id:stableId('large-'+i),
  payload:{need_key:'large-'+i,need:text,context:text,recommendation:text,next_action:text,parents:[]}
 })));
 const full=await owner('attention');
 assert.ok(Buffer.byteLength(JSON.stringify(full))>4*1024*1024);
 const selected=await owner('attention',{view:'renewal',grant_ids:[a.grant_id,next.grant_id]});
 assert.equal(selected.source,'checked');assert.equal(selected.principal.kind,'owner');
 assert.deepEqual(selected.grants.map((/** @type {any} */ g)=>g.grant_id).sort(),[a.grant_id,next.grant_id].sort());
 assert.deepEqual(selected.grants,full.grants.filter((/** @type {any} */ g)=>g.grant_id!==other.grant_id));
 assert.equal(selected.requests,undefined);assert.equal(selected.expectations,undefined);
 assert.ok(Buffer.byteLength(JSON.stringify(selected))<10000);
 await owner('revoke',{intent_id:'revoke-original',grant_id:a.grant_id});f.publish();
 const revoked=await owner('attention',{view:'renewal',grant_ids:[next.grant_id]});
 assert.equal(revoked.grants.length,1);assert.equal(revoked.grants[0].revoked,true);
});

test('renewal projection requires owner and bounded exact selectors and checked source',async()=>{
 const f=fixture(),owner=(/** @type {any} */ body)=>f.service.handle('attention',{cookieToken:f.token,body});
 const a=await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'original',agent_id:'alpha',name:'Alpha'}});f.publish();
 const body={view:'renewal',grant_ids:[a.grant_id]};
 await assert.rejects(()=>f.service.handle('attention',{token:a.credential,body}),/Owner/);
 for(const bad of [
  {...body,view:'other'}, {...body,grant_ids:[]}, {...body,grant_ids:[a.grant_id,a.grant_id]},
  {...body,grant_ids:Array(61).fill(a.grant_id)}, {...body,grant_ids:['invalid']},
  {...body,intent_ids:Array(21).fill('pending')}, {...body,intent_ids:['x'.repeat(161)]},
  {...body,extra:true}
 ])await assert.rejects(()=>owner(bad));
 f.corrupt('unverified');
 await assert.rejects(()=>owner(body),/source|unverified/i);
});

test('renewal projection stays bounded across retained expired grant ancestry',async()=>{
 const f=fixture(20000),name='n'.repeat(100),environment='p'.repeat(99);
 const original=await f.service.handle('enroll',{cookieToken:f.token,body:{
  intent_id:'original',agent_id:'alpha',name,environment,expires_at:2000
 }});f.publish();
 let parent=original.grant_id;
 const records=Array.from({length:9000},(_,i)=>{
  const grant_id=stableId('retained-grant-'+i);
  const record=canonicalRecord({
   schema:'unblock/1',kind:'enroll',agent_id:'alpha',intent_id:('retained-'+i).padEnd(160,'x'),
   payload:{grant_id,name,environment,kind:'agent',agent_ids:['alpha'],expires_at:2000,renewal_of:parent}
  });
  parent=grant_id;
  return record;
 });
 assert.ok(Buffer.byteLength(JSON.stringify(records))>4*1024*1024);
 f.seedEvents(records);f.advance(1500);
 const selected=await f.service.handle('attention',{cookieToken:f.token,body:{
  view:'renewal',grant_ids:[original.grant_id,parent]
 }});
 assert.equal(selected.grants.length,2);
 assert.ok(selected.grants.every((/** @type {any} */ g)=>g.expires_at===2000 && g.revoked===false));
 assert.ok(Buffer.byteLength(JSON.stringify(selected))<10000);
});

test('renewal projection retains full work history source validation',async()=>{
 const f=fixture();
 const a=await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'original',agent_id:'alpha',name:'Alpha'}});f.publish();
 f.seedEvents([canonicalRecord({schema:'unblock/1',kind:'answer',agent_id:'alpha',
  intent_id:'missing-request',request_id:stableId('missing-request'),payload:{answer:'Blue',revision:stableId('missing-revision')}
 })]);
 await assert.rejects(()=>f.service.handle('attention',{cookieToken:f.token,body:{view:'renewal',grant_ids:[a.grant_id]}}),/source unavailable or invalid/);
});

test('renewal rejects global intent selectors that can collide across agents',async()=>{
 const f=fixture();
 const a=await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'same-intent',agent_id:'alpha',name:'Alpha'}});f.publish();
 await f.service.handle('enroll',{cookieToken:f.token,body:{intent_id:'same-intent',agent_id:'beta',name:'Beta'}});f.publish();
 await assert.rejects(()=>f.service.handle('attention',{cookieToken:f.token,body:{
  view:'renewal',grant_ids:[a.grant_id],intent_ids:['same-intent']
 }}),/Invalid renewal selection/);
 const selected=await f.service.handle('attention',{cookieToken:f.token,body:{view:'renewal',grant_ids:[a.grant_id]}});
 assert.deepEqual(selected.grants.map((/** @type {any} */ g)=>g.agent_id),['alpha']);
});
