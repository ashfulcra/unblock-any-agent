# Detect missed native work updates

Workers can declare an expected update without creating a human question. An independent monitor records a concern when that update is missed, including after the worker session ends. Human questions remain in **Needs you**; missed updates appear in **Investigate** and in the responsible worker's recovery. A missed update establishes neither its cause nor a human action.

This uses the existing Fulcra-native pilot, authentication, signed annotation and sealed worker/listener profiles. No newly registered OAuth client or external database is required. Use the canonical checkout or a self-contained 0.5.0 package. The native transport has eight worker tools; the separate loopback proof retains seven.

## Declare and update work

Use native MCP `record_work_update` with `key`, `summary`, `context`, actual `evidence`, `next_action`, explicit reviewed `parent_revisions`, `status`, `next_update_at` and optional `request_id`. A working deadline is integer Unix seconds after server time and within 30 days. Terminal states `completed` or `cancelled` require null. The associated question and original environment binding remain fixed. A replacement uses that same authorized environment; cross-environment handoff is not inferred.

Or create a private initial body from the canonical checkout/export:

```sh
python3 - <<'PY'
from pathlib import Path
import time, uuid
from unblock.client import private_write
private_write(Path.home()/'.local/state/unblock/review-start.json', {
    'intent_id':str(uuid.uuid4()), 'work_key':'review',
    'summary':'Review implementation', 'context':'Review the current change',
    'evidence':'Started inspecting the source', 'next_action':'Return findings',
    'parents':[], 'status':'working', 'next_update_at':int(time.time())+300,
    'request_id':None
})
PY
python3 -m unblock.native_client --config /PRIVATE/native-agent.json work_update --file "$HOME/.local/state/unblock/review-start.json"
python3 -m unblock.native_client --config /PRIVATE/native-agent.json attention
```

Replace `/PRIVATE/native-agent.json` with the actual private worker profile. The file writer refuses to overwrite an earlier body: reuse that file for uncertainty/retries. Verify the exact returned `record_id` in `expectations[].history` before relying on it. If the deadline passes before an uncertain initial write can be read back, preserve the original intent and inspect the source; a rejected retry cannot prove the earlier attempt did not publish.

For another update, save a new body/intent/file with the same work key and all parent revisions actually reviewed. Retain the request link, context and useful evidence. Concurrent heads remain a conflict until explicitly reconciled. An update saying work continues does not establish that a human request resumed. Closing an expectation never answers its linked question or clears an uncertain external action.

## Run an independent monitor

The owner enrolls an **Environment listener** for the worker's exact environment and explicit agent ID set, as described in [listener setup](listener-setup.md). Use its separate private profile, never a worker or owner credential. A listener can record overdue observations but cannot change worker expectations or report progress.

```sh
python3 -m unblock.native_monitor --config /PRIVATE/native-listener.json --environment ENVIRONMENT --state /PRIVATE/monitor.db --interval 60 --once
python3 -m unblock.native_monitor --config /PRIVATE/native-listener.json --environment ENVIRONMENT --state /PRIVATE/monitor.db --interval 60 --duration 600
```

Choose the actual private profile, environment and absolute ledger path. The parent directory must not be writable by other users; the SQLite file must be an owned regular 0600 file without symlinks/hardlinks. The first command performs one check. The second loops in its current session and stops between checks after its selected duration; an in-flight bounded source call can finish first. Omit duration only when deliberately running that session's loop. No startup service or scheduled task is installed.

The monitor reopens its profile each tick, accepts explicit renewal of the same scope, and freezes the ledger's source/listener/environment/agent mapping. Keep the original ledger across restart and renewal. Do not point it at another dashboard, identity or scope, or replace it to discard pending records. The existing trusted [renewal operator](native-renewal.md) is a separately authorized setup; this monitor never acquires owner authentication.

Quiet checks use no model and launch no agent command. Each pass processes at most 32 observation submissions. The server validates its current clock, the exact sole current revision and monitor scope, and derives a stable observation for that revision/observer. Repeated or concurrent checks do not create another concern card.

## Read the result and recover

CLI `checked: true` means the authorized source was checked, not that the worker noticed a concern. `persisted` counts cumulative journal receipts verified against exact native observation history; `pending_receipts` and `receipt_errors` retain publication obligations. `pending_known` preserves the last checked active expectations. Unknown source/revoked access returns a failed check and a nonzero one-shot exit; it is not an empty queue. A pending receipt also makes a one-shot exit nonzero so a scheduler cannot call it a completed check.

After source recovery, run the same command/profile/ledger. An accepted observation is confirmed only by matching its original body and record in native history, including after a newer work update. A later definitive rejection remains in the rejected journal and cannot erase an earlier uncertain attempt; it can still reconcile if the original observation becomes visible. First resolve the exact source, revision or access problem. Keep unresolved bodies and receipts for inspection; the monitor will not silently reset them or repeatedly submit a definitively rejected snapshot. A known confirmed observation disappearing from a purported complete source is treated as unknown rather than forgotten.

The owner can select **Check this update** for one due item. The browser retains an uncertain original check across reload and a changed work revision until exact observation readback. Those manual checks are distinct from environment-monitor observations. The dashboard keeps answered work/history below current human questions and investigations.

A concern is available to its worker through `recover_work`/native attention. General automatic investigation dispatch has not been verified; an answer-only route must not be presumed to handle this new kind. Verify its actual route before promising automatic follow-up. The dashboard states that persistent automatic checks have not been verified. A saved command, old observation or successful one-shot check proves no currently running monitor. Configure and test the actual trigger, cadence, credentials, lifetime and restart procedure for each advertised unattended environment.

Source, skills, personal forks and optional stars: [ashfulcra/unblock-any-agent](https://github.com/ashfulcra/unblock-any-agent).

New expectation identities include authenticated agent, granted environment and work key. Existing pilot identities remain readable and are updated in place in their original environment; no records are moved or discarded. Monitors cap each pass at32 submissions and prioritize the least-attempted pending checks so delayed readback cannot starve later work. Every successful receipt is retained even if a concurrent attempt was rejected.

Uncertain manual checks are retained per expectation and revision. An old rejected or delayed check remains separately retryable while a new current revision can be checked. Existing browser entries migrate without dropping their original revision or receipt. Unanswered conflicting questions remain in primary human attention. Concurrent first declarations with different linked questions retain both links explicitly; the agent must review all heads to reconcile to one already-known link. Historical question associations and exact accepted retry receipts remain recoverable.
