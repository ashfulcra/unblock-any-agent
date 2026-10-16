/** @param {any} existing @param {string} request_id @param {string} revision @param {string} answer */
export function editDraft(existing,request_id,revision,answer) {
  return {...(existing || {request_id,revision,intent_id:crypto.randomUUID()}),answer};
}
/** @param {any} draft @param {string} revision */
export function reviewDraft(draft,revision) {
  return {...draft,revision,intent_id:crypto.randomUUID()};
}
/** @param {any} draft @param {string} revision @param {boolean} [isRetry] */
export function submitDraft(draft,revision,isRetry=false) {
  if (!draft || (!isRetry && draft.revision!==revision)) throw new Error('Question changed; review the current question before sending');
  return {...draft};
}
