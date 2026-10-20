<script>
  import { onMount } from 'svelte';
  import { requestView, waitingAge, excerpt, progressView } from '$lib/unblock-view.js';
  /** @type {{row:any,name:string,answerText:string,draft:any,pending:any,earlierPending:any[],onverify:(body:any)=>void,busy:boolean,sourceReady:boolean,now:number,onedit:(value:string)=>void,onreview:()=>void,onsend:()=>void,onclose:()=>void}} */
  let {
    row,
    name,
    answerText,
    draft,
    pending,
    earlierPending,
    onverify,
    busy,
    sourceReady,
    now,
    onedit,
    onreview,
    onsend,
    onclose
  } = $props();
  const view = $derived(requestView(row));
  const progress = $derived(progressView(row));
  /** @type {HTMLElement|undefined} */ let panel;
  onMount(() => {
    const previous = document.activeElement;
    panel?.focus({ preventScroll: true });
    const escape = (/** @type {KeyboardEvent} */ event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onclose();
      }
    };
    window.addEventListener('keydown', escape);
    return () => {
      window.removeEventListener('keydown', escape);
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus({ preventScroll: true });
    };
  });
</script>

<aside class="decision-panel" aria-label="Selected request" tabindex="-1" bind:this={panel}>
  <header class="detail-toolbar">
    <span>DECISION DETAILS</span><button
      onclick={onclose}
      class="icon-button"
      aria-label="Close request">✕</button
    >
  </header>
  <div class="detail-body">
    <div class="detail-agent">
      <span class="agent-avatar large">{name.slice(0, 2).toUpperCase()}</span>
      <div>
        <strong>{name}</strong>
        <p>{view.status}</p>
      </div>
    </div>
    <p class="detail-age">
      ◷ Requested {row.created_at
        ? new Date(row.created_at).toLocaleString()
        : 'at an unknown time'}{#if row.created_at && view.lane === 'attention'}
        · waiting {waitingAge(row.created_at, now)}{/if}
    </p>
    {#each row.revisions as revision}
      <h2>{revision.payload.need}</h2>
      {#if progress && row.revisions.length === 1}
        <section class="progress-summary" aria-label="Last observed agent progress">
          <h3>{progress.title}</h3>
          <p>{excerpt(progress.evidence, 220)}</p>
          {#if progress.at}<p class="progress-time">
              Observed {new Date(progress.at).toLocaleString()}
            </p>{/if}
          {#if progress.evidence.length > 220}<details class="detail-section">
              <summary>Read full progress</summary>
              <p>{progress.evidence}</p>
            </details>{/if}
        </section>
      {/if}
      <section class="decision-context">
        <h3>What you need to know</h3>
        <p>{excerpt(revision.payload.context, 400)}</p>
        {#if revision.payload.context.length > 400}<details class="detail-section">
            <summary>Read full context</summary>
            <p>{revision.payload.context}</p>
          </details>{/if}
      </section>
      <section class="recommendation">
        <h3>Agent’s recommendation</h3>
        <p>{excerpt(revision.payload.recommendation, 300)}</p>
        {#if revision.payload.recommendation.length > 300}<details class="detail-section">
            <summary>Read full recommendation</summary>
            <p>{revision.payload.recommendation}</p>
          </details>{/if}
      </section>
      <details class="detail-section">
        <summary>What happens next</summary>
        <p>{revision.payload.next_action}</p>
      </details>
    {/each}
    {#if row.answers.length}<details
        class="detail-section"
        open={row.state === 'answer_conflict' || view.lane === 'done'}
      >
        <summary>Your answers ({row.answers.length})</summary>{#each row.answers as a}<blockquote>
            {a.payload.answer}
          </blockquote>{/each}
      </details>{/if}
    {#if row.revisions.length !== 1}<p class="warning-note">
        The agent has conflicting versions of this question. It needs to reconcile them before you
        answer.
      </p>
    {:else if view.lane !== 'done'}
      <section class="answer-section">
        <h3>{row.answers.length ? 'Add a clarification' : 'Your decision'}</h3>
        <textarea
          aria-label="Your decision"
          rows="3"
          maxlength="16000"
          value={answerText}
          oninput={(e) => onedit(e.currentTarget.value)}
          disabled={!!pending}
          placeholder="Give the agent what it needs to move forward…"
        ></textarea>
        {#if draft && !pending && draft.revision !== row.revisions[0].id}<p class="warning-note">
            The question changed while you were writing. Review it before sending.
          </p>
          <button class="quiet-button" onclick={onreview}>I reviewed the updated question</button
          >{/if}
        <button
          class="primary-button"
          disabled={busy ||
            !sourceReady ||
            (!pending && (!answerText.trim() || draft?.revision !== row.revisions[0].id))}
          onclick={onsend}
          >{pending ? 'Retry saved answer' : 'Send decision'}<span aria-hidden="true">↗</span
          ></button
        >
        <p class="answer-help">
          {pending
            ? 'Verifying your saved answer. Retrying sends the same decision.'
            : 'Send your decision to save it to this request. Agent progress will appear below.'}
        </p>
      </section>
    {/if}
    {#each earlierPending as original (original.intent_id)}<section class="verification">
        <h3>Earlier answer needs verification</h3>
        <p>
          Its outcome is still uncertain. Answering this question does not withdraw the earlier
          submission.
        </p>
        <blockquote>{original.answer}</blockquote>
        <button
          class="quiet-button"
          disabled={busy || !sourceReady}
          onclick={() => onverify(original)}>Verify earlier answer</button
        >
      </section>{/each}
    {#if row.uncertain_actions.length}<section class="verification">
        <h3>Action needs verification</h3>
        {#each row.uncertain_actions as a}<p>{a.payload.effect}</p>{/each}
        <p class="answer-help">Check what happened before repeating this action.</p>
      </section>{/if}
    {#if row.progress.length}<details class="detail-section">
        <summary>Agent progress history ({row.progress.length})</summary>
        {#each row.progress as p}<div class="progress-entry">
            <span class="status-dot waiting"></span>
            <div>
              <strong
                >{p.payload.stage === 'withdrawn'
                  ? 'No longer needed'
                  : p.payload.stage === 'completed'
                    ? 'Completed'
                    : p.payload.stage === 'resumed'
                      ? 'Work resumed'
                      : 'Answer read'}</strong
              >
              <p>{p.payload.evidence}</p>
            </div>
          </div>{/each}
      </details>{/if}
    <details class="detail-section">
      <summary>Earlier context & activity</summary>
      {#each row.history as h}<p>{h.payload.need}</p>
        <p class="muted">{h.payload.context}</p>{/each}
      {#each row.stale_answers as a}<blockquote>
          Earlier answer: {a.payload.answer}
        </blockquote>{/each}
      {#each row.deliveries || [] as d}<p>
          Delivery: {d.payload.disposition}. {d.payload.evidence}
        </p>{/each}
      {#each row.settlements || [] as s}<p>Verified: {s.payload.evidence}</p>{/each}
      <p class="record-reference">Request {row.id}</p>
    </details>
  </div>
</aside>
