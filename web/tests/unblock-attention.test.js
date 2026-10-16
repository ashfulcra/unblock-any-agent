import test from 'node:test';
import assert from 'node:assert/strict';
import {needsHuman,currentCheck,pendingChecks,checkKey} from '../src/lib/unblock-attention.js';
test('unanswered conflicting questions stay in primary human attention',()=>{
 assert.equal(needsHuman({revisions:[{id:'a'},{id:'b'}],answers:[]}),true);
 assert.equal(needsHuman({revisions:[{id:'a'}],answers:[{id:'answer'}]}),false);
});
test('a retained old uncertain check cannot block checking a later revision',()=>{
 const old={expectation_id:'work',revision:'old',_uncertain:true,_receipt:'receipt'};
 const pending={[checkKey(old)]:old},row={id:'work',revisions:[{id:'new'}]};
 assert.deepEqual(currentCheck(row,pending),{expectation_id:'work',revision:'new'});
 assert.deepEqual(pendingChecks(row,pending),[old]);
 const fresh=currentCheck(row,pending);pending[checkKey(fresh)]=fresh;
 assert.equal(pendingChecks(row,pending).length,2);assert.equal(pending[checkKey(old)]._receipt,'receipt');
});
