<script>
  import {onMount} from 'svelte';
  import {failedAnswer} from '$lib/answer-draft.js';
  import {checkKey,currentCheck,pendingChecks} from '$lib/unblock-attention.js';
  import ExpectationCard from './ExpectationCard.svelte';
  /** @type {{rows:any[],ownerId:string,sourceReady:boolean,refresh:()=>Promise<void>}} */
  let {rows,ownerId,sourceReady,refresh}=$props();
  /** @type {Record<string,any>} */ let pending=$state({});
  let error=$state(''),notice=$state(''),busy=$state(false);
  const active=$derived(rows.filter(r=>['due','investigate','conflict'].includes(r.state)));
  const other=$derived(rows.filter(r=>!['due','investigate','conflict'].includes(r.state)));
  /** @param {string} id @param {any} value */
  function retain(id,value) {
    if(value){pending[id]=value;sessionStorage.setItem('unblock-observe:'+id,JSON.stringify(value));}
    else{delete pending[id];sessionStorage.removeItem('unblock-observe:'+id);}
  }
  $effect(()=>{
    if(!sourceReady || !ownerId)return;
    for(const [id,body] of Object.entries(pending)) {
      const row=rows.find(r=>r.id===body.expectation_id);
      if(row?.observations.some((/** @type {any} */ o)=>o.payload.revision===body.revision && o.payload.observer===ownerId && o.payload.observer_kind==='owner' && (!body._receipt || o.id===body._receipt))) {
        retain(id,null);notice='Concern read back. This check does not assert agent acknowledgment or resumed work.';
      }
    }
  });
  /** @param {any} row @param {any} [original] */
  async function observe(row,original=null) {
    const body=original || currentCheck(row,pending),id=checkKey(body);
    retain(id,body);busy=true;error='';notice='';
    try {
      const res=await fetch('/api/unblock/observe_due',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({expectation_id:body.expectation_id,revision:body.revision})});
      const data=await res.json();
      if(!res.ok){retain(id,failedAnswer(body,data.outcome || 'uncertain'));throw new Error(data.error);}
      retain(id,{...body,_uncertain:true,_receipt:data.record_id});notice='Check accepted; verifying the exact concern in retained history.';await refresh();
    }catch(e){if(pending[id])retain(id,failedAnswer(pending[id],'uncertain'));error=(/** @type {Error} */(e)).message;}
    finally{busy=false;}
  }
  onMount(()=>{
    for(let i=0;i<sessionStorage.length;i++) {
      const key=sessionStorage.key(i);
      if(key?.startsWith('unblock-observe:'))try{const body=JSON.parse(sessionStorage.getItem(key)||'null');if(!body?.expectation_id || !body?.revision)throw new Error('Invalid retained check');const id=checkKey(body);pending[id]=body;if(key!=='unblock-observe:'+id){sessionStorage.setItem('unblock-observe:'+id,JSON.stringify(body));sessionStorage.removeItem(key);i--;}}catch{error='A saved check could not be read. Keep its browser storage and reconcile the original revision before retrying.';}
    }
  });
</script>

<section class="my-8 border-y border-white/20 py-6" aria-labelledby="investigate-heading">
  <h2 id="investigate-heading" class="text-2xl font-semibold">Investigate</h2>
  <p class="mt-2 text-sm opacity-75">Declared updates and missed-update concerns. A concern does not by itself mean a human decision is needed.</p>
  <p class="mt-2 text-sm opacity-65">Persistent automatic checks have not been verified. Checking this page or an individual item does not start a background monitor.</p>
  {#if !sourceReady}<p role="alert" class="mt-3">Expected-update source unavailable. Last known work and pending checks remain below.</p>{/if}
  {#if error}<p role="alert" class="mt-3">{error}. Earlier uncertain checks remain pending.</p>{/if}
  {#if notice}<p role="status" class="mt-3">{notice}</p>{/if}
  {#if sourceReady && !active.length}<p class="mt-3">No current missed-update investigations in the checked source.</p>{/if}
  {#each active as row (row.id)}<ExpectationCard {row} {busy} pending={pendingChecks(row,pending)} allowCheck={sourceReady} oncheck={observe}/>{/each}
  {#if other.length}<details class="mt-4"><summary class="cursor-pointer">Other declared work and history ({other.length})</summary>{#each other as row (row.id)}<ExpectationCard {row} {busy} pending={pendingChecks(row,pending)} allowCheck={sourceReady} oncheck={observe}/>{/each}</details>{/if}
</section>
