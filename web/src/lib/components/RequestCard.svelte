<script>
  import { requestView, waitingAge } from '$lib/unblock-view.js';
  /** @type {{row:any,name:string,selected?:boolean,now?:number,onselect:(id:string)=>void}} */
  let { row, name, selected = false, now = Date.now(), onselect } = $props();
  const view = $derived(requestView(row));
  const since = $derived(view.lane === 'waiting' ? row.answered_at : row.created_at);
</script>

<button
  class:chosen={selected}
  class="work-card"
  onclick={() => onselect(row.id)}
  aria-label={'Open ' + view.title}
>
  <span class="card-top"
    ><span class="agent-avatar">{name.slice(0, 2).toUpperCase()}</span><span class="agent-name"
      >{name}</span
    ></span
  >
  <span
    class="card-age"
    title={since
      ? new Date(since).toLocaleString()
      : 'This older record has no available timestamp'}
    ><span aria-hidden="true">◷</span>
    {row.state === 'withdrawn'
      ? 'Closed'
      : view.lane === 'done'
        ? 'Finished'
        : view.lane === 'waiting'
          ? 'With agent'
          : 'Waiting'} · {view.lane === 'done'
      ? row.withdrawn_at || row.completed_at
        ? new Date(row.withdrawn_at || row.completed_at).toLocaleDateString()
        : 'date unknown'
      : waitingAge(since, now)}</span
  >
  <strong class="card-title">{view.title}</strong>
  <span class="card-context">{view.context || 'Open this request to review its context.'}</span>
  <span class="card-bottom"
    ><span class={'status-dot ' + view.lane}></span>{view.status}<span
      class="card-arrow"
      aria-hidden="true">↗</span
    ></span
  >
</button>
