import { createHmac, timingSafeEqual, randomUUID } from 'node:crypto';
import { canonicalRecord, projectEvents, readEvents, stableId, sealAgent, openAgent, validateAgentCredential, authorizeAgent, enrollmentRecord, grantScope, decisionSnapshot } from './unblock-core.js';
import {projectExpectations} from './unblock-expectations.js';

export class NativeSourceError extends Error {
  constructor() {super('Fulcra source unavailable');this.name='NativeSourceError';}
}

/** @param {any} config */
export function createService(config) {
  const endpoint = config.apiEndpoint || 'https://api.fulcradynamics.com/';
  const now = config.now || (() => Date.now()/1000);
  const fetcher = config.fetch || fetch;
  const annotation = config.annotation;
  if (!/^MomentAnnotation\/[a-f0-9-]{36}$/.test(annotation || '') || !/^[a-f0-9]{64}$/.test(config.key || '') || !config.ownerId) throw new Error('Native pilot is not configured');
  /** @param {string} token @param {string} path @param {any} [options] */
  async function upstream(token,path,options={}) {
    try {
      const response = await fetcher(endpoint+path,{...options,headers:{Authorization:'Bearer '+token,...options.headers},signal:AbortSignal.timeout(12000)});
      if (!response.ok) throw new NativeSourceError();
      return await response.json();
    } catch {throw new NativeSourceError();}
  }
  /** @param {string} note */
  const mac = note => createHmac('sha256',config.key).update('unblock-record/1:'+note).digest('hex');
  /** @param {string} token */
  async function load(token) {
    const data = await upstream(token,`data/v1alpha1/event/${encodeURIComponent(annotation)}?start_time=1970-01-01T00:00:00Z&end_time=${encodeURIComponent(new Date((now()+60)*1000).toISOString())}`);
    const rows = Array.isArray(data) ? data : data.records;
    if (!Array.isArray(rows)) throw new Error('Unexpected native record response');
    try { return rows.map((/** @type {any} */ row) => {
      const signed = JSON.parse(row.note);
      if (typeof signed?.note!=='string' || !/^[a-f0-9]{64}$/.test(signed?.mac || '')) throw new Error('Invalid source envelope');
      const expected = Buffer.from(mac(signed.note),'hex'),actual = Buffer.from(signed.mac || '','hex');
      if (expected.length !== actual.length || !timingSafeEqual(expected,actual)) throw new Error('Unverified native record');
      return {id:row.id,note:signed.note,recorded_at:row.recorded_at || null};
    }); } catch { throw new Error('Native source unavailable or unverified'); }
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
  /** @param {any} value */
  function reference(value) {
    if(typeof value!=='string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(value))throw new Error('Invalid expectation reference');
    return value.toLowerCase();
  }
  /** @param {any} rows */
  const view = rows => projectEvents(rows);
  return {
    /** @param {string} operation @param {any} input @returns {Promise<any>} */
    async handle(operation,input) {
      const body=input.body || {};
      const agent=!!input.token;
      /** @type {any} */ let grant;
      if (agent) {
        grant=openAgent(input.token,config.key);
        validateAgentCredential(grant,config.ownerId,now());
      }
      const token=agent?grant.upstream:input.cookieToken;
      if (!token) throw new Error('Authentication required');
      const user=await upstream(token,'user/v1alpha1/info');
      if (user.userid !== config.ownerId) throw new Error('Account is not the pilot owner');
      const rows=await load(token);
      /** @type {any[]} */ let events,requests,expectations;
      try {events=readEvents(rows);requests=view(rows);expectations=projectExpectations(rows,now());} catch {throw new Error('Native source unavailable or invalid');}
      if (agent) authorizeAgent(grant,events,user.userid,now());
      const principal=agent?{kind:grant.kind || 'agent',id:grant.agent_id,environment:grant.environment || 'pilot',agent_ids:grant.agent_ids || [grant.agent_id]}:{kind:'owner',id:user.userid};
      const allowed=(/** @type {any} */ r)=>!agent || (principal.kind==='listener'?principal.agent_ids.includes(r.agent_id):r.agent_id===grant.agent_id);
      const allowedExpectation=(/** @type {any} */ r)=>allowed(r) && (principal.kind!=='listener' || r.environment===principal.environment);
      if (operation==='identity') return principal;
      if (operation==='enrollment') {
        if (!agent) throw new Error('Enrolled connection required');
        return {...principal,grant_id:grant.grant_id,expires_at:grant.expires_at};
      }
      if (['attention','recover'].includes(operation)) {
        if (body.request_id && !requests.some(r=>r.id===body.request_id && allowed(r))) throw new Error('Request not permitted');
        return {principal,requests:requests.filter(r=>allowed(r) && (!body.request_id || r.id===body.request_id)),expectations:expectations.filter(r=>allowedExpectation(r) && (!body.request_id || r.request_ids.includes(body.request_id))),grants:agent?[]:events.filter(e=>e.kind==='enroll').map(e=>{let revoked=false;try{enrollmentRecord(e.payload.grant_id,events);}catch{revoked=true;}return {record_id:e.id,agent_id:e.agent_id,intent_id:e.intent_id,...e.payload,revoked};}),checked_at:new Date(now()*1000).toISOString(),source:'checked'};
      }
      if(operation==='work_update') {
        if(principal.kind!=='agent')throw new Error('Enrolled worker required');
        const work_key=text(body,'work_key',160),legacy_id=stableId(grant.agent_id+':expectation:'+work_key);
        const legacy=expectations.find(r=>r.id===legacy_id && r.agent_id===grant.agent_id && r.environment===principal.environment);
        // Keep already-published pilot identities; new work is collision-safe before readback.
        const expectation_id=legacy?.id || stableId(JSON.stringify(['expectation/2',grant.agent_id,principal.environment,work_key]));
        const existing=expectations.find(r=>r.id===expectation_id);
        const parents=body.parents;
        if(!Array.isArray(parents) || parents.length>10)throw new Error('Explicit expectation parents required');
        const reviewed=parents.map(reference).sort();
        if(new Set(reviewed).size!==reviewed.length || (reviewed.length && (!existing || reviewed.some(p=>!existing.history.some((/** @type {any} */ e)=>e.id===p)))))throw new Error('Unknown or duplicate expectation parent');
        const request_id=body.request_id==null?null:reference(body.request_id);
        if(request_id && !requests.some(r=>r.id===request_id && r.agent_id===grant.agent_id))throw new Error('Linked request not permitted');
        const payload={work_key,summary:text(body,'summary'),context:text(body,'context',16000),evidence:text(body,'evidence',16000),next_action:text(body,'next_action'),parents:reviewed,status:text(body,'status',20),next_update_at:body.next_update_at,request_id,environment:principal.environment};
        const event={schema:'unblock/1',intent_id:text(body,'intent_id',160),kind:'work_update',expectation_id,agent_id:grant.agent_id,payload};
        const retry=canonicalRecord(event);
        if(rows.some(r=>r.id===retry.id && r.note===retry.note))return {record_id:retry.id,expectation_id,visibility:'visible'};
        if(existing && existing.environment!==principal.environment)throw new Error('Expectation environment binding changed');
        if(existing && (existing.link_conflict || existing.request_id!==request_id)) {
          const knownLinks=existing.revisions.map((/** @type {any} */ e)=>e.payload.request_id);
          if(!existing.link_conflict || !knownLinks.includes(request_id) || existing.revisions.some((/** @type {any} */ e)=>!reviewed.includes(e.id)))throw new Error('Expectation request binding changed without complete conflict review');
        }
        if(!['working','completed','cancelled'].includes(payload.status))throw new Error('Invalid expectation status');
        if(payload.status==='working') {
          if(!Number.isInteger(payload.next_update_at) || payload.next_update_at<=now() || payload.next_update_at>now()+30*86400)throw new Error('Expected update must be in the next 30 days');
        } else if(payload.next_update_at!==null)throw new Error('Terminal expectation needs a null deadline');
        return {...await publish(token,event),expectation_id};
      }
      if(operation==='observe_due') {
        if(!['listener','owner'].includes(principal.kind))throw new Error('Monitor or owner operation required');
        const expectation_id=reference(body.expectation_id),revision=reference(body.revision);
        const work=expectations.find(r=>r.id===expectation_id && allowedExpectation(r));
        if(!work || work.revisions.length!==1 || work.revisions[0].id!==revision || work.revisions[0].payload.status!=='working' || work.revisions[0].payload.next_update_at>now())throw new Error('Current scoped overdue expectation required');
        const next_update_at=work.revisions[0].payload.next_update_at;
        const payload={revision,next_update_at,observer:principal.id,observer_kind:principal.kind,environment:work.environment,condition:'expected_update_missing'};
        const event={schema:'unblock/1',intent_id:stableId('overdue:'+expectation_id+':'+revision+':'+principal.id),kind:'overdue',expectation_id,agent_id:work.agent_id,payload};
        return {...await publish(token,event),expectation_id};
      }
      if (operation==='delivery') {
        if (principal.kind!=='listener') throw new Error('Listener operation required');
        const request_id=text(body,'request_id',100),request=requests.find(r=>r.id===request_id && allowed(r));
        if (!request) throw new Error('Request not permitted');
        const revision=text(body,'revision',100),answers=body.answers;
        if (!request.history.some((/** @type {any} */ r)=>r.id===revision) || !Array.isArray(answers) || new Set(answers).size!==answers.length || answers.some(a=>![...request.answers,...request.stale_answers].some(r=>r.id===a && r.payload.revision===revision))) throw new Error('Invalid delivery snapshot');
        const disposition=text(body,'disposition',30);
        if (!['queued','failed','blocked','unknown'].includes(disposition)) throw new Error('Delivery cannot assert agent progress');
        return publish(token,{schema:'unblock/1',intent_id:text(body,'intent_id',160),kind:'delivery',request_id,agent_id:request.agent_id,payload:{revision,answers:[...answers].sort(),receiver:principal.id,environment:principal.environment,disposition,evidence:text(body,'evidence',16000)}});
      }
      if (principal.kind==='listener') throw new Error('Listener cannot mutate agent work');
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
        const kind=body.kind || 'agent',environment=body.environment || 'pilot';
        if (!['agent','listener'].includes(kind) || typeof environment!=='string' || !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$/.test(environment)) throw new Error('Invalid enrollment role or environment');
        const agent_ids=kind==='listener'?body.agent_ids:[agent_id];
        if (!Array.isArray(agent_ids) || !agent_ids.length || agent_ids.length>100 || agent_ids.some(id=>typeof id!=='string') || (kind==='listener' && agent_ids.some(id=>!events.some(e=>e.kind==='enroll' && e.agent_id===id && (e.payload.kind || 'agent')==='agent')))) throw new Error('Listener needs explicit enrolled agent IDs');
        const renewal_of=body.renewal_of==null?null:text(body,'renewal_of',100);
        if (renewal_of) {
          const parent=enrollmentRecord(renewal_of,events);
          if (parent.payload.name!==name || grantScope(parent.agent_id,parent.payload)!==grantScope(agent_id,{kind,environment,agent_ids})) throw new Error('Renewal must preserve the parent scope');
        }
        const grant_id=stableId(user.userid+':'+agent_id+':'+intent_id);
        const original=events.find(e=>e.kind==='enroll' && e.payload.grant_id===grant_id);
        const expires_at=body.expires_at ?? original?.payload.expires_at ?? (exp<=Math.floor(now())+3600?exp:NaN);
        if (!Number.isFinite(expires_at) || expires_at<=now() || expires_at>exp || expires_at>Math.floor(now())+3600) throw new Error('Prepare a stable enrollment expiry within the current session and one hour');
        if (original && (original.payload.name!==name || original.payload.expires_at!==expires_at || (original.payload.kind || 'agent')!==kind || (original.payload.environment || 'pilot')!==environment || (original.payload.renewal_of || null)!==renewal_of || JSON.stringify([...(original.payload.agent_ids || [agent_id])].sort())!==JSON.stringify([...agent_ids].sort()))) throw new Error('Enrollment intent already has different fields');
        const newGrant={agent_id,grant_id,kind,environment,agent_ids,renewal_of,owner_id:user.userid,expires_at,upstream:token};
        const saved=original?{record_id:original.id,visibility:'visible'}:await publish(token,{schema:'unblock/1',intent_id,kind:'enroll',agent_id,payload:{grant_id,name,expires_at,kind,environment,agent_ids,renewal_of}});
        return {...saved,agent_id,grant_id,kind,environment,agent_ids,expires_at,credential:sealAgent(newGrant,config.key)};
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
        const event={...base,payload:{revision,answer:text(body,'answer',16000),responder:user.userid}};
        const retry=canonicalRecord(event);
        if(rows.some(r=>r.id===retry.id && r.note===retry.note))return {record_id:retry.id,request_id,visibility:'visible'};
        if(request.state==='withdrawn')throw new Error('Request withdrawn; no new answer needed');
        if(body.reviewed_snapshot!==undefined && (!/^[a-f0-9]{64}$/.test(body.reviewed_snapshot) || request.revisions.length!==1 || request.revisions[0].id!==revision || decisionSnapshot(request)!==body.reviewed_snapshot))throw new Error('Decision changed; review again');
        return publish(token,event);
      }
      if (!agent) throw new Error('Enrolled agent required');
      if (operation==='progress') {
        const revision=text(body,'revision',100),stage=text(body,'stage',30),evidence=text(body,'evidence',16000);
        const answers=body.answers;
        if (Array.isArray(answers) && answers.every(a=>typeof a==='string')) {
          const retry=canonicalRecord({...base,payload:{revision,stage,evidence,answers:[...answers].sort(),reconciled:body.reconciled===true}});
          if(rows.some(r=>r.id===retry.id && r.note===retry.note)) return {record_id:retry.id,request_id,visibility:'visible'};
        }
        if(request.state==='withdrawn')throw new Error('Request withdrawn; revise it before reporting new progress');
        if (!['acknowledged','resumed','completed','withdrawn'].includes(stage) || !Array.isArray(answers) || (stage!=='withdrawn' && answers.length===0) || new Set(answers).size!==answers.length || answers.some(a=>!request.answers.some((/** @type {any} */ r)=>r.id===a)) || request.revisions.length!==1 || request.revisions[0].id!==revision || answers.length!==request.answers.length) throw new Error('Current question and complete answer set required');
        if(stage==='withdrawn' && request.uncertain_actions.length)throw new Error('Reconcile uncertain actions before withdrawal');
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
