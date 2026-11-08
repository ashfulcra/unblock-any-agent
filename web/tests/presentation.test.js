import test from 'node:test';
import assert from 'node:assert/strict';
import {
  parsePresentation,
  presentationLink,
  presentationRows,
  presentationStage
} from '../src/lib/presentation.js';

const a = '00000000-0000-4000-8000-000000000001';
const b = '00000000-0000-4000-8000-000000000002';
/** @param {string} id @param {string} state @param {any} [extra] */
const row = (id, state, extra = {}) => ({
  id,
  state,
  revisions: [{ id: 'revision', payload: {} }],
  answers: [],
  progress: [],
  uncertain_actions: [],
  ...extra
});

test('presentation link retains exact request order across reload and source changes', () => {
  const link = presentationLink([b, a]);
  const selection = parsePresentation(new URL(link, 'https://unblock.test').search);
  assert.deepEqual(selection, { active: true, ids: [b, a], error: '' });
  const rows = [row(a, 'needs_you'), row('unrelated', 'completed'), row(b, 'awaiting_pickup')];
  assert.deepEqual(
    presentationRows(rows, selection.ids).rows.map((r) => r.id),
    [b, a]
  );
  rows[2].state = 'completed';
  assert.equal(presentationRows(rows, selection.ids).rows[0].state, 'completed');
  assert.deepEqual(presentationRows(rows.slice(0, 1), selection.ids).missing, [b]);
});

test('invalid, partial or oversized selection never falls back to other work', () => {
  assert.deepEqual(parsePresentation(''), { active: false, ids: [], error: '' });
  for (const query of [
    '?present=1',
    '?present=1&show=bad',
    `?present=1&show=${a}&show=bad`,
    `?present=2&show=${a}`,
    `?present=0&present=1&show=${a}`,
    `?show=${a}`,
    '?present=1&' +
      Array(7)
        .fill('show=' + a)
        .join('&')
  ]) {
    const selection = parsePresentation(query);
    assert.equal(selection.active, true);
    assert.ok(selection.error);
    assert.deepEqual(selection.ids, []);
    assert.deepEqual(presentationRows([row(a, 'completed')], selection.ids).rows, []);
  }
  assert.deepEqual(parsePresentation(`?present=1&show=${a}&show=${a}`).ids, [a]);
  assert.throws(() => presentationLink([]));
  assert.throws(() => presentationLink(['bad']));
});

test('an answer or launch receipt never implies model progress or completion', () => {
  const answered = row(a, 'awaiting_pickup', {
    answers: [{ payload: { answer: 'Use the patio' } }],
    deliveries: [{ outcome: 'launched' }],
    progress: [{ payload: { stage: 'completed', evidence: 'Older completed event' } }]
  });
  const stage = presentationStage(answered);
  assert.equal(stage.label, 'Answer saved');
  assert.equal(stage.step, 2);
  assert.match(stage.evidence, /pickup has not been observed/i);
  assert.doesNotMatch(stage.evidence, /Older completed/);
  for (const state of ['acknowledged', 'resumed', 'completed', 'withdrawn']) {
    const current = row(a, state, {
      progress: [
        {
          recorded_at: '2026-11-08T16:00:00Z',
          payload: { stage: state, evidence: 'Exact source result <script>unsafe</script>' }
        }
      ]
    });
    assert.equal(
      presentationStage(current).evidence,
      'Exact source result <script>unsafe</script>'
    );
  }
  assert.equal(presentationStage(row(a, 'completed')).label, 'Completed');
  assert.equal(presentationStage(row(a, 'withdrawn')).label, 'No longer needed');
});

test('conflicts, uncertainty and unknown states cannot appear as successful work', () => {
  for (const state of ['answer_conflict', 'conflict', 'uncertain_action', 'future_state']) {
    assert.equal(presentationStage(row(a, state)).step, 0);
  }
  assert.equal(
    presentationStage(row(a, 'completed', { uncertain_actions: [{ id: 'effect' }] })).step,
    0
  );
  assert.equal(
    presentationStage(row(a, 'completed', { revisions: [{ id: 'one' }, { id: 'two' }] })).step,
    0
  );
});

test('compiled presentation exposes last-known and missing work, and escapes answer/result text', async () => {
  const fs = await import('node:fs');
  const { pathToFileURL, fileURLToPath } = await import('node:url');
  const { compile } = await import('svelte/compiler');
  const { render } = await import('svelte/server');
  const cache = new URL('../node_modules/.cache/', import.meta.url);
  fs.mkdirSync(cache, { recursive: true });
  const dir = fs.mkdtempSync(fileURLToPath(new URL('presentation-', cache)));
  const file = dir + '/server.mjs';
  const source = fs.readFileSync(
    new URL('../src/lib/components/Presentation.svelte', import.meta.url),
    'utf8'
  );
  const compiled = compile(source, { generate: 'server' })
    .js.code.replace(
      /(['"])\.\.\/presentation\.js\1/g,
      JSON.stringify(new URL('../src/lib/presentation.js', import.meta.url).href)
    )
    .replace(
      /(['"])\.\.\/unblock-view\.js\1/g,
      JSON.stringify(new URL('../src/lib/unblock-view.js', import.meta.url).href)
    );
  fs.writeFileSync(file, compiled);
  try {
    const component = (await import(pathToFileURL(file).href)).default;
    const result = row(a, 'completed', {
      agent_id: 'demo-agent',
      answers: [{ payload: { answer: '<img src=x onerror=alert(1)>' } }],
      progress: [{ payload: { stage: 'completed', evidence: '<script>unsafe</script>' } }]
    });
    const html = render(component, {
      props: {
        rows: [result],
        ids: [a, b],
        grants: [],
        checked: '2026-11-08T16:00:00Z',
        error: 'offline',
        selectionError: '',
        onselect() {}
      }
    }).body;
    assert.match(html, /Last known source/);
    assert.match(html, /selected request is unavailable/);
    assert.match(html, /Agent’s result/);
    assert.match(html, /&lt;script>/);
    assert.doesNotMatch(html, /<script>unsafe/);
    assert.doesNotMatch(html, /<img src=x/);
    assert.match(html, /Saving an answer does not mean/);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
});
