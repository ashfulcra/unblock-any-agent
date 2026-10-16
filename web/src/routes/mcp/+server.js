import {env as privateEnv} from '$env/dynamic/private';
import {env} from '$env/dynamic/public';
import {createService} from '$lib/server/unblock-api.js';
import {createNativeMcp} from '$lib/server/unblock-mcp.js';

// Process configuration only; the SDK creates a fresh worker server per request.
/** @type {ReturnType<typeof createNativeMcp>|undefined} */
let endpoint;
/** @param {import('@sveltejs/kit').RequestEvent} event */
async function handle({request}) {
 if(!privateEnv.UNBLOCK_MCP_ORIGIN)return Response.json({error:'native_mcp_origin_not_configured'},{status:503,headers:{'Cache-Control':'no-store'}});
 try {
  endpoint ??= createNativeMcp({origin:privateEnv.UNBLOCK_MCP_ORIGIN,service:createService({ownerId:privateEnv.OWNER_USER_ID,annotation:privateEnv.UNBLOCK_ANNOTATION_ID,key:privateEnv.UNBLOCK_AGENT_KEY,apiEndpoint:env.PUBLIC_FULCRA_API_ENDPOINT})});
  return await endpoint.fetch(request);
 } catch {return Response.json({error:'native_mcp_configuration_unavailable_work_remains_pending'},{status:503,headers:{'Cache-Control':'no-store'}});}
}
export const POST=handle;
export const GET=handle;
export const DELETE=handle;
export const OPTIONS=handle;
