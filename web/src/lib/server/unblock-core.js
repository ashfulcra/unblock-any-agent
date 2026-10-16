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
/** @param {any[]} records */
export function readEvents(records) {
  const unique = new Map();
  for (const record of records) {
    const event = JSON.parse(record.note);
    if (canonicalRecord(event).id !== record.id) throw new Error('Record integrity mismatch');
    unique.set(record.id, { ...event, id: record.id });
  }
  return [...unique.values()];
}
/** @param {any[]} records */
export function projectEvents(records) {
  const events = readEvents(records);
  const groups = new Map();
  for (const e of events) {
    if (['enroll','revoke'].includes(e.kind)) continue;
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
    return { id, agent_id, revisions, history, answers, stale_answers, progress, progress_history:list.filter((/** @type {any} */ e)=>e.kind==='progress'), delivery_history, deliveries, actions:list.filter((/** @type {any} */ e)=>e.kind==='action'), settlements:list.filter((/** @type {any} */ e)=>e.kind==='settle'), uncertain_actions, state };
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
/** @param {any} grant @param {any[]} events @param {string} account @param {number} now */
export function authorizeAgent(grant,events,account,now) {
  if (!grant.agent_id || grant.owner_id !== account || !Number.isFinite(grant.expires_at) || grant.expires_at <= now) throw new Error('Agent credential expired or account mismatch');
  if (!events.some(e => e.kind === 'enroll' && e.agent_id === grant.agent_id && e.payload.grant_id === grant.grant_id) || events.some(e => e.kind === 'revoke' && e.payload.grant_id === grant.grant_id)) throw new Error('Agent enrollment unavailable or revoked');
  return grant;
}
