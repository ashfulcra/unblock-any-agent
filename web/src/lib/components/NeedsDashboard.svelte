<script>
  import { requestView, filterRequests, groupAgents, sortRequests } from '$lib/unblock-view.js';
  import RequestCard from './RequestCard.svelte';
  import RequestDetail from './RequestDetail.svelte';
  import '$lib/unblock-workspace.css';
  import { editDraft, reviewDraft, submitDraft, failedAnswer } from '$lib/answer-draft.js';
  import { onMount } from 'svelte';
  import ExpectationsDashboard from './ExpectationsDashboard.svelte';
  /** @type {any[]} */ let requests = $state([]);
  /** @type {any[]} */ let grants = $state([]);
  /** @type {any[]} */ let expectations = $state([]);
  let expectationSourceReady = $state(false),
    ownerId = $state('');
  let error = $state('');
  let checked = $state('');
  let busy = $state(false);
  let agentId = $state('');
  let agentName = $state('');
  let enrollmentKind = $state('agent');
  let environment = $state('pilot');
  let agentScope = $state('');
  let credential = $state('');
  let expires = $state('');
  let notice = $state('');
  /** @type {any} */ let pendingEnrollment = $state(null);
  /** @type {Record<string,string>} */ let answers = $state({});
  /** @type {Record<string,any>} */ let drafts = $state({});
  /** @type {Record<string,any>} */ let pending = $state({});

  let pageView = $state('work'),
    mode = $state('board'),
    sortOrder = $state('oldest'),
    query = $state(''),
    agentFilter = $state(''),
    laneFilter = $state(''),
    selectedId = $state(''),
    now = $state(Date.now());
  const lanes = [
    { id: 'attention', name: 'Needs you', hint: 'Decisions that move work forward', icon: '↗' },
    { id: 'waiting', name: 'With agents', hint: 'Answers sent · watching for progress', icon: '◷' },
    { id: 'done', name: 'Done', hint: 'Observed results, kept for context', icon: '✓' }
  ];
  const filtered = $derived(
    sortRequests(
      filterRequests(requests, { query, agent: agentFilter, lane: laneFilter, grants }),
      sortOrder
    )
  );
  const agents = $derived(groupAgents(requests, grants));
  const activeAgents = $derived(
    agents.filter((a) => a.requests.some((r) => requestView(r).lane !== 'done'))
  );
  const mapAgents = $derived(groupAgents(filtered, grants));
  const selected = $derived(requests.find((r) => r.id === selectedId));
  const selectedPending = $derived(
    Object.values(pending).find(
      (p) => p.request_id === selectedId && p.revision === selected?.revisions[0]?.id
    )
  );
  const earlierPending = $derived(
    Object.values(pending).filter((p) => p.request_id === selectedId && p !== selectedPending)
  );
  const concernCount = $derived(
    expectations.filter((r) => ['due', 'investigate', 'conflict'].includes(r.state)).length
  );
  /** @param {string} id */
  function agentLabel(id) {
    return grants.find((g) => g.agent_id === id)?.name || id;
  }
  /** @param {string} id */
  function selectRequest(id) {
    selectedId = id;
  }
  function readHash() {
    const match = window.location.hash.match(/^#request-(.+)$/);
    if (match) {
      selectedId = decodeURIComponent(match[1]);
      pageView = 'work';
    }
  }
  /** @param {string} value */
  function editAnswer(value) {
    if (!selected) return;
    answers[selected.id] = value;
    drafts[selected.id] = editDraft(
      drafts[selected.id],
      selected.id,
      selected.revisions[0].id,
      value
    );
    sessionStorage.setItem('unblock-draft:' + selected.id, JSON.stringify(drafts[selected.id]));
  }
  function reviewAnswer() {
    if (!selected) return;
    drafts[selected.id] = reviewDraft(drafts[selected.id], selected.revisions[0].id);
    sessionStorage.setItem('unblock-draft:' + selected.id, JSON.stringify(drafts[selected.id]));
  }
  async function refresh() {
    try {
      const res = await fetch('/api/unblock/attention');
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      requests = data.requests;
      grants = data.grants;
      checked = data.checked_at;
      now = Date.now();
      error = '';
      expectationSourceReady = Array.isArray(data.expectations);
      if (expectationSourceReady) expectations = data.expectations;
      ownerId = data.principal?.kind === 'owner' ? data.principal.id : '';
      if (pendingEnrollment && grants.some((g) => g.intent_id === pendingEnrollment.intent_id)) {
        pendingEnrollment = null;
        sessionStorage.removeItem('unblock-enrollment');
        notice = 'Enrollment read back. The credential is ready until its displayed expiry.';
      }
      for (const [id, body] of Object.entries(pending)) {
        const row = requests.find((r) => r.id === body.request_id);
        if (
          row &&
          [...row.answers, ...row.stale_answers].some(
            (a) =>
              a.intent_id === body.intent_id &&
              a.payload.answer === body.answer &&
              a.payload.revision === body.revision &&
              a.payload.responder === ownerId
          )
        ) {
          delete pending[id];
          sessionStorage.removeItem('unblock-answer:' + id);
          const draft = drafts[body.request_id];
          if (
            draft?.intent_id === body.intent_id &&
            draft?.revision === body.revision &&
            draft?.answer === body.answer
          ) {
            delete drafts[body.request_id];
            delete answers[body.request_id];
            sessionStorage.removeItem('unblock-draft:' + body.request_id);
          }
          notice = 'Answer read back. Current agent progress appears on the request card.';
        }
      }
    } catch (e) {
      error = /** @type {Error} */ (e).message;
      expectationSourceReady = false;
    }
  }
  /** @param {string} operation @param {any} body */
  async function post(operation, body) {
    const res = await fetch('/api/unblock/' + operation, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) {
      const failure = /** @type {Error & {writeOutcome?:string}} */ (new Error(data.error));
      failure.writeOutcome = data.outcome || 'uncertain';
      throw failure;
    }
    return data;
  }
  async function enroll() {
    busy = true;
    error = '';
    credential = '';
    try {
      if (!pendingEnrollment) {
        const response = await fetch('/api/unblock/prepare_enrollment');
        const prepared = await response.json();
        if (!response.ok) throw new Error(prepared.error);
        pendingEnrollment = {
          intent_id: crypto.randomUUID(),
          agent_id: agentId,
          name: agentName,
          kind: enrollmentKind,
          environment,
          agent_ids: agentScope
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
          expires_at: prepared.expires_at
        };
        sessionStorage.setItem('unblock-enrollment', JSON.stringify(pendingEnrollment));
      }
      const data = await post('enroll', pendingEnrollment);
      if (pendingEnrollment) {
        pendingEnrollment = failedAnswer(pendingEnrollment, 'uncertain');
        sessionStorage.setItem('unblock-enrollment', JSON.stringify(pendingEnrollment));
      }
      credential = data.credential;
      expires = new Date(data.expires_at * 1000).toLocaleString();
      notice =
        data.visibility === 'visible'
          ? 'Enrollment is visible.'
          : 'Enrollment accepted; wait for it to appear below before using the credential.';
      await refresh();
    } catch (e) {
      const failure = /** @type {Error & {writeOutcome?:string}} */ (e);
      error = failure.message;
      if (pendingEnrollment) {
        pendingEnrollment = failedAnswer(pendingEnrollment, failure.writeOutcome || 'uncertain');
        if (pendingEnrollment)
          sessionStorage.setItem('unblock-enrollment', JSON.stringify(pendingEnrollment));
        else sessionStorage.removeItem('unblock-enrollment');
      }
    } finally {
      busy = false;
    }
  }
  /** @param {any} row */
  async function sendRecommendation(row) {
    if (
      busy ||
      !checked ||
      error ||
      !row ||
      row.revisions.length !== 1 ||
      ['completed', 'withdrawn'].includes(row.state) ||
      requests.find((current) => current.id === row.id) !== row ||
      Object.values(pending).some(
        (p) => p.request_id === row.id && p.revision === row.revisions[0].id
      )
    )
      return;
    const revision = row.revisions[0];
    if (!revision.payload.recommendation.trim()) return;
    drafts[row.id] = editDraft(null, row.id, revision.id, revision.payload.recommendation);
    answers[row.id] = drafts[row.id].answer;
    sessionStorage.setItem('unblock-draft:' + row.id, JSON.stringify(drafts[row.id]));
    await answer(row);
  }
  /** @param {any} row @param {any} [saved] */
  async function answer(row, saved = null) {
    const revision = row.revisions[0];
    let body =
      saved ||
      Object.values(pending).find((p) => p.request_id === row.id && p.revision === revision.id);
    if (!body) {
      try {
        body = submitDraft(drafts[row.id], revision.id);
      } catch (e) {
        error = /** @type {Error} */ (e).message;
        return;
      }
      pending[body.intent_id] = body;
      sessionStorage.setItem('unblock-answer:' + body.intent_id, JSON.stringify(body));
    }
    const intent = body.intent_id;
    busy = true;
    error = '';
    try {
      const data = await post('answer', body);
      if (pending[intent]) {
        pending[intent] = failedAnswer(pending[intent], 'uncertain');
        sessionStorage.setItem('unblock-answer:' + intent, JSON.stringify(pending[intent]));
      }
      notice =
        data.visibility === 'visible'
          ? 'Answer read back. Waiting for agent pickup.'
          : 'Answer accepted; checking native persistence. This does not mean the agent resumed.';
      await refresh();
    } catch (e) {
      const failure = /** @type {Error & {writeOutcome?:string}} */ (e);
      const retained = failedAnswer(pending[intent], failure.writeOutcome || 'uncertain');
      if (retained) {
        pending[intent] = retained;
        sessionStorage.setItem('unblock-answer:' + intent, JSON.stringify(retained));
      } else {
        delete pending[intent];
        sessionStorage.removeItem('unblock-answer:' + intent);
      }
      error = failure.message;
    } finally {
      busy = false;
    }
  }
  /** @param {any} grant */
  async function revoke(grant) {
    busy = true;
    error = '';
    try {
      const data = await post('revoke', {
        intent_id: crypto.randomUUID(),
        grant_id: grant.grant_id
      });
      notice =
        data.visibility === 'visible'
          ? 'Revocation read back.'
          : 'Revocation pending native processing; access is not yet confirmed revoked.';
      await refresh();
    } catch (e) {
      error = /** @type {Error} */ (e).message;
    } finally {
      busy = false;
    }
  }
  onMount(() => {
    try {
      pendingEnrollment = JSON.parse(sessionStorage.getItem('unblock-enrollment') || 'null');
      if (pendingEnrollment) {
        agentId = pendingEnrollment.agent_id;
        agentName = pendingEnrollment.name;
        enrollmentKind = pendingEnrollment.kind || 'agent';
        environment = pendingEnrollment.environment || 'pilot';
        agentScope = (pendingEnrollment.agent_ids || []).join(',');
      }
    } catch {}
    const storageKeys = Array.from({ length: sessionStorage.length }, (_, i) =>
      sessionStorage.key(i)
    );
    for (const k of storageKeys) {
      if (k?.startsWith('unblock-draft:'))
        try {
          const body = JSON.parse(sessionStorage.getItem(k) || 'null');
          if (body?.request_id) {
            drafts[body.request_id] = body;
            answers[body.request_id] = body.answer;
          }
        } catch {}
      if (k?.startsWith('unblock-answer:'))
        try {
          const body = JSON.parse(sessionStorage.getItem(k) || 'null');
          if (body?.request_id && body.intent_id) {
            pending[body.intent_id] = body;
            if (k !== 'unblock-answer:' + body.intent_id) {
              sessionStorage.removeItem(k);
              sessionStorage.setItem('unblock-answer:' + body.intent_id, JSON.stringify(body));
            }
          }
        } catch {}
    }
    readHash();
    window.addEventListener('hashchange', readHash);
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => {
      clearInterval(timer);
      window.removeEventListener('hashchange', readHash);
    };
  });
</script>

<div class="unblock-app">
  <nav class="workspace-sidebar" aria-label="Workspace">
    <a href="/" class="brand"
      ><span class="brand-mark">u<span>↗</span></span><span
        >unblock<span class="brand-subtitle">YOUR AGENT WORKSPACE</span></span
      ></a
    >
    <span class="nav-section">WORKSPACE</span>
    <button class:active={pageView === 'work'} onclick={() => (pageView = 'work')}
      ><span aria-hidden="true">▦</span> Work
      <span class="nav-count"
        >{checked ? requests.filter((r) => requestView(r).lane === 'attention').length : '—'}</span
      ></button
    >
    <button class:active={pageView === 'updates'} onclick={() => (pageView = 'updates')}
      ><span aria-hidden="true">◷</span> Updates {#if concernCount}<span class="nav-count"
          >{concernCount}</span
        >{/if}</button
    >
    <button class:active={pageView === 'connections'} onclick={() => (pageView = 'connections')}
      ><span aria-hidden="true">⌘</span> Connections</button
    >
    <div class="sidebar-agents">
      <span class="nav-section">YOUR AGENTS</span>
      {#each activeAgents as a}<button
          class:agent-active={agentFilter === a.id}
          onclick={() => {
            agentFilter = agentFilter === a.id ? '' : a.id;
            pageView = 'work';
          }}
          ><span class="agent-avatar small">{a.name.slice(0, 2).toUpperCase()}</span><span
            >{a.name}</span
          >{#if a.attention}<span class="agent-count">{a.attention}</span>{/if}</button
        >{/each}
      {#if !agents.length}<p class="sidebar-empty">Connected work will appear here.</p>{/if}
    </div>
    <div class="sidebar-bottom">
      <a href="https://github.com/ashfulcra/unblock-any-agent" target="_blank" rel="noreferrer"
        >Source & guides ↗</a
      ><span>Unblock Any Agent · Pilot</span>
    </div>
  </nav>
  <main class="workspace-main">
    <header class="workspace-header">
      <div>
        <p class="eyebrow">YOUR ATTENTION, WHERE IT MATTERS</p>
        <h1>
          {pageView === 'work'
            ? 'Keep good work moving.'
            : pageView === 'updates'
              ? 'Stay in the loop.'
              : 'Your connected agents.'}
        </h1>
        <p class="header-subtitle">
          {pageView === 'work'
            ? 'See who’s waiting, make the decision, and follow what happens next.'
            : pageView === 'updates'
              ? 'Expected updates and work that needs a closer look.'
              : 'Manage the agents allowed to bring work into this workspace.'}
        </p>
      </div>
      <button class="quiet-button refresh-button" onclick={refresh} aria-label="Refresh workspace"
        >↻ <span>Refresh</span></button
      >
    </header>
    {#if error}<div class="source-alert" role="alert">
        <strong>Couldn’t refresh this workspace.</strong> Your last known work and saved answers are
        retained.
        <details><summary>Connection details</summary>{error}</details>
      </div>{/if}
    {#if notice}<div class="notice-banner" role="status">
        {notice}<button
          class="icon-button"
          onclick={() => (notice = '')}
          aria-label="Dismiss notice">✕</button
        >
      </div>{/if}
    {#if pageView === 'work'}
      <div class="workspace-stats" aria-label="Work status filters">
        {#each lanes as lane}<button
            class:stat-selected={laneFilter === lane.id}
            class={'stat ' + lane.id}
            onclick={() => (laneFilter = laneFilter === lane.id ? '' : lane.id)}
            ><span class="stat-symbol" aria-hidden="true">{lane.icon}</span><span
              ><strong
                >{checked
                  ? requests.filter((r) => requestView(r).lane === lane.id).length
                  : '—'}</strong
              ><span>{lane.name}</span></span
            ></button
          >{/each}
      </div>
      <div class="work-toolbar">
        <label class="search-field"
          ><span aria-hidden="true">⌕</span><input
            type="search"
            placeholder="Find a decision, context or agent…"
            aria-label="Search work"
            bind:value={query}
          /></label
        ><select aria-label="Filter by agent" bind:value={agentFilter}
          ><option value="">All agents</option>{#each agents as a}<option value={a.id}
              >{a.name}</option
            >{/each}</select
        ><select aria-label="Sort work" bind:value={sortOrder}
          ><option value="oldest">Longest waiting</option><option value="newest"
            >Newest first</option
          ></select
        >
        <div class="view-switch" aria-label="View">
          <button
            class:current={mode === 'board'}
            onclick={() => (mode = 'board')}
            aria-pressed={mode === 'board'}>▦ Board</button
          ><button
            class:current={mode === 'map'}
            onclick={() => (mode = 'map')}
            aria-pressed={mode === 'map'}>⌘ Map</button
          ><button
            class:current={mode === 'list'}
            onclick={() => (mode = 'list')}
            aria-pressed={mode === 'list'}>☰ List</button
          >
        </div>
      </div>
      {#if laneFilter || agentFilter || query}<div class="filter-summary">
          <span
            >{filtered.length} matching request{filtered.length === 1 ? '' : 's'}{laneFilter
              ? ' · ' + lanes.find((l) => l.id === laneFilter)?.name
              : ''}</span
          ><button
            onclick={() => {
              laneFilter = '';
              agentFilter = '';
              query = '';
            }}>Clear filters ×</button
          >
        </div>{/if}
      <div class:has-selection={!!selected} class="work-and-detail">
        <div class="work-canvas">
          {#if !checked && error}<div class="canvas-empty" role="status">
              <span class="empty-symbol">?</span>
              <h2>Your work is unavailable.</h2>
              <p>
                We haven’t read this workspace yet. Pending work is unknown until the connection
                recovers.
              </p>
              <button class="quiet-button" onclick={refresh}>Try again</button>
            </div>
          {:else if !checked}<div class="canvas-empty">
              <span class="empty-symbol">◷</span>
              <h2>Finding your work…</h2>
              <p>Reading your authorized workspace.</p>
            </div>
          {:else if !filtered.length}<div class="canvas-empty">
              <span class="empty-symbol">↗</span>
              <h2>
                {requests.length ? 'Nothing matches these filters.' : 'A little room to move.'}
              </h2>
              <p>
                {requests.length
                  ? 'Try another agent or search term.'
                  : 'Your agents’ questions and progress will appear here.'}
              </p>
              {#if requests.length}<button
                  class="quiet-button"
                  onclick={() => {
                    query = '';
                    agentFilter = '';
                    laneFilter = '';
                  }}>Show all work</button
                >{/if}
            </div>
          {:else if mode === 'board'}
            <div class="work-board">
              {#each lanes.filter((l) => !laneFilter || l.id === laneFilter) as lane}<section
                  class={'work-lane ' + lane.id}
                  aria-label={lane.name}
                >
                  <header>
                    <span class={'status-dot ' + lane.id}></span>
                    <h2>{lane.name}</h2>
                    <span class="lane-count"
                      >{filtered.filter((r) => requestView(r).lane === lane.id).length}</span
                    >
                  </header>
                  <p class="lane-hint">{lane.hint}</p>
                  <div class="lane-cards">
                    {#each filtered
                      .filter((r) => requestView(r).lane === lane.id)
                      .slice(0, lane.id === 'done' ? 6 : 100) as row (row.id)}<RequestCard
                        {row}
                        name={agentLabel(row.agent_id)}
                        selected={row.id === selectedId}
                        {now}
                        onselect={selectRequest}
                      />{/each}{#if !filtered.some((r) => requestView(r).lane === lane.id)}<div
                        class="lane-empty"
                      >
                        {lane.id === 'attention'
                          ? 'No decisions waiting.'
                          : lane.id === 'waiting'
                            ? 'No answers awaiting progress.'
                            : 'Completed work will land here.'}
                      </div>{/if}{#if lane.id === 'done' && filtered.filter((r) => requestView(r).lane === 'done').length > 6}<button
                        class="show-history"
                        onclick={() => {
                          mode = 'list';
                          laneFilter = 'done';
                        }}>Explore all completed work →</button
                      >{/if}
                    {#if lane.id !== 'done' && filtered.filter((r) => requestView(r).lane === lane.id).length > 100}<button
                        class="show-history"
                        onclick={() => {
                          mode = 'list';
                          laneFilter = lane.id;
                        }}>Explore all {lane.name.toLowerCase()} work →</button
                      >{/if}
                  </div>
                </section>{/each}
            </div>
          {:else if mode === 'map'}
            <div class="map-intro">
              <span class="map-legend"
                ><span class="status-dot attention"></span> Needs you
                <span class="status-dot waiting"></span>
                With agents <span class="status-dot done"></span> Done</span
              >
              <p>Explore by agent. Lines show who owns each request.</p>
            </div>
            <div class="agent-map">
              {#each mapAgents as a}<section class="agent-cluster">
                  <header class="agent-node">
                    <span class="agent-avatar large">{a.name.slice(0, 2).toUpperCase()}</span>
                    <div>
                      <h2>{a.name}</h2>
                      <p>
                        {a.attention} decision{a.attention === 1 ? '' : 's'} waiting · {a.requests
                          .length} request{a.requests.length === 1 ? '' : 's'}
                      </p>
                    </div>
                  </header>
                  <div class="map-branches">
                    {#each a.requests as row (row.id)}<div class="map-branch">
                        <RequestCard
                          {row}
                          name={a.name}
                          selected={row.id === selectedId}
                          {now}
                          onselect={selectRequest}
                        />
                      </div>{/each}
                  </div>
                </section>{/each}
            </div>
          {:else}<div class="request-list">
              {#each filtered as row (row.id)}<RequestCard
                  {row}
                  name={agentLabel(row.agent_id)}
                  selected={row.id === selectedId}
                  {now}
                  onselect={selectRequest}
                />{/each}
            </div>{/if}
        </div>
        {#if selected}<RequestDetail
            row={selected}
            name={agentLabel(selected.agent_id)}
            answerText={selectedPending?.answer || answers[selected.id] || ''}
            draft={drafts[selected.id]}
            pending={selectedPending}
            {earlierPending}
            onverify={(body) => answer(selected, body)}
            {busy}
            sourceReady={!!checked && !error}
            {now}
            onedit={editAnswer}
            onreview={reviewAnswer}
            onsend={() => answer(selected)}
            onrecommend={() => sendRecommendation(selected)}
            onclose={() => (selectedId = '')}
          />{/if}
      </div>
    {:else if pageView === 'updates'}<div class="updates-container">
        <ExpectationsDashboard
          rows={expectations}
          {ownerId}
          sourceReady={expectationSourceReady && !error}
          {refresh}
        />
      </div>
    {:else}<section class="connections-container">
        <h2>Connections & access</h2>
        <p>
          Each agent has its own identity. Keep credentials private and use a receiver to pick up
          answers when an agent is away.
        </p>
        <details class="mt-8 rounded-xl border border-white/20 p-5">
          <summary class="cursor-pointer text-lg font-semibold">Connect an agent</summary>
          <p class="mt-3 text-sm">
            Credentials are limited to the enrolled agent and expire with this sign-in session,
            within one hour. Renew enrollment when expired. Keep them in the agent's private
            credential storage.
          </p>
          <label class="mt-4 block" for="enrollment-kind">Connection role</label>
          <select
            id="enrollment-kind"
            class="select mt-1 w-full bg-black/30 text-white"
            bind:value={enrollmentKind}
            disabled={!!pendingEnrollment}
            ><option value="agent">Agent worker</option><option value="listener"
              >Environment listener — check and route</option
            ></select
          >
          <label class="mt-3 block" for="environment">Environment ID</label><input
            id="environment"
            class="input mt-1 w-full bg-black/30 text-white"
            bind:value={environment}
            disabled={!!pendingEnrollment}
          />
          {#if enrollmentKind === 'listener'}<label class="mt-3 block" for="agent-scope"
              >Permitted agent IDs, separated by commas</label
            ><input
              id="agent-scope"
              class="input mt-1 w-full bg-black/30 text-white"
              bind:value={agentScope}
              disabled={!!pendingEnrollment}
            />
            <p class="mt-2 text-sm">
              The listener can check these agents and record delivery or overdue observations. It
              cannot change their work or report their progress. Each worker needs its own
              credential.
            </p>{/if}
          <label class="mt-4 block" for="agent-id">Agent or listener ID</label><input
            id="agent-id"
            class="input mt-1 w-full bg-black/30 text-white"
            placeholder="my-agent"
            bind:value={agentId}
            disabled={!!pendingEnrollment}
          />
          <label class="mt-3 block" for="agent-name">Display name</label><input
            id="agent-name"
            class="input mt-1 w-full bg-black/30 text-white"
            bind:value={agentName}
            disabled={!!pendingEnrollment}
          />
          <button class="btn mt-4" disabled={busy || !agentId || !agentName} onclick={enroll}
            >{pendingEnrollment ? 'Retry same enrollment' : 'Create scoped enrollment'}</button
          >
          {#if credential}
            <label class="mt-4 block" for="agent-credential"
              >Private agent credential · expires {expires}</label
            >
            <textarea
              id="agent-credential"
              class="textarea mt-2 w-full bg-black/30 text-white"
              readonly
              value={credential}
              rows="3"
            ></textarea>
            <button
              class="btn mt-2 btn-sm"
              onclick={() => {
                credential = '';
              }}>Hide credential</button
            >
          {/if}
          <ul class="mt-4 space-y-2">
            {#each grants as grant (grant.record_id)}<li>
                {grant.name} · {grant.kind || 'agent'} · {grant.environment || 'pilot'} · {grant.revoked
                  ? 'revoked'
                  : new Date(grant.expires_at * 1000).getTime() < Date.now()
                    ? 'expired'
                    : 'enrolled'}
                {#if !grant.revoked}<button
                    class="btn ml-2 btn-xs"
                    disabled={busy}
                    onclick={() => revoke(grant)}>Revoke</button
                  >{/if}
              </li>{/each}
          </ul>
        </details>
      </section>{/if}
    <footer class="workspace-status">
      <span class:source-ok={checked && !error} class="source-indicator"></span>{error
        ? checked
          ? 'Showing last known work'
          : 'Work status unknown'
        : checked
          ? 'Workspace checked ' +
            new Date(checked).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
          : 'Connecting…'}<span class="status-footnote"
        >Pickup is confirmed by agent progress, not by sending an answer.</span
      >
    </footer>
  </main>
</div>
