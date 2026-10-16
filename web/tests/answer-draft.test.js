import test from 'node:test';
import assert from 'node:assert/strict';
import { editDraft, reviewDraft, submitDraft, failedAnswer } from '../src/lib/answer-draft.js';

test('a draft keeps the question shown at first edit until explicit review of a changed question',()=>{
 const first=editDraft(undefined,'request','revision-one','Blue');
 const changed=editDraft(first,'request','revision-two','Blue please');
 assert.equal(changed.revision,'revision-one');assert.throws(()=>submitDraft(changed,'revision-two'));
 const reviewed=reviewDraft(changed,'revision-two');assert.equal(submitDraft(reviewed,'revision-two').answer,'Blue please');assert.equal(reviewed.revision,'revision-two');
 assert.equal(submitDraft(changed,'revision-two',true).revision,'revision-one');
});

test('invalid long answers never enter pending and definite rejection restores editing',()=>{
 const draft=editDraft(undefined,'r','v','x'.repeat(16001));assert.throws(()=>submitDraft(draft,'v'),/16000/);
 const valid=editDraft(undefined,'r','v','Blue');assert.equal(failedAnswer(valid,'rejected'),null);
 const uncertain=failedAnswer(valid,'uncertain');assert.equal(uncertain.intent_id,valid.intent_id);assert.equal(failedAnswer(uncertain,'rejected').intent_id,valid.intent_id);assert.equal(failedAnswer(undefined,'uncertain'),null);
});
