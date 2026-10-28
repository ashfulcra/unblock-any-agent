// @ts-nocheck -- evaluates compiled-away Svelte runes with controlled source/transport doubles.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { editDraft, reviewDraft, submitDraft, failedAnswer } from '../src/lib/answer-draft.js';
const source = fs
  .readFileSync(new URL('../src/lib/components/NeedsDashboard.svelte', import.meta.url), 'utf8')
  .split('<script>')[1]
  .split('</script>')[0]
  .replace(/^\s*import .*$/gm, '');
function harness() {
  const stored = new Map();
  const c = vm.createContext({
    $state: (v) => v,
    $derived: (v) => v,
    onMount() {},
    requestView: () => ({ lane: 'attention' }),
    filterRequests: () => [],
    groupAgents: () => [],
    sortRequests: (v) => v,
    Date,
    editDraft,
    reviewDraft,
    submitDraft,
    failedAnswer,
    sessionStorage: { setItem: (k, v) => stored.set(k, v), removeItem: (k) => stored.delete(k) }
  });
  vm.runInContext(source, c);
  return { c, stored, run: (s) => vm.runInContext(s, c) };
}
const old = {
  request_id: 'request-A',
  intent_id: 'old',
  revision: 'old-revision',
  answer: 'Old uncertain answer',
  _uncertain: true
};
const fresh = {
  request_id: 'request-A',
  intent_id: 'new',
  revision: 'new-revision',
  answer: 'New reviewed answer'
};
test('dashboard can submit a revised question while preserving its earlier uncertain answer', async () => {
  const h = harness();
  h.c.oldInput = old;
  h.c.freshInput = fresh;
  h.run(
    'pending.old=oldInput;drafts["request-A"]=freshInput;refresh=async()=>{};post=async(op,body)=>{captured=body;return {visibility:"pending"}}'
  );
  await h.run('answer({id:"request-A",revisions:[{id:"new-revision"}]})');
  assert.equal(h.c.captured.intent_id, 'new');
  assert.equal(h.run('Object.keys(pending).length'), 2);
  assert.equal(h.run('pending.old.answer'), old.answer);
});
test('readback of an earlier dashboard answer preserves a newly reviewed draft', async () => {
  const h = harness();
  h.c.oldInput = old;
  h.c.freshInput = fresh;
  h.c.fetch = async () => ({
    ok: true,
    json: async () => ({
      principal: { kind: 'owner', id: 'owner' },
      requests: [
        {
          id: 'request-A',
          answers: [],
          stale_answers: [
            {
              intent_id: 'old',
              payload: { revision: 'old-revision', answer: old.answer, responder: 'owner' }
            }
          ]
        }
      ],
      grants: [],
      expectations: [],
      checked_at: '2026-10-19T17:00:00Z'
    })
  });
  h.run(
    'pending.old=oldInput;drafts["request-A"]=freshInput;answers["request-A"]=freshInput.answer'
  );
  await h.run('refresh()');
  assert.equal(h.run('Object.keys(pending).length'), 0);
  assert.equal(h.run('drafts["request-A"].answer'), fresh.answer);
  assert.equal(h.run('answers["request-A"]'), fresh.answer);
});

test('dashboard sends full recommendation with a fresh intent and preserves earlier uncertain answers', async () => {
  const h = harness();
  h.c.freshInput = fresh;
  h.c.full = 'Use the private target. '.repeat(25);
  h.c.oldInput = old;
  h.run(
    'checked="now";requests=[{id:"request-A",state:"needs_you",revisions:[{id:"new-revision",payload:{recommendation:full}}]}];drafts["request-A"]={...freshInput};pending.old=oldInput;post=async(op,body)=>{captured={...body};return {visibility:"pending"}};refresh=async()=>{}'
  );
  await h.run('sendRecommendation(requests[0])');
  assert.equal(h.c.captured.answer, h.c.full);
  assert.equal(h.c.captured.revision, 'new-revision');
  assert.ok(h.c.captured.intent_id);
  assert.notEqual(h.c.captured.intent_id, 'new');
  assert.notEqual(h.c.captured.intent_id, 'old');
  assert.equal(
    h.run('pending[Object.keys(pending).find(k=>k!=="old")].intent_id'),
    h.c.captured.intent_id
  );
  assert.equal(h.run('pending.old.answer'), old.answer);
  h.c.captured = null;
  await h.run('sendRecommendation(requests[0])');
  assert.equal(h.c.captured, null);
});
test('dashboard recommendation does not send a stale, completed, conflicted or unavailable question', async () => {
  const h = harness();
  h.run(
    'checked="now";requests=[{id:"request-A",state:"needs_you",revisions:[{id:"new-revision",payload:{recommendation:"Use the private target"}}]}];post=async()=>{captured=true};refresh=async()=>{}'
  );
  for (const mutate of [
    'error="offline"',
    'error="";busy=true',
    'busy=false;requests[0].state="completed"',
    'requests[0].state="needs_you";requests[0].revisions.push(requests[0].revisions[0])'
  ]) {
    h.run(mutate);
    await h.run('sendRecommendation(requests[0])');
    assert.equal(h.c.captured, undefined);
  }
});
