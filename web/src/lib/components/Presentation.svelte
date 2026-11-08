<script>
  import { presentationRows, presentationStage } from '../presentation.js';
  import { requestView, excerpt } from '../unblock-view.js';
  /** @type {{rows:any[],ids:string[],grants:any[],checked:string,error:string,selectionError:string,onselect:(id:string)=>void}} */
  let { rows, ids, grants, checked, error, selectionError, onselect } = $props();
  const selected = $derived(presentationRows(rows, ids));
</script>

<section class="presentation" aria-label="Selected work presentation">
  <header class="presentation-intro">
    <p class="eyebrow">A DECISION. THEN THE WORK MOVES.</p>
    <h2>Your agents bring the question.<br />You make the call.</h2>
    <p>Review the context, send a decision, and follow the agent’s result.</p>
    <p class="presentation-source">
      {!checked
        ? 'Waiting for the workspace source.'
        : error
          ? 'Last known source · refresh failed'
          : 'Source checked · ' + new Date(checked).toLocaleTimeString()}
    </p>
  </header>
  {#if selectionError}<p role="alert" class="warning-note">{selectionError}</p>
  {:else if checked && selected.missing.length}<p role="alert" class="warning-note">
      {selected.missing.length} selected request{selected.missing.length === 1 ? ' is' : 's are'} unavailable
      in this source. Other work has not been substituted.
    </p>{/if}
  <div class="presentation-grid">
    {#each selected.rows as row (row.id)}
      {@const stage = presentationStage(row)}
      {@const view = requestView(row)}
      {@const name =
        grants.find((g) => g.agent_id === row.agent_id && g.kind !== 'listener')?.name ||
        row.agent_id}
      <article class={'presentation-card ' + stage.tone}>
        <div class="presentation-agent">
          <span class="agent-avatar">{name.slice(0, 2).toUpperCase()}</span><strong>{name}</strong
          ><span class="presentation-status">{stage.label}</span>
        </div>
        <h3>{view.title}</h3>
        <p>{view.context}</p>
        <ol class="presentation-steps" aria-label="Current work stage">
          {#each ['Decision', 'Saved', 'Agent work', 'Result'] as label, index}
            <li
              class:reached={stage.step > index}
              aria-current={stage.step === index + 1 ? 'step' : undefined}
            >
              <span>{index + 1}</span>{label}
            </li>
          {/each}
        </ol>
        {#if row.answers.length}<section class="presentation-answer">
            <h4>Decision received</h4>
            {#each row.answers as answer}<p>{answer.payload.answer}</p>{/each}
          </section>{/if}
        {#if stage.evidence}<section class="presentation-result">
            <h4>{stage.step === 4 ? 'Agent’s result' : 'Last observed progress'}</h4>
            <p>{excerpt(stage.evidence, 700)}</p>
            {#if stage.evidence.length > 700}<details>
                <summary>Read full evidence</summary>
                <p>{stage.evidence}</p>
              </details>{/if}
          </section>{/if}
        <button class="primary-button" onclick={() => onselect(row.id)}
          >{stage.step === 1 ? 'Review & decide' : 'Open full request'}
          <span aria-hidden="true">↗</span></button
        >
      </article>
    {/each}
  </div>
  <p class="presentation-footnote">
    Saving an answer does not mean the agent has picked it up. Progress appears only after the agent
    records it.
  </p>
</section>

<style>
  .presentation {
    max-width: 1400px;
    margin: 0 auto;
    padding: 12px 0 40px;
  }
  .presentation-intro {
    max-width: 800px;
    margin: 8px 0 36px;
  }
  .presentation-intro h2 {
    font-size: clamp(30px, 4vw, 52px);
    line-height: 1.12;
    letter-spacing: -0.035em;
    margin: 12px 0 18px;
    font-weight: 650;
  }
  .presentation-intro > p {
    color: var(--muted);
    font-size: 17px;
  }
  .presentation-intro .eyebrow {
    color: var(--mint);
    font-size: 11px;
  }
  .presentation-intro .presentation-source {
    font-size: 12px;
    margin-top: 16px;
  }
  .presentation-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr));
    gap: 24px;
  }
  .presentation-card {
    border: 1px solid #ffffff20;
    border-radius: 18px;
    padding: 28px;
    background: var(--surface);
    box-shadow: 0 5px 20px #0002;
    min-width: 0;
    overflow-wrap: anywhere;
  }
  .presentation-agent {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    flex-wrap: wrap;
  }
  .presentation-status {
    margin-left: auto;
    color: var(--mint);
    font-size: 12px;
  }
  .presentation-card h3 {
    font-size: 23px;
    line-height: 1.3;
    margin: 24px 0 12px;
    letter-spacing: -0.02em;
  }
  .presentation-card > p {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.6;
  }
  .presentation-steps {
    display: flex;
    gap: 8px;
    list-style: none;
    padding: 0;
    margin: 26px 0;
  }
  .presentation-steps li {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 11px;
    color: var(--muted);
    border-top: 2px solid #ffffff15;
    padding-top: 12px;
  }
  .presentation-steps .reached {
    border-color: var(--mint);
    color: var(--mint);
  }
  .presentation-steps span {
    font-weight: 650;
  }
  .presentation-answer,
  .presentation-result {
    background: #83d9bb0b;
    padding: 16px;
    border-radius: 10px;
    margin: 18px 0;
  }
  .presentation-result {
    background: #b5a5f60b;
  }
  .presentation-card h4 {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin: 0 0 8px;
    color: var(--muted);
  }
  .presentation-answer p,
  .presentation-result p {
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    margin: 6px 0;
  }
  .presentation-result summary {
    cursor: pointer;
    font-size: 12px;
    margin-top: 10px;
  }
  .presentation-footnote {
    font-size: 12px;
    color: var(--muted);
    margin-top: 24px;
  }
  @media (max-width: 600px) {
    .presentation-card {
      padding: 20px;
    }
  }
</style>
