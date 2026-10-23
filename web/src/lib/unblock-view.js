/** Present source text without inventing a summary or interpreting instructions.
 * @param {string} value @param {number} [limit] */
export function excerpt(value, limit = 155) {
  const text = (value || '').replace(/\s+/g, ' ').trim();
  if (text.length <= limit) return text;
  return text.slice(0, limit).replace(/\s+\S*$/, '') + '…';
}
/** @param {any} row */
export function requestView(row) {
  /** @type {Record<string,string[]>} */
  const states = {
    needs_you: ['attention', 'Decision needed'],
    conflict: ['attention', 'Question changed'],
    answer_conflict: ['attention', 'Review answers'],
    uncertain_action: ['attention', 'Verify action'],
    awaiting_pickup: ['waiting', 'Awaiting pickup'],
    acknowledged: ['waiting', 'Answer read'],
    resumed: ['waiting', 'Working'],
    completed: ['done', 'Completed'],
    withdrawn: ['done', 'No longer needed']
  };
  const [lane, status] = states[row.state] || ['attention', 'Needs review'];
  const question = row.revisions[0]?.payload || {};
  return {
    lane,
    status,
    title: excerpt(question.need || 'Review this request', 120),
    context: excerpt(question.context, 190),
    recommendation: excerpt(question.recommendation, 150)
  };
}
/** Only the folded current stage counts as observed progress. Array arrival
 * order and a saved human answer never imply that an agent resumed.
 * @param {any} row */
export function progressView(row) {
  const titles = /** @type {Record<string,string>} */ ({
    awaiting_pickup: 'Awaiting agent pickup',
    acknowledged: 'Answer read',
    resumed: 'Work resumed',
    completed: 'Completed',
    withdrawn: 'No longer needed'
  });
  const title = titles[row.state];
  if (!title) return null;
  const events = (row.progress || [])
    .filter((/** @type {any} */ p) => p.payload.stage === row.state)
    .sort(
      (/** @type {any} */ a, /** @type {any} */ b) =>
        (Date.parse(b.recorded_at || '') || 0) - (Date.parse(a.recorded_at || '') || 0)
    );
  return {
    title,
    evidence:
      events[0]?.payload.evidence ||
      (row.state === 'awaiting_pickup'
        ? 'Your decision is saved. Agent pickup has not been observed yet.'
        : 'No additional progress details supplied.'),
    at: events[0]?.recorded_at || null
  };
}
/** @param {any[]} rows @param {{query?:string,agent?:string,lane?:string,grants?:any[]}} [options] */
export function filterRequests(rows, { query = '', agent = '', lane = '', grants = [] } = {}) {
  const terms = query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  return rows.filter((row) => {
    if (agent && row.agent_id !== agent) return false;
    if (lane && requestView(row).lane !== lane) return false;
    const name = grants.find((g) => g.agent_id === row.agent_id)?.name || row.agent_id;
    const haystack = [
      name,
      row.agent_id,
      ...row.revisions.flatMap((/** @type {any} */ r) => Object.values(r.payload))
    ]
      .join(' ')
      .toLocaleLowerCase();
    return terms.every((term) => haystack.includes(term));
  });
}
/** @param {any[]} rows @param {any[]} [grants] */
export function groupAgents(rows, grants = []) {
  return [...new Set(rows.map((row) => row.agent_id))]
    .map((id) => {
      const requests = rows.filter((row) => row.agent_id === id),
        grant = grants.find((g) => g.agent_id === id && g.kind !== 'listener');
      return {
        id,
        name: grant?.name || id,
        environment: grant?.environment || '',
        requests,
        attention: requests.filter((row) => requestView(row).lane === 'attention').length
      };
    })
    .sort((a, b) => b.attention - a.attention || a.name.localeCompare(b.name));
}
/** @param {string|null|undefined} since @param {number} [now] */
export function waitingAge(since, now = Date.now()) {
  const start = since ? Date.parse(since) : NaN;
  if (!Number.isFinite(start) || start > now) return 'Waiting time unknown';
  const minutes = Math.floor((now - start) / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ${minutes % 60}m`;
  return `${Math.floor(hours / 24)}d ${hours % 24}h`;
}
/** Unknown dates stay last. Sorting never resets a request's waiting clock.
 * @param {any[]} rows @param {string} [order] */
export function sortRequests(rows, order = 'oldest') {
  const time = (/** @type {any} */ row) => Date.parse(row.created_at || '');
  return [...rows].sort((a, b) => {
    const x = time(a),
      y = time(b);
    if (!Number.isFinite(x)) return Number.isFinite(y) ? 1 : 0;
    if (!Number.isFinite(y)) return -1;
    return order === 'newest' ? y - x : x - y;
  });
}
