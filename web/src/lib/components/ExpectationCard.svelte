<script>
  /** @type {{row:any,busy:boolean,pending:any[],allowCheck:boolean,oncheck:(row:any,original?:any)=>Promise<void>}} */
  let {row,busy,pending,allowCheck,oncheck}=$props();
</script>

<article id={'expectation-'+row.id} class="my-4 rounded-xl border border-amber-200/30 bg-white/5 p-5">
  <p class="text-sm text-fulcra-teal">{row.agent_id} · {row.state.replaceAll('_',' ')}</p>
  {#each row.revisions as revision}
    <h3 class="mt-2 text-lg font-semibold">{revision.payload.summary}</h3>
    <p class="mt-2 whitespace-pre-wrap">{revision.payload.context}</p>
    <p class="mt-2 text-sm"><strong>Latest update:</strong> {revision.payload.evidence}</p>
    <p class="mt-2 text-sm"><strong>Next action:</strong> {revision.payload.next_action}</p>
    {#if revision.payload.status==='working'}<p class="mt-2 text-sm">Update expected by {new Date(revision.payload.next_update_at*1000).toLocaleString()}</p>{/if}
  {/each}
  {#if row.state==='conflict'}<p class="mt-3">Concurrent updates need agent reconciliation. No deadline was silently chosen.</p>
  {:else if row.state==='investigate'}<p class="mt-3">A missed update was recorded. Its cause is unknown. This concern is available when the agent checks its work; automatic follow-up has not been verified.</p>
  {:else if row.state==='due'}<p class="mt-3">The declared update is overdue. No persisted check is visible yet.</p>{/if}
  {#if row.link_conflict}<p class="mt-3">Conflicting linked questions need explicit agent reconciliation. Every question remains separately pending.</p>{/if}
  {#each row.request_ids || (row.request_id?[row.request_id]:[]) as id}<a class="mt-3 block text-sm underline" href={'#request-'+id}>{id===row.request_id?'Related human question':'Retained linked human question'} — its answers and verification remain separate</a>{/each}
  {#if ['due','investigate'].includes(row.state)}
    <button class="btn btn-sm mt-3" disabled={busy || !allowCheck} onclick={()=>oncheck(row)}>{pending.some(p=>p.revision===row.revisions[0].id)?'Retry current pending check':'Check this update'}</button>
  {/if}
  {#each pending as body}
    <p class="mt-2 text-sm">Check pending readback for revision {body.revision}. Its original receipt remains retained.</p>
    {#if row.revisions.length!==1 || body.revision!==row.revisions[0].id || !['due','investigate'].includes(row.state)}<button class="btn btn-sm mt-2" disabled={busy || !allowCheck} onclick={()=>oncheck(row,body)}>Retry original pending check</button>{/if}
  {/each}
  <details class="mt-3 text-sm">
    <summary class="cursor-pointer">Retained update and concern history</summary>
    {#each row.history as update}<p class="mt-2"><strong>{update.payload.status}:</strong> {update.payload.evidence}</p>{/each}
    {#each row.observations as observation}<p class="mt-2">Missed update recorded by {observation.payload.observer_kind==='owner'?'an owner check':'an environment monitor'} for {new Date(observation.payload.next_update_at*1000).toLocaleString()}. {row.current_observations.some((/** @type {any} */ o)=>o.id===observation.id)?'Current concern.':'Historical concern retained.'}</p>{/each}
  </details>
</article>
