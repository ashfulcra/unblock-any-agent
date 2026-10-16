import test from 'node:test';
import assert from 'node:assert/strict';
import {runStatus} from '../src/lib/harness-status.js';
test('a completed run envelope retains its actual incomplete outcome',()=>{
 assert.equal(runStatus({events:[{step:'REVIEW',status:'completed'},{step:'REVIEW',status:'failed'},{step:'RUN_COMPLETE',status:'incomplete'}]}),'incomplete');
 assert.equal(runStatus({events:[{step:'RUN_COMPLETE',status:'failed'}]}),'incomplete');
});
test('successful, legacy and active outcomes remain distinct',()=>{
 assert.equal(runStatus({events:[{step:'RUN_COMPLETE',status:'completed'}]}),'completed');
 assert.equal(runStatus({events:[{step:'RUN_INCOMPLETE',status:'incomplete'}]}),'incomplete');
 assert.equal(runStatus({events:[{step:'ESCALATE',status:'completed'}]}),'escalated');
 assert.equal(runStatus({events:[{step:'GENERATE',status:'started'}]}),'in-progress');
});
test('an unrecognized terminal outcome never becomes successful',()=>{
 assert.equal(runStatus({events:[{step:'RUN_COMPLETE',status:'new-unknown-status'}]}),'unknown');
});
