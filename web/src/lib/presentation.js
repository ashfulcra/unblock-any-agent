import { progressView, requestView } from './unblock-view.js';

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Exact IDs are a display selection, never an authorization or a write.
 * @param {string} search */
export function parsePresentation(search) {
  const query = new URLSearchParams(search);
  if (!query.has('present') && !query.has('show')) return { active: false, ids: [], error: '' };
  const ids = query.getAll('show');
  if (
    query.getAll('present').length !== 1 ||
    query.get('present') !== '1' ||
    !ids.length ||
    ids.length > 6 ||
    ids.some((id) => !uuid.test(id))
  ) {
    return {
      active: true,
      ids: [],
      error:
        'This presentation needs one to six valid request IDs. Return to the workspace to choose them again.'
    };
  }
  return { active: true, ids: [...new Set(ids.map((id) => id.toLowerCase()))], error: '' };
}

/** @param {string[]} ids */
export function presentationLink(ids) {
  const query = new URLSearchParams({ present: '1' });
  ids.forEach((id) => query.append('show', id));
  const selection = parsePresentation(query.toString());
  if (selection.error) throw new Error(selection.error);
  return '/?' + query.toString();
}

/** Preserve selection order and explicitly expose absent records.
 * @param {any[]} rows @param {string[]} ids */
export function presentationRows(rows, ids) {
  const found = ids.map((id) => rows.find((row) => row.id === id));
  return { rows: found.filter(Boolean), missing: ids.filter((_, index) => !found[index]) };
}

/** Only current folded stages count. Receipts and historical events do not.
 * @param {any} row */
export function presentationStage(row) {
  if (
    row.revisions.length !== 1 ||
    row.uncertain_actions.length ||
    ['conflict', 'answer_conflict', 'uncertain_action'].includes(row.state)
  ) {
    return {
      step: 0,
      label: 'Review required',
      evidence: 'Review the full question, answers and uncertain effects before continuing.',
      tone: 'attention'
    };
  }
  const stages = /** @type {Record<string,[number,string]>} */ ({
    needs_you: [1, 'Decision needed'],
    awaiting_pickup: [2, 'Answer saved'],
    acknowledged: [3, 'Answer read'],
    resumed: [3, 'Work resumed'],
    completed: [4, 'Completed'],
    withdrawn: [0, 'No longer needed']
  });
  const [step, label] = stages[row.state] || [0, 'Needs review'];
  return {
    step,
    label,
    evidence: progressView(row)?.evidence || '',
    tone: requestView(row).lane
  };
}
