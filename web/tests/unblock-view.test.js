import test from 'node:test';
import assert from 'node:assert/strict';
import {
  requestView,
  filterRequests,
  groupAgents,
  waitingAge,
  sortRequests,
  progressView
} from '../src/lib/unblock-view.js';

/** @param {string} id @param {string} state @param {any} [extra] */
const row = (id, state, extra = {}) => ({
  id,
  agent_id: 'writer',
  state,
  revisions: [
    {
      id: 'revision',
      payload: {
        need: 'Choose a publishing identity',
        context: 'The release is prepared.',
        recommendation: 'Use the company account.',
        next_action: 'Publish the reviewed release.'
      }
    }
  ],
  answers: [],
  progress: [],
  uncertain_actions: [],
  ...extra
});

test('current decisions, verification and observed completion are distinct lanes', () => {
  assert.equal(requestView(row('1', 'needs_you')).lane, 'attention');
  assert.equal(requestView(row('2', 'awaiting_pickup', { answers: [{}] })).lane, 'waiting');
  assert.equal(requestView(row('3', 'resumed', { answers: [{}] })).status, 'Working');
  assert.equal(requestView(row('4', 'completed', { answers: [{}] })).lane, 'done');
  assert.equal(
    requestView(row('5', 'uncertain_action', { answers: [{}], uncertain_actions: [{}] })).lane,
    'attention'
  );
  assert.equal(
    requestView(row('6', 'answer_conflict', { answers: [{}, {}] })).status,
    'Review answers'
  );
});
test('search includes retained context and agent display names without changing the source', () => {
  const rows = [row('1', 'needs_you'), row('2', 'completed', { agent_id: 'builder' })];
  const before = JSON.stringify(rows);
  assert.deepEqual(
    filterRequests(rows, { query: 'company' }).map((r) => r.id),
    ['1', '2']
  );
  assert.deepEqual(
    filterRequests(rows, { query: 'Editor', grants: [{ agent_id: 'writer', name: 'Editor' }] }).map(
      (r) => r.id
    ),
    ['1']
  );
  assert.deepEqual(
    filterRequests(rows, { agent: 'builder', lane: 'done' }).map((r) => r.id),
    ['2']
  );
  assert.equal(JSON.stringify(rows), before);
});
test('agent map uses actual ownership, not guessed dependencies or duplicated enrollment renewals', () => {
  const rows = [
    row('1', 'needs_you'),
    row('2', 'completed'),
    row('3', 'awaiting_pickup', { agent_id: 'builder' })
  ];
  const agents = groupAgents(rows, [
    { agent_id: 'writer', name: 'Editor' },
    { agent_id: 'writer', name: 'Editor' },
    { agent_id: 'listener', kind: 'listener', name: 'Monitor' }
  ]);
  assert.equal(agents.length, 2);
  assert.equal(agents.find((a) => a.id === 'writer')?.name, 'Editor');
  assert.equal(agents.find((a) => a.id === 'writer')?.requests.length, 2);
  assert.equal(agents.find((a) => a.id === 'writer')?.attention, 1);
});
test('waiting age exposes missing dates and never invents a fresh start', () => {
  const now = Date.parse('2026-10-19T12:00:00Z');
  assert.equal(waitingAge('2026-10-17T09:30:00Z', now), '2d 2h');
  assert.equal(waitingAge(null, now), 'Waiting time unknown');
  assert.equal(waitingAge('2026-10-20T12:00:00Z', now), 'Waiting time unknown');
});
test('longest waiting sorts known original request dates before unknown dates without rewriting source order', () => {
  const rows = [
    row('new', 'needs_you', { created_at: '2026-10-19T12:00:00Z' }),
    row('unknown', 'needs_you'),
    row('old', 'needs_you', { created_at: '2026-10-16T12:00:00Z' })
  ];
  assert.deepEqual(
    sortRequests(rows).map((r) => r.id),
    ['old', 'new', 'unknown']
  );
  assert.deepEqual(
    rows.map((r) => r.id),
    ['new', 'unknown', 'old']
  );
});

test('progress summary uses evidence for the current observed stage, not arrival order or an older stage', () => {
  const progress = [
    {
      recorded_at: '2026-10-20T12:00:00Z',
      payload: { stage: 'resumed', evidence: 'Latest verified action.' }
    },
    {
      recorded_at: '2026-10-20T10:00:00Z',
      payload: { stage: 'resumed', evidence: 'Earlier action.' }
    },
    {
      recorded_at: '2026-10-20T13:00:00Z',
      payload: { stage: 'acknowledged', evidence: 'Read receipt.' }
    }
  ];
  const before = JSON.stringify(progress);
  const result = progressView(row('1', 'resumed', { progress }));
  assert.ok(result);
  assert.equal(result.title, 'Work resumed');
  assert.equal(result.evidence, 'Latest verified action.');
  assert.equal(JSON.stringify(progress), before);
  const awaiting = progressView(row('2', 'awaiting_pickup'));
  assert.ok(awaiting);
  assert.equal(awaiting.title, 'Awaiting agent pickup');
  assert.match(awaiting.evidence, /pickup has not been observed/);
  assert.equal(progressView(row('3', 'needs_you')), null);
  assert.equal(progressView(row('4', 'uncertain_action', { progress })), null);
});
