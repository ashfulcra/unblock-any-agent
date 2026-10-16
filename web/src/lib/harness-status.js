/** @param {any} run */
export function runStatus(run) {
 const lastEvent=run.events[run.events.length-1];
 if(lastEvent.step==='RUN_COMPLETE') {
  if(lastEvent.status==='completed')return 'completed';
  if(['incomplete','failed','error'].includes(lastEvent.status))return 'incomplete';
  return 'unknown';
 }
 if(lastEvent.step==='RUN_INCOMPLETE')return 'incomplete';
 if(lastEvent.step==='ESCALATE')return 'escalated';
 return 'in-progress';
}
