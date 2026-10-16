import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture} from './helpers/native-fixture.js';
import {canonicalRecord,stableId} from '../src/lib/server/unblock-core.js';

/** @type {any} */
const update={intent_id:'update-a',work_key:'review',summary:'Review implementation',context:'A bounded review is running',evidence:'Started reviewing the current source',next_action:'Return reviewed findings',parents:[],status:'working',next_update_at:1010,request_id:null};
async function setup() {
 const f=fixture();
 const owner=(/** @type {string} */ op,/** @type {any} */ body={})=>f.service.handle(op,{cookieToken:f.token,body});
 const alpha=await owner('enroll',{intent_id:'a',agent_id:'alpha',name:'Alpha',environment:'here'});f.publish();
 const beta=await owner('enroll',{intent_id:'b',agent_id:'beta',name:'Beta',environment:'elsewhere'});f.publish();
 const listener=await owner('enroll',{intent_id:'l',agent_id:'monitor',name:'Monitor',kind:'listener',environment:'here',agent_ids:['alpha']});f.publish();
 const neighbor=await owner('enroll',{intent_id:'n',agent_id:'neighbor-monitor',name:'Other environment',kind:'listener',environment:'elsewhere',agent_ids:['alpha']});f.publish();
 const call=(/** @type {string} */ credential)=>(/** @type {string} */ op,/** @type {any} */ body={})=>f.service.handle(op,{token:credential,body});
 const agent=call(alpha.credential),monitor=call(listener.credential);
 const save=async(/** @type {any} */ body=update)=>{let saved=/** @type {any} */(undefined);await assert.doesNotReject(async()=>{saved=await agent('work_update',body)},'native work_update must save an expectation without creating a human need');f.publish();return saved;};
 return {f,owner,agent,monitor,save,other:call(beta.credential),neighbor:call(neighbor.credential),listener};
}

test('declared update is separate from human needs; independent scoped observation deduplicates',async()=>{
 const {f,agent,monitor,save,other,neighbor,owner,listener}=await setup();
 const first=await save();let work=await agent('attention');
 assert.equal(work.requests.length,0);assert.equal(work.expectations.length,1);assert.equal(work.expectations[0].state,'working');
 assert.equal((await other('attention')).expectations.length,0);assert.equal((await neighbor('attention')).expectations.length,0);
 const observation={expectation_id:first.expectation_id,revision:first.record_id};
 await assert.rejects(()=>monitor('observe_due',observation));f.advance(11);
 await assert.rejects(()=>agent('observe_due',observation));await assert.rejects(()=>neighbor('observe_due',observation));
 const found=await monitor('observe_due',observation);assert.equal(found.visibility,'pending');f.publish();
 const again=await monitor('observe_due',observation);assert.equal(again.record_id,found.record_id);f.publish();
 work=await agent('attention');assert.equal(work.expectations[0].state,'investigate');assert.equal(work.expectations[0].current_observations.length,1);assert.equal(work.requests.length,0);
 await assert.rejects(()=>monitor('work_update',update));await assert.rejects(()=>owner('work_update',update));
 await owner('revoke',{intent_id:'revoke',grant_id:listener.grant_id});f.publish();await assert.rejects(()=>monitor('observe_due',observation));
});

test('new update retains concern history; historical retry does not reopen an old deadline',async()=>{
 const {f,agent,monitor,save}=await setup();const first=await save();f.advance(11);
 await monitor('observe_due',{expectation_id:first.expectation_id,revision:first.record_id});f.publish();
 const next=await save({...update,intent_id:'update-b',parents:[first.record_id],evidence:'Reviewed core; integration checks remain',next_update_at:1100});
 let row=(await agent('attention')).expectations[0];assert.equal(row.state,'working');assert.equal(row.observations.length,1);assert.equal(row.current_observations.length,0);
 assert.equal((await agent('work_update',update)).record_id,first.record_id);f.publish();
 row=(await agent('attention')).expectations[0];assert.equal(row.revisions[0].id,next.record_id);assert.equal(row.history.length,2);
 await assert.rejects(()=>monitor('observe_due',{expectation_id:first.expectation_id,revision:first.record_id}));
});

test('concurrent changes stay conflicted until all reviewed heads are reconciled',async()=>{
 const {f,agent,monitor,save}=await setup();const first=await save();
 const left=await save({...update,intent_id:'left',parents:[first.record_id],evidence:'One reviewer still working',next_update_at:1020});
 const right=await save({...update,intent_id:'right',parents:[first.record_id],evidence:'Another session reports a different due time',next_update_at:1030});f.advance(40);
 assert.equal((await agent('attention')).expectations[0].state,'conflict');
 await assert.rejects(()=>monitor('observe_due',{expectation_id:first.expectation_id,revision:left.record_id}));
 await save({...update,intent_id:'reconcile',parents:[right.record_id,left.record_id],evidence:'Reconciled both reviews; one remaining check',next_update_at:1100});
 const row=(await agent('attention')).expectations[0];assert.equal(row.state,'working');assert.equal(row.history.length,4);
});

test('closing an expectation preserves its unanswered request and uncertain action',async()=>{
 const {f,agent,save,other}=await setup();const need=await agent('request',{intent_id:'need',need_key:'deployment',need:'Which target?',context:'Awaiting owner target',recommendation:'Use the test target',next_action:'Deploy after answer',parents:[]});f.publish();
 await agent('action',{intent_id:'action',request_id:need.request_id,effect:'A previously attempted test effect requires verification'});f.publish();
 await assert.rejects(()=>other('work_update',{...update,request_id:need.request_id}));
 const first=await save({...update,request_id:need.request_id});
 await assert.rejects(()=>agent('work_update',{...update,intent_id:'retarget',parents:[first.record_id],request_id:null}));
 await save({...update,intent_id:'done',parents:[first.record_id],status:'completed',next_update_at:null,request_id:need.request_id,evidence:'Review returned; original target decision and effect check remain outstanding'});
 const work=await agent('attention');assert.equal(work.expectations[0].state,'completed');assert.equal(work.requests.length,1);assert.equal(work.requests[0].uncertain_actions.length,1);assert.equal(work.requests[0].answers.length,0);
});

test('invalid time, parent, status and principal references do not create expectations',async()=>{
 const {agent,save}=await setup();
 for(const change of [{next_update_at:999},{next_update_at:1000},{next_update_at:true},{next_update_at:1000+30*86400+1},{status:'quiet'},{status:'completed'},{parents:['not-a-uuid']},{parents:['00000000-0000-4000-8000-000000000001']},{request_id:'00000000-0000-4000-8000-000000000001'}])await assert.rejects(()=>agent('work_update',{...update,...change}));
 await save();assert.equal((await agent('attention')).expectations.length,1);
});

test('source loss after expectation ingestion preserves publication uncertainty',async()=>{
 const {f,agent}=await setup();f.failAfterWrite();
 await assert.rejects(()=>agent('work_update',update),(/** @type {any} */ error)=>error.publication_uncertain===true);
 await assert.rejects(()=>agent('attention'));
});

test('same work key in two authenticated environments cannot corrupt source or cross scope',async()=>{
 const {f,owner,agent,monitor,neighbor}=await setup();
 const second=await owner('enroll',{intent_id:'alpha-there',agent_id:'alpha',name:'Alpha there',environment:'elsewhere'});f.publish();
 const there=(/** @type {string} */ op,/** @type {any} */ body={})=>f.service.handle(op,{token:second.credential,body});
 const one=await agent('work_update',update),two=await there('work_update',update);
 assert.notEqual(one.expectation_id,two.expectation_id);f.publish();
 assert.equal((await owner('attention')).expectations.length,2);await owner('identity');
 assert.deepEqual((await monitor('attention')).expectations.map((/** @type {any} */ r)=>r.id),[one.expectation_id]);
 assert.deepEqual((await neighbor('attention')).expectations.map((/** @type {any} */ r)=>r.id),[two.expectation_id]);
 await assert.rejects(()=>there('work_update',{...update,intent_id:'foreign-parent',parents:[one.record_id]}));
 await owner('revoke',{intent_id:'revoke-there',grant_id:second.grant_id});f.publish();await assert.rejects(()=>there('identity'));
});

test('pre-namespace pilot expectation keeps its identity, exact retry and history',async()=>{
 const {f,agent,monitor,owner}=await setup();
 const legacy=stableId('alpha:expectation:'+update.work_key);
 const event={schema:'unblock/1',intent_id:update.intent_id,kind:'work_update',expectation_id:legacy,agent_id:'alpha',payload:{...update,environment:'here'}};
 delete event.payload.intent_id;
 const record=canonicalRecord(event);f.seedEvents([record]);
 assert.equal((await agent('work_update',update)).record_id,record.id);
 f.advance(11);await monitor('observe_due',{expectation_id:legacy,revision:record.id});f.publish();
 const changed=await agent('work_update',{...update,intent_id:'legacy-next',parents:[record.id],next_update_at:1100});f.publish();
 assert.equal(changed.expectation_id,legacy);const row=(await agent('attention')).expectations[0];assert.equal(row.history.length,2);assert.equal(row.observations.length,1);
 assert.equal((await agent('work_update',update)).record_id,record.id);await owner('identity');
});
