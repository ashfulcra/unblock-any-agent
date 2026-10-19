import { createHash, createCipheriv, createDecipheriv, randomBytes } from 'node:crypto';

/** @param {any} value @returns {string} */
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
/** @param {string} text */
export function stableId(text) {
  const hash = createHash('sha256').update(text).digest('hex');
  return `${hash.slice(0,8)}-${hash.slice(8,12)}-5${hash.slice(13,16)}-a${hash.slice(17,20)}-${hash.slice(20,32)}`;
}
/** @param {any} event */
export function canonicalRecord(event) {
  if (event?.schema !== 'unblock/1' || !event.intent_id || !event.agent_id || !event.kind || !event.payload) throw new Error('Invalid event');
  const note = canonical(event);
  return { id: stableId(note), note };
}
/** Exact question, answer set and unresolved effects reviewed by a human.
 * @param {any} request */
export function decisionSnapshot(request) {
  return createHash('sha256').update(canonical({request_id:request.id,revisions:request.revisions.map((/** @type {any} */ r)=>r.id).sort(),answers:request.answers.map((/** @type {any} */ r)=>r.id).sort(),uncertain_actions:request.uncertain_actions.map((/** @type {any} */ r)=>r.id).sort()})).digest('hex');
}
/** @param {any[]} records */
export function readEvents(records) {
  const unique = new Map();
  for (const record of records) {
    const event = JSON.parse(record.note);
    if (canonicalRecord(event).id !== record.id) throw new Error('Record integrity mismatch');
    const recorded_at=typeof record.recorded_at==='string' && Number.isFinite(Date.parse(record.recorded_at))?record.recorded_at:null;
    const prior=unique.get(record.id)?.recorded_at;
    unique.set(record.id, { ...event, id: record.id, recorded_at:prior && (!recorded_at || Date.parse(prior)<Date.parse(recorded_at))?prior:recorded_at });
  }
  return [...unique.values()];
}
/** @param {any[]} records */
export function projectEvents(records) {
  const events = readEvents(records);
  const groups = new Map();
  for (const e of events) {
    if (['enroll','revoke','work_update','overdue'].includes(e.kind)) continue;
    if (!e.request_id) throw new Error('Missing request identity');
    const list = groups.get(e.request_id) || []; list.push(e); groups.set(e.request_id,list);
  }
  return [...groups].map(([id, list]) => {
    const history = list.filter((/** @type {any} */ e) => e.kind === 'request');
    if (!history.length || new Set(history.map((/** @type {any} */ e) => e.agent_id)).size !== 1) throw new Error('Missing or ambiguous agent');
    const agent_id = history[0].agent_id;
    if (list.some((/** @type {any} */ e) => e.agent_id !== agent_id)) throw new Error('Foreign agent event');
    const superseded = new Set(history.flatMap((/** @type {any} */ e) => e.payload.parents || []));
    const revisions = history.filter((/** @type {any} */ e) => !superseded.has(e.id));
    if (!revisions.length) throw new Error('Invalid revision graph');
    const current = revisions.length === 1 ? revisions[0] : null;
    const allAnswers = list.filter((/** @type {any} */ e) => e.kind === 'answer');
    const answers = allAnswers.filter((/** @type {any} */ e) => current && e.payload.revision === current.id);
    const stale_answers = allAnswers.filter((/** @type {any} */ e) => !answers.includes(e));
    const answerIds = answers.map((/** @type {any} */ e) => e.id).sort();
    const progress = list.filter((/** @type {any} */ e) => e.kind === 'progress' && current && e.payload.revision === current.id && canonical([...e.payload.answers].sort()) === canonical(answerIds));
    const settled = new Set(list.filter((/** @type {any} */ e) => e.kind === 'settle' && e.payload.evidence?.trim()).map((/** @type {any} */ e) => e.payload.action));
    const uncertain_actions = list.filter((/** @type {any} */ e) => e.kind === 'action' && !settled.has(e.id));
    let state = !current ? 'conflict' : !answers.length ? 'needs_you' : answers.length > 1 ? 'answer_conflict' : 'awaiting_pickup';
    if (current && answers.length && progress.length) {
      state = ['completed','resumed','acknowledged'].find(stage => progress.some((/** @type {any} */ e) => e.payload.stage === stage)) || state;
    }
    if (uncertain_actions.length) state = 'uncertain_action';
    const delivery_history=list.filter((/** @type {any} */ e)=>e.kind==='delivery');
    const deliveries=delivery_history.filter((/** @type {any} */ e)=>current && e.payload.revision===current.id && canonical([...e.payload.answers].sort())===canonical(answerIds));
    const firstDate=(/** @type {any[]} */ rows)=>rows.map(e=>e.recorded_at).filter(Boolean).sort((a,b)=>Date.parse(a)-Date.parse(b))[0] || null;
    const roots=history.filter((/** @type {any} */ e)=>!(e.payload.parents || []).length);
    const created_at=roots.length && roots.every((/** @type {any} */ e)=>e.recorded_at)?firstDate(roots):null;
    return { id, agent_id, created_at,updated_at:firstDate(revisions),answered_at:firstDate(answers),completed_at:firstDate(progress.filter((/** @type {any} */ e)=>e.payload.stage==='completed')), revisions, history, answers, stale_answers, progress, progress_history:list.filter((/** @type {any} */ e)=>e.kind==='progress'), delivery_history, deliveries, actions:list.filter((/** @type {any} */ e)=>e.kind==='action'), settlements:list.filter((/** @type {any} */ e)=>e.kind==='settle'), uncertain_actions, state };
  });
}
/** @param {any} grant @param {string} key */
export function sealAgent(grant,key) {
  if (!/^[a-f0-9]{64}$/.test(key)) throw new Error('Server enrollment key unavailable');
  const iv = randomBytes(12), cipher = createCipheriv('aes-256-gcm',Buffer.from(key,'hex'),iv);
  cipher.setAAD(Buffer.from('unblock-agent/1'));
  const ciphertext = Buffer.concat([cipher.update(JSON.stringify(grant),'utf8'),cipher.final()]);
  return 'uaa1.' + Buffer.concat([iv,cipher.getAuthTag(),ciphertext]).toString('base64url');
}
/** @param {string} token @param {string} key */
export function openAgent(token,key) {
  if (!token.startsWith('uaa1.') || token.length > 20000 || !/^[a-f0-9]{64}$/.test(key)) throw new Error('Invalid agent credential');
  const data = Buffer.from(token.slice(5),'base64url');
  const cipher = createDecipheriv('aes-256-gcm',Buffer.from(key,'hex'),data.subarray(0,12));
  cipher.setAAD(Buffer.from('unblock-agent/1')); cipher.setAuthTag(data.subarray(12,28));
  return JSON.parse(Buffer.concat([cipher.update(data.subarray(28)),cipher.final()]).toString('utf8'));
}
/** Check authenticated sealed claims before any upstream request.
 * @param {any} grant @param {string} account @param {number} now */
export function validateAgentCredential(grant,account,now) {
  if (!grant.agent_id || grant.owner_id !== account || !Number.isFinite(grant.expires_at) || grant.expires_at <= now) throw new Error('Agent credential expired or account mismatch');
}
/** @param {any} grant @param {any[]} events @param {string} account @param {number} now */
export function authorizeAgent(grant,events,account,now) {
  validateAgentCredential(grant,account,now);
  const enrollment=enrollmentRecord(grant.grant_id,events);
  if (grantScope(grant.agent_id,grant)!==grantScope(enrollment.agent_id,enrollment.payload)) throw new Error('Agent enrollment scope mismatch');
  return grant;
}

/** @param {string} agent_id @param {any} payload */
export function grantScope(agent_id,payload) {
  return canonical({agent_id,kind:payload.kind || 'agent',environment:payload.environment || 'pilot',agent_ids:[...(payload.agent_ids || [agent_id])].sort()});
}
/** Verify ancestry without inheriting an expired parent's lease. Revocation
 * remains effective for every descendant after asynchronous source readback.
 * @param {string} grant_id @param {any[]} events */
export function enrollmentRecord(grant_id,events) {
  const revoked=new Set(events.filter(e=>e.kind==='revoke').map(e=>e.payload.grant_id));
  const enrollments=new Map();
  for (const e of events.filter(e=>e.kind==='enroll')) {
    const rows=enrollments.get(e.payload.grant_id) || [];rows.push(e);enrollments.set(e.payload.grant_id,rows);
  }
  const seen=new Set();let id=grant_id,scope='',first;
  while (id) {
    const rows=enrollments.get(id);
    if (seen.has(id) || revoked.has(id) || !rows || rows.length!==1) throw new Error('Agent enrollment unavailable or revoked');
    seen.add(id);const current=rows[0],currentScope=grantScope(current.agent_id,current.payload);
    if (scope && scope!==currentScope) throw new Error('Agent enrollment scope mismatch');
    scope=currentScope;first=first || current;id=current.payload.renewal_of;
  }
  if (!first) throw new Error('Agent enrollment unavailable');
  return first;
}
