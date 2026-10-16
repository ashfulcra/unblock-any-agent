import { createHmac, randomBytes } from 'node:crypto';
import { createService } from '../../src/lib/server/unblock-api.js';

// External Fulcra processing is represented by accepted and then visible records;
// all authority, sealing, scope, projection and pending/readback logic is real.
export function fixture(expires=2000) {
 let clock=1000;
 /** @type {any[]} */ let visible=[];
 /** @type {any[]} */ let accepted=[];
 let offline=false,failAfterWrite=false;
 /** @type {{after:number,kind:string}|null} */ let sourceFault=null;
 const owner='owner-account';
 const token='header.'+Buffer.from(JSON.stringify({exp:expires})).toString('base64url')+'.signature';
 const key=randomBytes(32).toString('hex');
 const service=createService({ownerId:owner,annotation:'MomentAnnotation/11111111-1111-4111-a111-111111111111',key,now:()=>clock,fetch:async(/** @type {string} */ url,/** @type {any} */ options)=>{
   if(sourceFault && sourceFault.after--<=0){
    if(sourceFault.kind==='network')throw new TypeError('fetch failed');
    if(sourceFault.kind==='timeout')throw new DOMException('The operation was aborted due to timeout','TimeoutError');
    return new Response('invalid upstream JSON',{status:200});
   }
   const path=new URL(url).pathname;
   if(path==='/user/v1alpha1/info') return Response.json({userid:options.headers.Authorization==='Bearer '+token ? owner:'foreign'});
   if(offline) return new Response('unavailable',{status:503});
   if(path.startsWith('/data/')) return Response.json(visible);
   if(path==='/ingest/v1/record/MomentAnnotation') {const row=JSON.parse(options.body);if(!accepted.some(x=>x.id===row.id))accepted.push(row);if(failAfterWrite)offline=true;return Response.json({upload_id:'accepted'},{status:201});}
   throw Error('Unexpected upstream path '+path);
 }});
 return {service,token,seedEvents:(/** @type {any[]} */ rows)=>{accepted.push(...rows.map(row=>({...row,note:JSON.stringify({note:row.note,mac:createHmac('sha256',key).update('unblock-record/1:'+row.note).digest('hex')})})));visible=[...accepted]},sourceFault:(/** @type {string} */ kind,after=0)=>{sourceFault={kind,after}},corrupt:(/** @type {string} */ note)=>{visible=[{id:"bad",note}]},failAfterWrite:()=>{failAfterWrite=true},advance:(/** @type {number} */ seconds)=>{clock+=seconds},publish:()=>{visible=[...accepted]},fail:()=>{offline=true}};
}
