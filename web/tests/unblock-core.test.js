import test from 'node:test';
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { canonicalRecord, projectEvents, sealAgent, openAgent, authorizeAgent } from '../src/lib/server/unblock-core.js';

const request = { schema: 'unblock/1', intent_id: 'need-1', kind: 'request', request_id: 'req-1', agent_id: 'alpha', payload: { need_key: 'decision', need: 'Choose a color', context: 'Shipping a page', recommendation: 'blue', next_action: 'apply color', parents: [] } };
/** @param {any} e */
const record = e => canonicalRecord(e);
/** @param {string} id */
const answer = (id, text='blue', revision=record(request).id) => record({ schema:'unblock/1',intent_id:id,kind:'answer',request_id:'req-1',agent_id:'alpha',payload:{revision,answer:text,responder:'owner'} });
/** @param {string[]} answers */
const progress = (answers, stage='resumed') => record({schema:'unblock/1',intent_id:'progress-'+answers.join(),kind:'progress',request_id:'req-1',agent_id:'alpha',payload:{revision:record(request).id,answers,stage,evidence:'Read back applied color'}});

test('withdrawal closes only its reviewed snapshot and never hides a later answer or uncertain effect',()=>{
 const q=record(request),w=progress([],'withdrawn');
 assert.equal(projectEvents([q,w])[0].state,'withdrawn');
 assert.equal(projectEvents([q,w,answer('concurrent-answer')])[0].state,'awaiting_pickup');
 const action=record({schema:'unblock/1',intent_id:'uncertain',kind:'action',request_id:'req-1',agent_id:'alpha',payload:{effect:'Check first'}});
 assert.equal(projectEvents([q,w,action])[0].state,'uncertain_action');
});

test('display timestamps come from retained source metadata without changing signed record identity',()=>{
 const r={...record(request),recorded_at:'2026-10-17T12:00:00Z'};
 const a={...answer('time-answer'),recorded_at:'2026-10-19T12:00:00Z'};
 const p={...progress([a.id],'completed'),recorded_at:'2026-10-19T12:05:00Z'};
 const row=projectEvents([r,a,p])[0];
 assert.equal(row.created_at,r.recorded_at);
 assert.equal(row.answered_at,a.recorded_at);
 assert.equal(row.completed_at,p.recorded_at);
 assert.equal(row.history[0].id,record(request).id);
 assert.equal(projectEvents([record(request)])[0].created_at,null);
});

test('an unknown original waiting date never falls forward to a dated revision',()=>{
 const original=record(request);
 const revision={...record({...request,intent_id:'dated-revision',payload:{...request.payload,context:'Updated context',parents:[original.id]}}),recorded_at:'2026-10-19T12:00:00Z'};
 assert.equal(projectEvents([original,revision])[0].created_at,null);
 const dated={...original,recorded_at:'2026-10-17T12:00:00Z'};
 assert.equal(projectEvents([dated,revision])[0].created_at,dated.recorded_at);
 const undatedVariant=record({...request,payload:{...request.payload,context:'Concurrent original'}});
 assert.equal(projectEvents([dated,undatedVariant,revision])[0].created_at,null);
 const retry={...dated,recorded_at:'2026-10-19T12:00:00Z'};
 assert.equal(projectEvents([retry,dated,revision])[0].created_at,dated.recorded_at);
});

test('stable retry converges while changed payload stays visible as conflict', () => {
 const a=record(request),b=record({...request,payload:{...request.payload,need:'Choose a size'}});
 assert.equal(record({...request,payload:{...request.payload}}).id,a.id);
 assert.notEqual(a.id,b.id);
 const rows=projectEvents([a,a,b]);assert.equal(rows.length,1);assert.equal(rows[0].revisions.length,2);assert.equal(rows[0].state,'conflict');
});
test('new answer cannot be hidden by old progress; all answers remain attributed', () => {
 const a=answer('a'),b=answer('b','red');
 let row=projectEvents([record(request),a,progress([a.id])])[0];assert.equal(row.state,'resumed');
 row=projectEvents([record(request),a,b,progress([a.id])])[0];assert.equal(row.state,'answer_conflict');assert.equal(row.answers.length,2);assert.equal(row.answers[0].payload.responder,'owner');assert.equal(row.progress_history.length,1);
});
test('replacement recovers unanswered obligations and context corrections preserve stale answers', () => {
 const first=record(request);assert.equal(projectEvents([first])[0].state,'needs_you');
 const revised=record({...request,intent_id:'revision',payload:{...request.payload,context:'New color rules',parents:[first.id]}});
 const row=projectEvents([first,revised,answer('a')])[0];assert.equal(row.state,'needs_you');assert.equal(row.revisions[0].id,revised.id);assert.equal(row.history.length,2);assert.equal(row.stale_answers.length,1);
});
test('uncertain external action stays visible despite completion until evidence-backed settlement', () => {
 const a=answer('a'),act=record({schema:'unblock/1',intent_id:'act',kind:'action',request_id:'req-1',agent_id:'alpha',payload:{effect:'publish color'}});
 const rows=[record(request),a,progress([a.id],'completed'),act];let row=projectEvents(rows)[0];assert.equal(row.state,'uncertain_action');
 rows.push(record({schema:'unblock/1',intent_id:'settle',kind:'settle',request_id:'req-1',agent_id:'alpha',payload:{action:act.id,evidence:'Observed published artifact hash'}}));row=projectEvents(rows)[0];assert.equal(row.state,'completed');assert.equal(row.actions.length,1);assert.equal(row.settlements.length,1);assert.equal(row.settlements[0].payload.evidence,'Observed published artifact hash');
});
test('corrupt or foreign-agent records fail closed instead of manufacturing quiet', () => {
 assert.throws(()=>projectEvents([{id:'bad',note:'not json'}]));
 const bad=answer('a');bad.note=JSON.stringify({...JSON.parse(bad.note),agent_id:'beta'});assert.throws(()=>projectEvents([record(request),bad]));
});
test('sealed agent credentials reject tampering, expiry, account mismatch and revocation', () => {
 const key=randomBytes(32).toString('hex'),grant={agent_id:'alpha',grant_id:'grant-1',owner_id:'owner',expires_at:2000,upstream:'private bearer'};
 const token=sealAgent(grant,key);assert.ok(!token.includes('private bearer'));assert.deepEqual(openAgent(token,key),grant);assert.throws(()=>openAgent(token.slice(0,-4)+'xxxx',key));
 const enrollment={kind:'enroll',agent_id:'alpha',payload:{grant_id:'grant-1'}};
 assert.equal(authorizeAgent(grant,[enrollment],'owner',1000).agent_id,'alpha');
 assert.throws(()=>authorizeAgent(grant,[enrollment],'other',1000));assert.throws(()=>authorizeAgent(grant,[enrollment],'owner',2000));assert.throws(()=>authorizeAgent(grant,[],'owner',1000));
 assert.throws(()=>authorizeAgent(grant,[enrollment,{kind:'revoke',agent_id:'alpha',payload:{grant_id:'grant-1'}}],'owner',1000));
});
