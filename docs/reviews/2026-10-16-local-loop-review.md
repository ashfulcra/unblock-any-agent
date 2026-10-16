**Verdict: revise before accepting the local recovery/pickup slice.** No Critical findings. Six Important findings remain despite all 25 tests and the synthetic smoke passing.

Reviewed `91dd2e2..99809a8`, including the plan, specifications and AGENTS.md. Additional reproductions used disposable state; no repository or private maintainer/V5 state was changed. No Claude/model invocation occurred.

1. **Important — Late progress can erase attention for a newer answer.**  
   [store.py:261](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:261), [store.py:268](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:268)  
   Trigger: worker reads answer A; owner submits incompatible answer B against the same request revision; worker reports `resumed` using A. The server checks only the request revision and unconditionally changes status. Reproduced `conflicting_answers=True`, `status=resumed`, and empty attention. B remains stored but loses pickup.  
   **Correction:** make progress conditional on the response set the worker reconciled, or track handling per response so unseen answers remain pending. Preserve stale progress as history without clearing newer obligations.  
   **Missing regression:** interleave A fetch → B answer → A progress, including a delayed retry of A’s prior progress.

2. **Important — Uncertain actions disappear from recovery after `resumed`.**  
   [store.py:235](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:235), [store.py:264](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:264), [store.py:281](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:281)  
   Trigger: declare an action, report `resumed`, then lose the session before settling the action. Only `completed` is guarded; attention excludes `resumed` requests. Reproduced an uncertain action with empty agent attention. Declaring a new action on an already resumed request also leaves it hidden.  
   **Correction:** independently retain uncertain actions in recovery/attention, regardless of request progress; distinguish continuation evidence from unresolved action obligations.  
   **Missing regression:** restart after both declare → resumed and resumed → declare; replacement must discover and reconcile the action.

3. **Important — Replacement agents cannot discover unanswered requests.**  
   [store.py:244](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:244)  
   Trigger: an agent creates a request and disappears before the owner answers. Its replacement calls the documented `attention` command and receives no open requests. There is no agent listing endpoint or lookup by logical key, so recovery requires separately remembering identifiers or the original payload. Reproduced this omission.  
   **Correction:** return the agent’s outstanding open requests, distinguishing “waiting for owner” from actionable answers; listeners can continue filtering dispatch eligibility.  
   **Missing regression:** new Store/client with only the existing credential discovers the original unanswered context and commitment.

4. **Important — Retry timing permits concurrent dispatch of the same work.**  
   [listener.py:89](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/listener.py:89)  
   Trigger: a worker lasts longer than the default 60-second retry interval, while another scheduled invocation or replacement listener uses the same ledger. The second tick overwrites the `dispatching` row and launches another worker. Routes allow 300 seconds. A controlled-clock reproduction produced two launches before either finished.  
   **Correction:** use an exclusive execution claim/lease that covers the running command, with explicit recovery of abandoned or uncertain attempts. Prevent stale workers from overwriting a newer attempt’s result.  
   **Missing regression:** two listeners sharing a ledger, command duration exceeding retry interval, plus crash/restart recovery without overlapping execution.

5. **Important — Settling the blocker does not release blocked delivery.**  
   [listener.py:89](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/listener.py:89), [store.py:293](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/store.py:293)  
   Trigger: worker reports `blocked` because of an uncertain action; an authorized successor verifies and settles that action. Settlement changes neither request status nor delivery key. The listener permanently suppresses the request because its last blocked progress followed the previous dispatch. Reproduced pending work with zero dispatch attempts even at `retry_after=0`.  
   **Correction:** version relevant reconciliation changes and invalidate blocked suppression when the prerequisite changes, or explicitly transition released work back to actionable state.  
   **Missing regression:** blocked delivery → action settlement → automatic pickup using unchanged answers and route.

6. **Important — An interrupted synthetic artifact can falsely prove continuation.**  
   [__main__.py:84](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/__main__.py:84), [__main__.py:87](/Users/clawdbotvm/Developer/unblock-any-agent/unblock/__main__.py:87)  
   Trigger: interrupt `private_write` after creating the output file but before completing JSON. On retry, existence alone bypasses writing and reports `resumed`. Reproduced a zero-byte artifact being accepted as continuation evidence.  
   **Correction:** publish artifacts atomically and validate existing content against the current request/response before reporting progress. Preserve invalid output as an explicit recovery failure.  
   **Missing regression:** zero-byte, truncated and mismatched existing artifacts must not produce successful continuation.

No separate Minor findings warrant blocking this slice.

**Considered without finding a demonstrated violation:** account/workspace/agent authorization, listener environment scoping, credential revocation, role restrictions, request/answer retry keys, immutable revision history, wrong-agent credential rejection, Host/Origin checks, static path handling, response text rendering, private config checks, argv dispatch, failed-source pending retention, and distinguishing process exit from authenticated progress.

**Declined to judge:** actual Claude permission enforcement and session behavior, production OAuth/MCP, ChatGPT pickup, hosting, marketplace readiness, and visual browser acceptance. These require separate integration evidence. The Claude adapter received source-level review only.
