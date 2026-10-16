/** @param {any} row */
export function needsHuman(row){return row.revisions.length!==1 || row.answers.length===0;}
/** @param {any} body */
export function checkKey(body){return body.expectation_id+':'+body.revision;}
/** @param {any} row @param {Record<string,any>} pending */
export function currentCheck(row,pending){const body={expectation_id:row.id,revision:row.revisions[0].id};return pending[checkKey(body)] || body;}
/** @param {any} row @param {Record<string,any>} pending @returns {any[]} */
export function pendingChecks(row,pending){return Object.values(pending).filter(body=>body.expectation_id===row.id);}
