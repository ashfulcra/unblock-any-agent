const $ = (id) => document.getElementById(id);
async function api(path, data) {
  const response = await fetch(path, {method: data === undefined ? 'GET' : 'POST', headers: {'Content-Type': 'application/json'}, body: data === undefined ? undefined : JSON.stringify(data)});
  const body = await response.json();
  if (!response.ok) { const error = new Error(body.error); error.status = response.status; throw error; }
  return body;
}
function node(tag, text, className) { const element = document.createElement(tag); if (text !== undefined) element.textContent = text; if (className) element.className = className; return element; }
function report(error) { $('notice').textContent = error.message.replaceAll('_', ' '); }
async function load() {
  try {
    await api('/api/me');
    const pendingItems = await api('/api/attention');
    const recentItems = await api('/api/recent');
    const items = [...pendingItems, ...recentItems];
    $('login').hidden = true; $('dashboard').hidden = false; $('notice').textContent = '';
    $('summary').textContent = `${pendingItems.length} awaiting a next step · ${recentItems.length} recently resumed`;
    $('requests').replaceChildren();
    if (!items.length) {
      const empty = node('article', undefined, 'empty'); empty.append(node('span', '✓', 'empty-icon'), node('h2', 'Nothing waiting on you.'), node('p', 'Open requests and returned answers will appear here.')); $('requests').append(empty);
    }
    for (const item of items) {
      const card = node('article', undefined, 'request');
      const top = node('div', undefined, 'card-top'); top.append(node('span', item.context.goal || 'Agent request', 'goal'), node('span', item.status.replaceAll('_', ' '), `status ${item.status}`));
      card.append(top, node('h2', item.need));
      if (item.context.next_action) card.append(node('p', `Then: ${item.context.next_action}`, 'next-action'));
      for (const response of item.responses) card.append(node('p', `${response.stale ? 'Earlier answer' : 'Answer saved'}: ${response.answer}`, 'saved'));
      for (const action of item.actions) if (action.status === 'uncertain') card.append(node('p', `Needs verification: ${action.description}`, 'warning'));
      if (item.conflicting_answers) card.append(node('p', 'Multiple answers need reconciliation by the responsible agent.', 'warning'));
      if (item.status === 'answered') card.append(node('p', 'Waiting for the agent to pick up the answer.', 'waiting'));
      for (const progress of item.progress) card.append(node('p', `${progress.state}: ${progress.evidence}`, 'progress'));
      if (item.status === 'resumed' || item.status === 'completed') { $('requests').append(card); continue; }
      const form = node('form', undefined, 'answer-form'); const label = node('label', 'Your answer'); const input = node('textarea'); input.required = true; input.maxLength = 4000; input.rows = 2; input.placeholder = 'A decision, missing detail, or the next direction…'; label.append(input);
      const button = node('button', 'Send answer →'); button.type = 'submit'; form.append(label, button);
      let pending = null;
      form.addEventListener('submit', async (event) => { event.preventDefault(); if (!pending || pending.answer !== input.value) pending = {revision: item.revision, answer: input.value, key: crypto.randomUUID()}; button.disabled = true; try { await api(`/api/requests/${item.id}/answers`, pending); await load(); } catch (error) { report(error); button.disabled = false; } });
      card.append(form); $('requests').append(card);
    }
  } catch (error) {
    if (error.status === 401) { $('login').hidden = false; $('dashboard').hidden = true; } else report(error);
  }
}
$('login-form').addEventListener('submit', async (event) => { event.preventDefault(); try { await api('/api/session', {token: $('token').value}); $('token').value = ''; await load(); } catch (error) { report(error); } });
$('refresh').addEventListener('click', load);
$('logout').addEventListener('click', async () => { try { await api('/api/logout', {}); await load(); } catch (error) { report(error); } });
load();
