import test from 'node:test';
import assert from 'node:assert/strict';
import { editDraft, reviewDraft, submitDraft } from '../src/lib/answer-draft.js';

test('a draft keeps the question shown at first edit until explicit review of a changed question',()=>{
 const first=editDraft(undefined,'request','revision-one','Blue');
 const changed=editDraft(first,'request','revision-two','Blue please');
 assert.equal(changed.revision,'revision-one');assert.throws(()=>submitDraft(changed,'revision-two'));
 const reviewed=reviewDraft(changed,'revision-two');assert.equal(submitDraft(reviewed,'revision-two').answer,'Blue please');assert.equal(reviewed.revision,'revision-two');
 assert.equal(submitDraft(changed,'revision-two',true).revision,'revision-one');
});
