import {createHash} from 'node:crypto';
import {createMcpHandler,McpServer} from '@modelcontextprotocol/server';
import * as z from 'zod/v4';

/** @param {any} value @returns {any} */
function sorted(value) {
 if(Array.isArray(value))return value.map(sorted);
 if(value && typeof value==='object')return Object.fromEntries(Object.keys(value).sort().map(k=>[k,sorted(value[k])]));
 return value;
}
/** Match Python native_mcp.intent's sorted ASCII JSON, including surrogate pairs.
 * @param {string} label @param {any} payload */
function intent(label,payload) {
 const ascii=JSON.stringify(sorted(payload)).replace(/[\u007f-\uffff]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
 return label+'-'+createHash('sha256').update(ascii).digest('hex');
}
/** @param {unknown} error */
function failure(error) {
 const e=/** @type {Error & {publication_uncertain?:boolean}} */(error);
 if(e?.publication_uncertain)return 'native_write_uncertain_retain_same_intent_and_check_readback';
 if(/unavailable|unverified|integrity|Unexpected native/i.test(e?.message || ''))return 'source_unavailable_work_remains_pending';
 return 'native_operation_rejected_check_current_work_and_retain_prior_uncertainty';
}
/** @param {any} service @param {string} token */
function workerServer(service,token) {
 const server=new McpServer({name:'unblock',version:'0.4.0'},{instructions:'Recover owned work before acting. Pending receipts require exact readback. Review the current question and complete answer set; reconcile uncertain actions before effects. This transport supplies no owner authentication, command execution, background listener, OAuth flow or event subscription.'});
 const read={readOnlyHint:true,destructiveHint:false,openWorldHint:false};
 const write={readOnlyHint:false,destructiveHint:false,openWorldHint:false};
 const ref=z.uuid(),text=z.string().min(1),key=text.max(160);
 const question={need:text.max(4000),context:text.max(16000),recommendation:text.max(4000),next_action:text.max(4000)};
 /** @param {string} op @param {any} [body] */
 async function native(op,body={}) {return service.handle(op,{token,body});}
 /** @param {()=>Promise<any>} operation */
 async function result(operation) {
  try {const value=await operation();return {content:[{type:/** @type {const} */('text'),text:JSON.stringify(value)}],structuredContent:value};}
  catch(error){return {isError:true,content:[{type:/** @type {const} */('text'),text:failure(error)}]};}
 }
 server.registerTool('ask_for_help',{description:'Save an owned need with a stable key and useful continuity context. Retry identical fields; read back a pending receipt.',inputSchema:z.strictObject({key,...question}),annotations:write},args=>result(()=>native('request',{intent_id:args.key,need_key:args.key,need:args.need,context:args.context,recommendation:args.recommendation,next_action:args.next_action,parents:[]})));
 server.registerTool('recover_work',{description:'Read this worker’s retained needs, current and historical answers, actions, settlements and progress. Failed source is unknown.',inputSchema:z.strictObject({}),annotations:read},()=>result(()=>native('attention')));
 server.registerTool('get_work',{description:'Recover one owned request and its continuity history.',inputSchema:z.strictObject({request_id:ref}),annotations:read},args=>result(async()=> (await native('recover',args)).requests[0]));
 server.registerTool('revise_need',{description:'Correct context against the exact reviewed parent revisions. Concurrent unreviewed questions remain conflicts.',inputSchema:z.strictObject({request_id:ref,parent_revisions:z.array(ref),...question}),annotations:write},args=>result(async()=>{
  const work=(await native('recover',{request_id:args.request_id})).requests[0];
  const payload={need_key:work.revisions[0].payload.need_key,need:args.need,context:args.context,recommendation:args.recommendation,next_action:args.next_action,parents:[...args.parent_revisions].sort()};
  return native('request',{intent_id:intent('revise',payload),...payload});
 }));
 server.registerTool('record_progress',{description:'Record observed continuation using the reviewed question and full current answer set. Reconciled means actual reconciliation; stale retries stay historical.',inputSchema:z.strictObject({request_id:ref,revision:ref,answer_ids:z.array(ref),stage:z.enum(['acknowledged','resumed','completed']),evidence:text.max(16000),reconciled:z.boolean().default(false)}),annotations:write},args=>result(()=>{
  const payload={request_id:args.request_id,revision:args.revision,answers:[...args.answer_ids].sort(),stage:args.stage,evidence:args.evidence,reconciled:args.reconciled};
  return native('progress',{intent_id:intent('progress',payload),...payload});
 }));
 server.registerTool('begin_action',{description:'Retain and read back a stable action intent before an authorized effect. This tool executes nothing.',inputSchema:z.strictObject({request_id:ref,key:text.max(200),description:text.max(16000)}),annotations:write},args=>result(()=>native('action',{request_id:args.request_id,intent_id:args.key,effect:args.description})));
 server.registerTool('reconcile_action',{description:'Record actual checked action evidence; never blindly repeat an uncertain external effect.',inputSchema:z.strictObject({request_id:ref,action_id:ref,evidence:text.max(16000)}),annotations:write},args=>result(()=>{
  const payload={request_id:args.request_id,action:args.action_id,evidence:args.evidence};return native('settle',{intent_id:intent('settle',payload),...payload});
 }));
 return server;
}
/** @param {string} value */
function canonicalOrigin(value) {
 try {const u=new URL(value);if((u.protocol!=='https:' && !(u.protocol==='http:' && ['localhost','127.0.0.1','[::1]'].includes(u.hostname))) || u.username || u.password || u.pathname!=='/' || u.search || u.hash)return null;return u.origin;}catch{return null;}
}
/** @param {{service:any,origin:string}} config */
export function createNativeMcp({service,origin}) {
 const expected=canonicalOrigin(origin);
 const handler=createMcpHandler(({authInfo})=>workerServer(service,authInfo?.token || ''),{legacy:'stateless'});
 /** @param {string} code @param {number} status */
 const reject=(code,status)=>Response.json({error:code},{status,headers:{'Cache-Control':'no-store',...(status===401?{'WWW-Authenticate':'Bearer realm="unblock", error="invalid_token"'}:{})}});
 return {
  close:()=>handler.close(),
  /** @param {Request} request */
  async fetch(request) {
   if(!expected)return reject('native_mcp_origin_not_configured',503);
   const url=new URL(request.url),host=request.headers.get('host'),browserOrigin=request.headers.get('origin');
   if(url.origin!==expected || (host && host.toLowerCase()!==new URL(expected).host) || (browserOrigin && browserOrigin!==expected))return reject('native_mcp_origin_not_permitted',403);
   if(request.method!=='POST')return reject('native_mcp_post_required',405);
   const authorization=request.headers.get('authorization');
   if(!authorization?.startsWith('Bearer ') || authorization.length<=7 || authorization.length>20007 || authorization.slice(7).trim()!==authorization.slice(7))return reject('native_worker_enrollment_required',401);
   if(!request.headers.get('content-type')?.startsWith('application/json'))return reject('native_mcp_json_required',415);
   let body;
   try {
    const reader=request.body?.getReader();if(!reader)return reject('native_mcp_empty_request',400);
    const chunks=[];let size=0;
    while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>65536){await reader.cancel();return reject('native_mcp_request_too_large',413);}chunks.push(value);}
    body=new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks));
   } catch {return reject('native_mcp_invalid_request',400);}
   const token=authorization.slice(7);
   try {
    const principal=await service.handle('identity',{token,body:{}});
    if(principal.kind!=='agent')return reject('native_worker_role_required',403);
    const headers=new Headers(request.headers);headers.delete('content-length');
    const response=await handler.fetch(new Request(request.url,{method:'POST',headers,body,signal:request.signal}),{authInfo:{token,clientId:principal.id,scopes:[]}});
    response.headers.set('Cache-Control','no-store');return response;
   } catch(error) {
    const message=/** @type {Error} */(error).message || '';
    const source=/unavailable|unverified|integrity|not configured|Unexpected native/i.test(message);
    return reject(source?'source_unavailable_work_remains_pending':'native_enrollment_expired_or_revoked',source?503:401);
   }
  }
 };
}
