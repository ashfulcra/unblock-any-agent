import { createHmac, timingSafeEqual, randomUUID } from 'node:crypto';
import { canonicalRecord, projectEvents, readEvents, stableId, sealAgent, openAgent, authorizeAgent } from './unblock-core.js';

/** @param {any} config */
export function createService(config) {
  const endpoint = config.apiEndpoint || 'https://api.fulcradynamics.com/';
  const now = config.now || (() => Date.now()/1000);
  const fetcher = config.fetch || fetch;
  const annotation = config.annotation;
  if (!/^MomentAnnotation\/[a-f0-9-]{36}$/.test(annotation || '') || !/^[a-f0-9]{64}$/.test(config.key || '') || !config.ownerId) throw new Error('Native pilot is not configured');
  /** @param {string} token @param {string} path @param {any} [options] */
  async function upstream(token,path,options={}) {
    const response = await fetcher(endpoint+path,{...options,headers:{Authorization:'Bearer '+token,...options.headers},signal:AbortSignal.timeout(12000)});
    if (!response.ok) throw new Error('Fulcra request unavailable ('+response.status+')');
    return response.json();
  }
  /** @param {string} note */
  const mac = note => createHmac('sha256',config.key).update('unblock-record/1:'+note).digest('hex');
  /** @param {string} token */
  async function load(token) {
    const data = await upstream(token,`data/v1alpha1/event/${encodeURIComponent(annotation)}?start_time=1970-01-01T00:00:00Z&end_time=${encodeURIComponent(new Date((now()+60)*1000).toISOString())}`);
    const rows = Array.isArray(data) ? data : data.records;
    if (!Array.isArray(rows)) throw new Error('Unexpected native record response');
    return rows.map((/** @type {any} */ row) => {
      const signed = JSON.parse(row.note);
      const expected = Buffer.from(mac(signed.note),'hex'),actual = Buffer.from(signed.mac || '','hex');
      if (expected.length !== actual.length || !timingSafeEqual(expected,actual)) throw new Error('Unverified native record');
      return {id:row.id,note:signed.note};
    });
  }
  /** @param {string} token @param {any} event */
  async function publish(token,event) {
    const record=canonicalRecord(event),signed={note:record.note,mac:mac(record.note)};
    try {
    await upstream(token,'ingest/v1/record/MomentAnnotation?api_version=v1alpha1',{method:'POST',headers:{'Content-Type':'application/x-jsonl'},body:JSON.stringify({...record,note:JSON.stringify(signed),sources:['com.fulcradynamics.annotation.'+annotation.split('/')[1]]})+'\n'});
    const visible=(await load(token)).some(r=>r.id===record.id && r.note===record.note);
    return {record_id:record.id,request_id:event.request_id,visibility:visible?'visible':'pending'};
    } catch (err) {
      const failure=/** @type {Error & {publication_uncertain?:boolean}} */(err);failure.publication_uncertain=true;throw failure;
    }
  }
  /** @param {any} b @param {string} field @param {number} [max] */
  function text(b,field,max=4000) {
    if (typeof b[field] !== 'string' || !b[field].trim() || b[field].length>max) throw new Error('Invalid '+field);
    return b[field];
  }
  /** @param {any} rows */
  const view = rows => projectEvents(rows);
  return {
    /** @param {string} operation @param {any} input @returns {Promise<any>} */
    async handle(operation,input) {
      const body=input.body || {};
      const agent=!!input.token;
      /** @type {any} */ let grant;
      if (agent) grant=openAgent(input.token,config.key);
      const token=agent?grant.upstream:input.cookieToken;
      if (!token) throw new Error('Authentication required');
      const user=await upstream(token,'user/v1alpha1/info');
      if (user.userid !== config.ownerId) throw new Error('Account is not the pilot owner');
      const rows=await load(token),events=readEvents(rows);
      if (agent) authorizeAgent(grant,events,user.userid,now());
      const requests=view(rows);
      if (['attention','recover'].includes(operation)) {
        if (body.request_id && !requests.some(r=>r.id===body.request_id && (!agent || r.agent_id===grant.agent_id))) throw new Error('Request not permitted');
        return {requests:requests.filter(r=>(!agent || r.agent_id===grant.agent_id) && (!body.request_id || r.id===body.request_id)),grants:agent?[]:events.filter(e=>e.kind==='enroll').map(e=>({record_id:e.id,agent_id:e.agent_id,intent_id:e.intent_id,...e.payload,revoked:events.some(r=>r.kind==='revoke' && r.payload.grant_id===e.payload.grant_id)})),checked_at:new Date(now()*1000).toISOString(),source:'checked'};
      }
      if (operation==='prepare_enrollment') {
        if (agent) throw new Error('Owner operation required');
        const exp=JSON.parse(Buffer.from(token.split('.')[1],'base64url').toString()).exp;
        if (!Number.isFinite(exp) || exp<=now()) throw new Error('Owner session expired');
        return {expires_at:Math.min(exp,Math.floor(now())+3600)};
      }
      const intent_id=text(body,'intent_id',160);
      if (['enroll','revoke','answer'].includes(operation) && agent) throw new Error('Owner operation required');
      if (operation==='enroll') {
        const agent_id=text(body,'agent_id',100),name=text(body,'name',100);
        if (!/^[a-z0-9][a-z0-9-]*$/.test(agent_id)) throw new Error('Invalid agent ID');
        const exp=JSON.parse(Buffer.from(token.split('.')[1],'base64url').toString()).exp;
        const grant_id=stableId(user.userid+':'+agent_id+':'+intent_id);
        const original=events.find(e=>e.kind==='enroll' && e.payload.grant_id===grant_id);
        const expires_at=body.expires_at ?? original?.payload.expires_at ?? (exp<=Math.floor(now())+3600?exp:NaN);
        if (!Number.isFinite(expires_at) || expires_at<=now() || expires_at>exp || expires_at>Math.floor(now())+3600) throw new Error('Prepare a stable enrollment expiry within the current session and one hour');
        if (original && (original.payload.name!==name || original.payload.expires_at!==expires_at)) throw new Error('Enrollment intent already has different fields');
        const newGrant={agent_id,grant_id,owner_id:user.userid,expires_at,upstream:token};
        const saved=await publish(token,{schema:'unblock/1',intent_id,kind:'enroll',agent_id,payload:{grant_id,name,expires_at}});
        return {...saved,agent_id,grant_id,expires_at,credential:sealAgent(newGrant,config.key)};
      }
      if (operation==='revoke') {
        const grant_id=text(body,'grant_id',100),enrollment=events.find(e=>e.kind==='enroll' && e.payload.grant_id===grant_id);
        if (!enrollment) throw new Error('Enrollment not found');
        return publish(token,{schema:'unblock/1',intent_id,kind:'revoke',agent_id:enrollment.agent_id,payload:{grant_id}});
      }
      if (operation==='request') {
        if (!agent) throw new Error('Enrolled agent required');
        const need_key=text(body,'need_key',160),request_id=stableId(grant.agent_id+':'+need_key);
        const parents=body.parents || [];
        if (!Array.isArray(parents) || parents.length>10 || parents.some(p=>typeof p!=='string')) throw new Error('Invalid revision parents');
        const existing=requests.find(r=>r.id===request_id);
        if (parents.length && (!existing || parents.some(p=>!existing.history.some((/** @type {any} */ h)=>h.id===p)))) throw new Error('Unknown revision parent');
        const payload={need_key,need:text(body,'need'),context:text(body,'context',16000),recommendation:text(body,'recommendation'),next_action:text(body,'next_action'),parents:[...parents].sort()};
        return publish(token,{schema:'unblock/1',intent_id:parents.length?intent_id:request_id,kind:'request',request_id,agent_id:grant.agent_id,payload});
      }
      const request_id=text(body,'request_id',100),request=requests.find(r=>r.id===request_id);
      if (!request || (agent && request.agent_id!==grant.agent_id)) throw new Error('Request not permitted');
      const base={schema:'unblock/1',intent_id,kind:operation,request_id,agent_id:request.agent_id};
      if (operation==='answer') {
        const revision=text(body,'revision',100);
        if (!request.history.some((/** @type {any} */ r)=>r.id===revision)) throw new Error('Unknown request revision');
        return publish(token,{...base,payload:{revision,answer:text(body,'answer',16000),responder:user.userid}});
      }
      if (!agent) throw new Error('Enrolled agent required');
      if (operation==='progress') {
        const revision=text(body,'revision',100),stage=text(body,'stage',30),evidence=text(body,'evidence',16000);
        const answers=body.answers;
        if (Array.isArray(answers) && answers.every(a=>typeof a==='string')) {
          const retry=canonicalRecord({...base,payload:{revision,stage,evidence,answers:[...answers].sort(),reconciled:body.reconciled===true}});
          if(rows.some(r=>r.id===retry.id && r.note===retry.note)) return {record_id:retry.id,request_id,visibility:'visible'};
        }
        if (!['acknowledged','resumed','completed'].includes(stage) || !Array.isArray(answers) || answers.length===0 || new Set(answers).size!==answers.length || answers.some(a=>!request.answers.some((/** @type {any} */ r)=>r.id===a)) || request.revisions.length!==1 || request.revisions[0].id!==revision || answers.length!==request.answers.length) throw new Error('Current question and complete answer set required');
        if (answers.length>1 && body.reconciled!==true) throw new Error('Conflicting answers require explicit reconciliation');
        return publish(token,{...base,payload:{revision,stage,evidence,answers:[...answers].sort(),reconciled:body.reconciled===true}});
      }
      if (operation==='action') return publish(token,{...base,payload:{effect:text(body,'effect',16000)}});
      if (operation==='settle') {
        const action=text(body,'action',100);
        if (!request.actions.some((/** @type {any} */ a)=>a.id===action)) throw new Error('Action not found');
        return publish(token,{...base,payload:{action,evidence:text(body,'evidence',16000)}});
      }
      throw new Error('Unknown operation');
    }
  };
}
