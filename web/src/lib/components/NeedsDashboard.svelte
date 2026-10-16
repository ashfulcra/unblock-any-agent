<script>
  import { editDraft, reviewDraft, submitDraft } from '$lib/answer-draft.js';
  import { onMount } from 'svelte';
  /** @type {any[]} */ let requests=$state([]);
  /** @type {any[]} */ let grants=$state([]);
  let error=$state('');
  let checked=$state('');
  let busy=$state(false);
  let agentId=$state('');
  let agentName=$state('');
  let credential=$state('');
  let expires=$state('');
  let notice=$state('');
  /** @type {Record<string,string>} */ let answers=$state({});
  /** @type {Record<string,any>} */ let drafts=$state({});
  /** @type {Record<string,any>} */ let pending=$state({});

  async function refresh() {
    try {
      const res=await fetch('/api/unblock/attention');const data=await res.json();
      if(!res.ok)throw new Error(data.error);
      requests=data.requests;grants=data.grants;checked=data.checked_at;error='';
      for(const [id,body] of Object.entries(pending)) {
        const row=requests.find(r=>r.id===id);
        if(row && [...row.answers,...row.stale_answers].some(a=>a.intent_id===body.intent_id && a.payload.answer===body.answer)) {
          delete pending[id];delete drafts[id];delete answers[id];sessionStorage.removeItem('unblock-answer:'+id);sessionStorage.removeItem('unblock-draft:'+id);notice='Answer read back. Current agent progress appears on the request card.';
        }
      }
    } catch(e) {error=(/** @type {Error} */(e)).message;}
  }
  /** @param {string} operation @param {any} body */
  async function post(operation,body) {
    const res=await fetch('/api/unblock/'+operation,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await res.json();if(!res.ok)throw new Error(data.error);return data;
  }
  async function enroll() {
    busy=true;error='';credential='';
    try {
      const data=await post('enroll',{intent_id:crypto.randomUUID(),agent_id:agentId,name:agentName});
      credential=data.credential;expires=new Date(data.expires_at*1000).toLocaleString();notice=data.visibility==='visible'?'Enrollment is visible.':'Enrollment accepted; wait for it to appear below before using the credential.';
      await refresh();
    } catch(e){error=(/** @type {Error} */(e)).message;}finally{busy=false;}
  }
  /** @param {any} row */
  async function answer(row) {
    const revision=row.revisions[0];
    if(!pending[row.id]) {
      try { pending[row.id]=submitDraft(drafts[row.id],revision.id); } catch(e) {error=(/** @type {Error} */(e)).message;return;}
      sessionStorage.setItem('unblock-answer:'+row.id,JSON.stringify(pending[row.id]));
    }
    busy=true;error='';
    try {
      const data=await post('answer',pending[row.id]);notice=data.visibility==='visible'?'Answer read back. Waiting for agent pickup.':'Answer accepted; checking native persistence. This does not mean the agent resumed.';
      await refresh();
    }catch(e){error=(/** @type {Error} */(e)).message;}finally{busy=false;}
  }
  /** @param {any} grant */
  async function revoke(grant) {
    busy=true;error='';
    try{const data=await post('revoke',{intent_id:crypto.randomUUID(),grant_id:grant.grant_id});notice=data.visibility==='visible'?'Revocation read back.':'Revocation pending native processing; access is not yet confirmed revoked.';await refresh();}
    catch(e){error=(/** @type {Error} */(e)).message;}finally{busy=false;}
  }
  onMount(()=>{
    for(let i=0;i<sessionStorage.length;i++) {
      const k=sessionStorage.key(i);
      if(k?.startsWith('unblock-draft:'))try{const body=JSON.parse(sessionStorage.getItem(k)||'null');if(body?.request_id){drafts[body.request_id]=body;answers[body.request_id]=body.answer;}}catch{}
      if(k?.startsWith('unblock-answer:'))try{const body=JSON.parse(sessionStorage.getItem(k)||'null');if(body?.request_id){pending[body.request_id]=body;answers[body.request_id]=body.answer;}}catch{}
    }
    refresh();const timer=setInterval(refresh,5000);return ()=>clearInterval(timer);
  });
</script>

<section class="mx-auto w-full max-w-4xl px-5 py-8 text-fulcra-white">
  <div class="mb-6 flex items-start justify-between gap-4">
    <div><h1 class="text-3xl font-semibold">Needs you</h1><p class="mt-2 text-sm opacity-75">Answer an agent, then see what it actually did next.</p></div>
    <button class="btn btn-sm" onclick={refresh}>Check now</button>
  </div>
  <p class="mb-4 text-sm opacity-65">Single-owner pilot · no automatic pickup is claimed until a listener is connected.</p>
  {#if error}<p role="alert" class="mb-4 rounded border border-red-400 p-3">{error}. Last known work remains below.</p>{/if}
  {#if notice}<p role="status" class="mb-4 rounded border border-fulcra-teal p-3">{notice}</p>{/if}
  {#if checked}<p class="mb-4 text-xs opacity-60">Last successful check: {new Date(checked).toLocaleString()}</p>{/if}
  {#if checked && !requests.length}<p class="rounded border border-white/20 p-5">No requests found in the checked source. Enroll an agent below to connect its work.</p>{/if}
  {#each requests as row (row.id)}
    <article class="mb-5 rounded-xl border border-white/20 bg-white/5 p-5">
      <p class="mb-2 text-sm text-fulcra-teal">{grants.find(g=>g.agent_id===row.agent_id)?.name || row.agent_id} · {row.state.replaceAll('_',' ')}</p>
      {#each row.revisions as revision}
        <h2 class="text-xl font-semibold">{revision.payload.need}</h2>
        <p class="mt-3 whitespace-pre-wrap">{revision.payload.context}</p>
        <p class="mt-3 text-sm"><strong>Recommendation:</strong> {revision.payload.recommendation}</p>
        <p class="mt-2 text-sm"><strong>Next action:</strong> {revision.payload.next_action}</p>
      {/each}
      {#if row.revisions.length>1}<p class="mt-3">Conflicting question revisions need agent reconciliation before answering.</p>
      {:else}
        <label class="mt-4 block" for={'answer-'+row.id}>Your answer</label>
        <textarea id={'answer-'+row.id} class="textarea mt-2 w-full bg-black/30 text-white" rows="3" bind:value={answers[row.id]} oninput={(e)=>{drafts[row.id]=editDraft(drafts[row.id],row.id,row.revisions[0].id,e.currentTarget.value);sessionStorage.setItem('unblock-draft:'+row.id,JSON.stringify(drafts[row.id]));}} disabled={!!pending[row.id]}></textarea>
        {#if drafts[row.id] && !pending[row.id] && drafts[row.id].revision!==row.revisions[0].id}
          <p class="mt-3" role="alert">The question changed while you were composing. Review the current question before sending this draft.</p>
          <button class="btn mt-2" onclick={()=>{drafts[row.id]=reviewDraft(drafts[row.id],row.revisions[0].id);sessionStorage.setItem('unblock-draft:'+row.id,JSON.stringify(drafts[row.id]));}}>I reviewed the updated question</button>
        {/if}
        <button class="btn mt-3 bg-fulcra-teal text-black" disabled={busy || (!pending[row.id] && (!answers[row.id]?.trim() || drafts[row.id]?.revision!==row.revisions[0].id))} onclick={()=>answer(row)}>{pending[row.id]?'Retry same pending answer':'Send answer'}</button>
        {#if pending[row.id]}<p class="mt-2 text-sm">Pending readback. Retrying reuses the same answer; it does not create a new decision.</p>{/if}
      {/if}
      {#if row.answers.length}
        <h3 class="mt-4 font-semibold">Answers</h3>
        {#each row.answers as a}<p class="mt-2 whitespace-pre-wrap">{a.payload.answer}</p>{/each}
        {#if row.state==='awaiting_pickup'}<p class="mt-3 text-sm">Answer available; no agent acknowledgment observed yet.</p>{/if}
      {/if}
      {#if row.stale_answers.length}<p class="mt-3 text-sm">{row.stale_answers.length} historical answer(s) belong to an earlier question and remain retained.</p>{/if}
      {#each row.progress as p}<p class="mt-3 text-sm"><strong>{p.payload.stage}:</strong> {p.payload.evidence}</p>{/each}
      {#each row.uncertain_actions as action}<p class="mt-3 rounded border border-amber-400 p-3">Needs verification: {action.payload.effect}</p>{/each}
    </article>
  {/each}
  <details class="mt-8 rounded-xl border border-white/20 p-5">
    <summary class="cursor-pointer text-lg font-semibold">Connect an agent</summary>
    <p class="mt-3 text-sm">Credentials are limited to the enrolled agent and expire with this sign-in session, within one hour. Renew enrollment when expired. Keep them in the agent's private credential storage.</p>
    <label class="mt-4 block" for="agent-id">Agent ID</label><input id="agent-id" class="input mt-1 w-full bg-black/30 text-white" placeholder="my-agent" bind:value={agentId}/>
    <label class="mt-3 block" for="agent-name">Display name</label><input id="agent-name" class="input mt-1 w-full bg-black/30 text-white" bind:value={agentName}/>
    <button class="btn mt-4" disabled={busy || !agentId || !agentName} onclick={enroll}>Enroll agent</button>
    {#if credential}
      <label class="mt-4 block" for="agent-credential">Private agent credential · expires {expires}</label>
      <textarea id="agent-credential" class="textarea mt-2 w-full bg-black/30 text-white" readonly value={credential} rows="3"></textarea>
      <button class="btn btn-sm mt-2" onclick={()=>{credential='';}}>Hide credential</button>
    {/if}
    <ul class="mt-4 space-y-2">{#each grants as grant (grant.grant_id)}<li>{grant.name} · {grant.revoked?'revoked':new Date(grant.expires_at*1000).getTime()<Date.now()?'expired':'enrolled'} {#if !grant.revoked}<button class="btn btn-xs ml-2" disabled={busy} onclick={()=>revoke(grant)}>Revoke</button>{/if}</li>{/each}</ul>
  </details>
  <p class="mt-6 text-sm"><a class="underline" href="https://github.com/ashfulcra/unblock-any-agent/blob/main/docs/native-pilot.md" target="_blank" rel="noopener noreferrer">Agent setup and pilot limits</a></p>
</section>
