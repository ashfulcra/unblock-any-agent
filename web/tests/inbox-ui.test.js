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
    window: { parent: { postMessage() {} }, addEventListener() {} },
    Option: class extends Node {},
    crypto: { randomUUID: () => 'fresh-intent' },
    setTimeout() {},
    clearTimeout() {},
    setInterval() {},
    clearInterval() {}
  });
  vm.runInContext(script, context);
  vm.runInContext('renderOverview=()=>{}; refresh=async()=>{};', context);
  return {
    context,
    nodes,
    stored,
    run: (code) => vm.runInContext(code, context),
    set: (name, value) => {
      context[name] = value;
    }
  };
}
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
