import {readEvents} from './unblock-core.js';

/** @param {any[]} records @param {number} now */
export function projectExpectations(records,now) {
 const groups=new Map();
 for(const event of readEvents(records).filter(e=>['work_update','overdue'].includes(e.kind))) {
  if(!event.expectation_id)throw new Error('Missing expectation identity');
  const rows=groups.get(event.expectation_id) || [];rows.push(event);groups.set(event.expectation_id,rows);
 }
 return [...groups].map(([id,rows])=>{
  const history=rows.filter((/** @type {any} */ e)=>e.kind==='work_update');
  if(!history.length || new Set(rows.map((/** @type {any} */ e)=>e.agent_id)).size!==1 || new Set(history.map((/** @type {any} */ e)=>e.payload.environment)).size!==1)throw new Error('Invalid expectation history');
  const superseded=new Set(history.flatMap((/** @type {any} */ e)=>e.payload.parents));
  const revisions=history.filter((/** @type {any} */ e)=>!superseded.has(e.id));
  if(!revisions.length)throw new Error('Invalid expectation revision graph');
  const current=revisions.length===1?revisions[0]:null;
  const observations=rows.filter((/** @type {any} */ e)=>e.kind==='overdue');
  const current_observations=observations.filter((/** @type {any} */ e)=>current?.payload.status==='working' && e.payload.revision===current.id && e.payload.next_update_at===current.payload.next_update_at);
  let state=current?.payload.status || 'conflict';
  if(state==='working' && current.payload.next_update_at<=now)state=current_observations.length?'investigate':'due';
  return {id,agent_id:history[0].agent_id,environment:history[0].payload.environment,request_id:history[0].payload.request_id,history,revisions,observations,current_observations,state};
 });
}
