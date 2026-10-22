// @ts-nocheck -- executable DOM/host doubles intentionally implement only exercised APIs.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const script = fs
  .readFileSync(new URL('../../unblock/ui/inbox.html', import.meta.url), 'utf8')
  .split('<script type="module">')[1]
  .split('</script>')[0];
function harness(stored = new Map()) {
  const nodes = new Map();
  const listeners = new Map();
  class Node {
    constructor(tag = 'div', text = '') {
      this.tag = tag;
      this.textContent = text;
      this.children = [];
      this.value = '';
      this.dataset = {};
    }
    append(...items) {
      for (const item of items) {
        item.parent = this;
        this.children.push(item);
      }
    }
    replaceChildren(...items) {
      this.children = [];
      this.append(...items);
    }
    get lastChild() {
      return this.children.at(-1);
    }
    remove() {
      this.parent.children = this.parent.children.filter((n) => n !== this);
    }
    setAttribute() {}
    addEventListener() {}
    querySelector() {
      return this.children.find((n) => n.tag === 'button');
    }
    querySelectorAll(tag) {
      return this.children.flatMap((n) => [
        ...(n.tag === tag ? [n] : []),
        ...n.querySelectorAll(tag)
      ]);
    }
    focus() {}
  }
  const storage = {
    get length() {
      return stored.size;
    },
    key: (n) => [...stored.keys()][n],
    getItem: (k) => stored.get(k),
    setItem: (k, v) => stored.set(k, v),
    removeItem: (k) => stored.delete(k)
  };
  const context = vm.createContext({
    document: {
      getElementById: (id) => {
        if (!nodes.has(id)) nodes.set(id, new Node());
        return nodes.get(id);
      },
      createElement: (tag) => new Node(tag),
      documentElement: { dataset: {}, scrollHeight: 500 },
      addEventListener() {},
      activeElement: null
    },
    sessionStorage: storage,
    window: {
      parent: { postMessage() {} },
      addEventListener: (name, fn) => listeners.set(name, fn)
    },
    Option: class extends Node {
      constructor(text, value) {
        super('option', text);
        this.value = value;
      }
    },
    crypto: { randomUUID: () => 'fresh-intent' },
    setTimeout() {},
    clearTimeout() {},
    setInterval() {},
    clearInterval() {}
  });
  vm.runInContext(script, context);
  vm.runInContext(
    'const actualOverview=renderOverview,actualRefresh=refresh;renderOverview=()=>{}; refresh=async()=>{};',
    context
  );
  return {
    context,
    nodes,
    stored,
    hostMessage: (data) => listeners.get('message')({ source: context.window.parent, data }),
    run: (code) => vm.runInContext(code, context),
    set: (name, value) => {
      context[name] = value;
    }
  };
}

const workItem = {
  expectation_id: 'work-A',
  agent_id: 'builder',
  agent_name: 'Builder',
  environment: 'desktop',
  state: 'investigate',
  updates: [
    {
      revision: 'update-A',
      recorded_at: '2026-10-22T12:00:00Z',
      summary: 'Deliver the installed inbox',
      evidence: 'Missing work status reproduced',
      next_action: 'Publish and inspect the installed work view',
      status: 'working',
      next_update_at: 1792669200
    }
  ],
  request_ids: []
};
const workInbox = {
  workspace_id: 'w',
  source: 'checked',
  checked_at: '2026-10-22T12:01:00Z',
  counts: { needs_you: 0, with_agents: 0, done: 0 },
  items: [],
  pending_answers: [],
  work_source: 'checked',
  work_checked_at: '2026-10-22T12:01:00Z',
  work_counts: { working: 0, investigate: 1, done: 0 },
  work_items: [workItem]
};
const nodeText = (n) => [n.textContent, ...n.children.map(nodeText)].join(' ');

test('plugin overview exposes declared work and investigations without inventing human questions', () => {
  const h = harness();
  h.set('input', workInbox);
  h.run('renderOverview=actualOverview;applyInbox(input)');
  const tabs = h.nodes.get('status').children;
  assert.ok(tabs.some((n) => n.textContent.includes('Agent work')));
  assert.ok(tabs.some((n) => n.textContent.includes('Investigate') && n.textContent.includes('1')));
  tabs.find((n) => n.textContent.includes('Investigate')).onclick();
  const text = nodeText(h.nodes.get('cards'));
  assert.match(text, /Builder/);
  assert.match(text, /Missing work status reproduced/);
  assert.match(text, /Publish and inspect the installed work view/);
  assert.match(text, /overdue|missed update/i);
  assert.equal(h.run('last.counts.needs_you'), 0);
});

test('work-only agents remain searchable and filterable in the plugin', () => {
  const h = harness();
  h.set('input', workInbox);
  h.run('renderOverview=actualOverview;applyInbox(input);tab="work";renderOverview()');
  assert.ok(h.nodes.get('agents').children.some((n) => n.textContent === 'Builder'));
  h.nodes.get('search').value = 'installed';
  h.run('renderOverview()');
  assert.match(nodeText(h.nodes.get('cards')), /Deliver the installed inbox/);
  h.nodes.get('search').value = 'unrelated';
  h.run('renderOverview()');
  assert.doesNotMatch(nodeText(h.nodes.get('cards')), /Deliver the installed inbox/);
});

test('unknown work coverage labels retained updates without checked empty or fresh counts', () => {
  const h = harness();
  h.set('input', {
    ...workInbox,
    work_source: 'unavailable',
    work_counts: null,
    work_last_known: true
  });
  h.run('renderOverview=actualOverview;applyInbox(input);tab="work";renderOverview()');
  assert.match(nodeText(h.nodes.get('cards')), /last.known|unavailable/i);
  assert.match(nodeText(h.nodes.get('cards')), /Missing work status reproduced/);
  assert.ok(
    h.nodes
      .get('status')
      .children.some((n) => n.textContent.includes('Agent work') && n.textContent.includes('—'))
  );
});

test('work detail retains concurrent heads and has no human answer form', () => {
  const h = harness();
  const revision = {
    id: 'update-A',
    recorded_at: '2026-10-22T12:00:00Z',
    payload: {
      summary: 'Deliver inbox',
      context: 'Current implementation',
      evidence: 'First result',
      next_action: 'Inspect host',
      status: 'working',
      next_update_at: 1792669200
    }
  };
  h.set('input', {
    workspace_id: 'w',
    source: 'checked',
    checked_at: '2026-10-22T12:01:00Z',
    agent_name: 'Builder',
    expectation: {
      id: 'work-A',
      agent_id: 'builder',
      environment: 'desktop',
      state: 'conflict',
      revisions: [
        revision,
        {
          ...revision,
          id: 'update-B',
          payload: { ...revision.payload, evidence: 'Second concurrent result' }
        }
      ],
      history: [revision],
      observations: [],
      current_observations: [],
      request_ids: [],
      link_conflict: false
    }
  });
  h.run('applyWorkDetail(input)');
  const panel = h.nodes.get('detail');
  const text = nodeText(panel);
  assert.match(text, /First result/);
  assert.match(text, /Second concurrent result/);
  assert.match(text, /concurrent|reconcil/i);
  assert.equal(panel.querySelectorAll('textarea').length, 0);
});

test('refreshing selected work uses the read-only work tool and marks retained details unknown on failure', async () => {
  const h = harness();
  const revision = {
    id: 'update-A',
    recorded_at: '2026-10-22T12:00:00Z',
    payload: {
      summary: 'Deliver inbox',
      context: 'Current implementation',
      evidence: 'First result',
      next_action: 'Inspect host',
      status: 'working',
      next_update_at: 1792669200
    }
  };
  const data = {
    workspace_id: 'w',
    source: 'checked',
    checked_at: '2026-10-22T12:01:00Z',
    agent_name: 'Builder',
    expectation: {
      id: 'work-A',
      agent_id: 'builder',
      state: 'working',
      revisions: [revision],
      history: [revision],
      observations: [],
      current_observations: [],
      request_ids: []
    }
  };
  h.set('input', workInbox);
  h.set('workData', data);
  h.run('applyInbox(input);applyWorkDetail(workData);refresh=actualRefresh');
  const calls = [];
  h.set('hostTool', async (name, args) => {
    calls.push([name, args]);
    if (name === 'show_inbox') return workInbox;
    if (name === 'get_work_update')
      return {
        ...data,
        expectation: {
          ...data.expectation,
          revisions: [
            { ...revision, payload: { ...revision.payload, evidence: 'New verified result' } }
          ]
        }
      };
    throw new Error('Unexpected tool');
  });
  h.run('tool=hostTool');
  await h.run('refresh()');
  assert.equal(calls[1][0], 'get_work_update');
  assert.equal(calls[1][1].expectation_id, 'work-A');
  assert.match(nodeText(h.nodes.get('detail')), /New verified result/);
  h.set('hostTool', async (name) => {
    if (name === 'show_inbox') return workInbox;
    throw new Error('Work source read failed');
  });
  h.run('tool=hostTool');
  await h.run('refresh()');
  assert.match(nodeText(h.nodes.get('detail')), /retained|unknown/i);
  assert.match(nodeText(h.nodes.get('detail')), /New verified result/);
});
const old = {
  request_id: 'request-A',
  revision: 'old-revision',
  reviewed_snapshot: 'old-snapshot',
  answer: 'Original uncertain answer',
  intent_id: 'old:intent'
};
const fresh = {
  request_id: 'request-A',
  revision: 'new-revision',
  reviewed_snapshot: 'new-snapshot',
  answer: 'New reviewed answer'
};
const row = {
  id: 'request-A',
  agent_id: 'alpha',
  state: 'needs_you',
  revisions: [
    {
      id: 'new-revision',
      payload: {
        need: 'New question',
        context: 'Current context',
        recommendation: 'New recommendation',
        next_action: 'Next'
      }
    }
  ],
  answers: [],
  uncertain_actions: [],
  history: [],
  stale_answers: []
};
function prepare(h) {
  h.set('oldInput', old);
  h.set('freshInput', fresh);
  h.set('rowInput', row);
  h.run(
    'workspace="w";selected="request-A";ready=true;interactive=true;detail={request:rowInput,reviewed_snapshot:"new-snapshot",can_answer:true};drafts.set(selected,{...freshInput});'
  );
  h.run('applyInbox({workspace_id:"w",source:"checked",items:[],pending_answers:[oldInput]});');
}

test('multiple uncertain intents for one request survive source refresh and storage restart', () => {
  const h = harness();
  h.set('oldInput', old);
  h.set('newInput', { ...old, intent_id: 'second:intent', revision: 'second-revision' });
  h.run(
    'applyInbox({workspace_id:"w",source:"checked",items:[],pending_answers:[oldInput,newInput]});'
  );
  assert.equal(h.run('pending.size'), 2);
  const restarted = harness(h.stored);
  restarted.run('bindWorkspace("w")');
  assert.equal(restarted.run('pending.size'), 2);
  assert.deepEqual(
    JSON.parse(restarted.run('JSON.stringify([...pending.values()].map(p=>p.intent_id).sort())')),
    ['old:intent', 'second:intent']
  );
});

test('legacy request-keyed session state migrates without dropping colon-bearing intents', () => {
  const stored = new Map([['unblock-human:w:pending:request-A', JSON.stringify(old)]]);
  const h = harness(stored);
  h.run('bindWorkspace("w")');
  assert.equal(h.run('pending.size'), 1);
  assert.equal(h.run('pending.get("old:intent").request_id'), 'request-A');
  assert.equal(stored.has('unblock-human:w:pending:request-A'), false);
  assert.equal(stored.has('unblock-human:w:pending:old:intent'), true);
});

test('an uncertain earlier revision stays verifiable while the current question remains editable', () => {
  const h = harness();
  prepare(h);
  h.run('renderDetail()');
  const fields = h.nodes.get('detail').querySelectorAll('textarea');
  assert.equal(fields.length, 1);
  assert.equal(fields[0].disabled, false);
  assert.equal(fields[0].value, fresh.answer);
  assert.ok(
    h.nodes
      .get('detail')
      .querySelectorAll('button')
      .some((b) => b.textContent === 'Verify earlier answer')
  );
});

test('sending the newly reviewed question does not replace the original uncertain intent', async () => {
  const h = harness();
  prepare(h);
  h.run(
    'renderDetail=()=>{};tool=async(name,args)=>{captured=args;return {visibility:"pending",reason:"Still uncertain"}}'
  );
  await h.run('sendDecision()');
  assert.equal(h.context.captured.revision, 'new-revision');
  assert.equal(h.run('pending.size'), 2);
  assert.equal(
    h.run('[...pending.values()].find(p=>p.intent_id==="old:intent").answer'),
    old.answer
  );
});

test('verifying an earlier answer preserves the fresh draft and unrelated request draft', async () => {
  const h = harness();
  prepare(h);
  h.run(
    'renderDetail=()=>{};drafts.set("request-B",{answer:"B draft"});tool=async()=>({visibility:"visible",progress:"needs_you",current_question:false})'
  );
  await h.run('sendDecision(oldInput)');
  assert.equal(h.run('drafts.get("request-A").answer'), fresh.answer);
  assert.equal(h.run('drafts.get("request-B").answer'), 'B draft');
  assert.equal(h.run('pending.size'), 0);
});

const textOf = (node) => [node.textContent, ...node.children.map(textOf)].join(' ');
test('completed and withdrawn details keep the request date without claiming an ongoing wait', () => {
  for (const state of ['completed', 'withdrawn']) {
    const h = harness();
    h.set('rowInput', { ...row, state, created_at: '2026-10-16T12:00:00Z', progress: [] });
    h.run('selected="request-A";detail={request:rowInput,can_answer:false};renderDetail()');
    const header = textOf(h.nodes.get('detail').children[0]);
    assert.match(header, /Requested/);
    assert.doesNotMatch(header, /Waiting/);
    assert.match(header, state === 'completed' ? /Completed/ : /No longer needed/);
  }
});

test('verified current progress is visible before context and answer controls', () => {
  const h = harness();
  h.set('rowInput', {
    ...row,
    state: 'resumed',
    progress: [
      {
        recorded_at: '2026-10-20T12:00:00Z',
        payload: { stage: 'resumed', evidence: 'Deployment read back successfully.' }
      },
      {
        recorded_at: '2026-10-20T11:00:00Z',
        payload: { stage: 'acknowledged', evidence: 'Earlier read receipt.' }
      }
    ]
  });
  h.run('selected="request-A";detail={request:rowInput,can_answer:true};renderDetail()');
  const children = h.nodes.get('detail').children;
  const summary = children.findIndex((n) => n.className === 'progress-summary');
  assert.ok(summary >= 0);
  assert.match(textOf(children[summary]), /Deployment read back successfully/);
  assert.ok(summary < children.findIndex((n) => n.textContent === 'What you need to know'));
  assert.ok(summary < children.findIndex((n) => n.tag === 'textarea'));
  assert.doesNotMatch(textOf(children[summary]), /Earlier read receipt/);
});

test('saved answer status never claims agent pickup and full long context remains available', () => {
  const h = harness();
  h.set('rowInput', {
    ...row,
    state: 'awaiting_pickup',
    progress: [],
    revisions: [
      {
        ...row.revisions[0],
        payload: { ...row.revisions[0].payload, context: 'Retained full context. '.repeat(50) }
      }
    ]
  });
  h.run('selected="request-A";detail={request:rowInput,can_answer:true};renderDetail()');
  const panel = h.nodes.get('detail');
  const summary = panel.children.find((n) => n.className === 'progress-summary');
  assert.match(textOf(summary), /pickup has not been observed/);
  assert.doesNotMatch(textOf(summary), /Work resumed|Completed/);
  assert.ok(panel.querySelectorAll('details').some((n) => textOf(n).includes(rowInputContext())));
  function rowInputContext() {
    return 'Retained full context. '.repeat(50);
  }
});

test('fullscreen host changes apply without losing the current theme', () => {
  const h = harness();
  h.context.document.documentElement.dataset.theme = 'light';
  h.hostMessage({
    jsonrpc: '2.0',
    method: 'ui/notifications/host-context-changed',
    params: { displayMode: 'fullscreen' }
  });
  assert.equal(h.context.document.documentElement.dataset.displayMode, 'fullscreen');
  assert.equal(h.context.document.documentElement.dataset.theme, 'light');
  h.hostMessage({
    jsonrpc: '2.0',
    method: 'ui/notifications/host-context-changed',
    params: { displayMode: 'inline' }
  });
  assert.equal(h.context.document.documentElement.dataset.displayMode, 'inline');
});
