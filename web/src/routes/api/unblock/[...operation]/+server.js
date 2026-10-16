import { env as privateEnv } from '$env/dynamic/private';
import { env } from '$env/dynamic/public';
import { json } from '@sveltejs/kit';
import { createService } from '$lib/server/unblock-api.js';

/** @param {import('@sveltejs/kit').RequestEvent} event */
async function handle({request,cookies,params,url}) {
  const headers={'Cache-Control':'no-store'};
  const operation=params.operation || '';
  const bearer=request.headers.get('authorization');
  if (bearer && !bearer.startsWith('Bearer ')) return json({outcome:'rejected',error:'Invalid authorization'},{status:401,headers});
  const token=bearer?.slice(7);
  if (request.method==='POST' && !token && request.headers.get('origin')!==url.origin) return json({outcome:'rejected',error:'Same-origin owner request required'},{status:403,headers});
  if (request.method==='GET' && !['identity','prepare_enrollment','attention','recover'].includes(operation)) return json({outcome:'rejected',error:'POST required'},{status:405,headers});
  try {
    let body={};
    if (request.method==='POST') {
      if (!request.headers.get('content-type')?.startsWith('application/json')) return json({outcome:'rejected',error:'JSON required'},{status:415,headers});
      const reader=request.body?.getReader();
      if (!reader) throw new Error('Empty request');
      const chunks=[];let size=0;
      while (true) {
        const {done,value}=await reader.read();if(done)break;
        size+=value.length;if(size>65536){await reader.cancel();return json({outcome:'rejected',error:'Request too large'},{status:413,headers});}chunks.push(value);
      }
      body=JSON.parse(Buffer.concat(chunks).toString('utf8'));
    } else body={request_id:url.searchParams.get('request_id') || undefined};
    const service=createService({ownerId:privateEnv.OWNER_USER_ID,annotation:privateEnv.UNBLOCK_ANNOTATION_ID,key:privateEnv.UNBLOCK_AGENT_KEY,apiEndpoint:env.PUBLIC_FULCRA_API_ENDPOINT});
    const result=await service.handle(operation,{body,token,cookieToken:token?undefined:cookies.get('fulcra_access_token')});
    return json(result,{status:result.visibility==='pending'?202:200,headers});
  } catch (err) {
    const message=(/** @type {Error} */ (err)).message;
    const status=message.includes('Authentication') || message.includes('credential') || message.includes('Agent enrollment')?401:message.includes('not configured') || message.includes('unavailable') || message.includes('Unverified') || message.includes('integrity')?503:400;
    return json({outcome:(/** @type {Error & {publication_uncertain?:boolean}} */(err)).publication_uncertain?'uncertain':'rejected',error:status===503?'Source unavailable; pending work is not known to be quiet':status===401?'Sign in or renew your agent enrollment':message},{status,headers});
  }
}
export const GET=handle;
export const POST=handle;
