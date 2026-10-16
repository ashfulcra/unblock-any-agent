# Run the local Unblock loop

The repository now includes a working loopback proof: separate owner/agent/listener credentials, durable requests and responses, a small human dashboard, continuity recovery, and a listener that routes through trusted local commands. It uses Python 3.13+ and the standard library, with no product package installation required.

This is not the public release. Production OAuth, remote MCP/Events, Fulcra artifact integration, official marketplace installs and hosted personal dashboards remain separate acceptance work. The server deliberately refuses public bindings.

## Quick verification

```sh
python3 -m unittest discover -s tests -v
python3 scripts/smoke.py
```

The smoke script creates disposable synthetic state and starts an independent listener process before the owner answers. It passes only when the worker retrieves the answer and context, writes one synthetic continuation artifact, and reports progress. The controller checks the result but does not nudge the worker. No external action is performed.

A bounded model-backed variant is available when Claude Code is installed and authenticated:

```sh
python3 scripts/smoke.py --claude
```

It creates a dedicated synthetic Claude session under normal permission checks, allows only the local demo-worker command, and limits turns and API budget. It uses the configured model, preserves caller attribution, and does not join an unrelated session. This test invokes a model and may incur normal API usage. A failed native permission check remains a failed route; the result stays pending. It does not prove a plugin or a closed desktop session can be awakened.

## Start a persistent local dashboard

```sh
python3 -m unblock init --state .state --port 8765
python3 -m unblock serve --db .state/work.db --port 8765
```

Choose a different port in both commands if that port is already occupied. Open the printed loopback address. Use the owner credential in the private `.state/owner.json` file to sign in. Credentials stay out of URLs. Browser sessions use HTTP-only SameSite cookies; a restart requires signing in again. State files and credentials are excluded from Git.

In another terminal, enroll a worker and a listener:

```sh
python3 -m unblock enroll --name Worker --environment local --out .state/worker.json
python3 -m unblock enroll --name Listener --kind listener --environment local --out .state/listener.json
python3 -m unblock --config .state/worker.json ask --key first-need --need 'Which option should I use?' --context '{"goal":"Run the pilot","next_action":"Save the decision and continue the proof"}'
```

The private worker/listener configs contain their separate credentials. Enrollment prints only the ID and config location. The worker's identity comes from its credential; callers cannot choose another sender in the request body.

## Configure the environment listener

For the synthetic CLI worker, create a private route file:

```sh
python3 - <<'PY'
from pathlib import Path
import sys
from unblock.client import private_read, private_write
agent = private_read('.state/worker.json')
private_write('.state/routes.json', {
    agent['id']: {
        'argv': [sys.executable, '-m', 'unblock', '--config', str(Path('.state/worker.json').resolve()), 'demo-worker', '--output', str(Path('.state/artifacts').resolve())],
        'cwd': str(Path.cwd()),
        'timeout': 10
    }
})
PY
python3 -m unblock --config .state/listener.json listen --environment local --routes .state/routes.json --state .state/delivery.db --interval 5
```

Answer the open request in the dashboard. The already-running listener checks the source, dispatches to that worker, and records whether it failed, merely queued, or actually resumed. The synthetic worker writes a local decision artifact and reports its progress; it does not execute arbitrary instructions from an answer. Refresh the dashboard to see recent progress.

Use the listener invocation as the body of a supported scheduled task or dedicated listener session. An existing runtime heartbeat can instead run it with `--once`. Installing a system schedule is a separate environment operation; these instructions do not install one. Keep one defined operating owner and restart procedure for each environment.

Routes are owner-controlled argv lists, never commands supplied by incoming work. Config files must be owned by the current user, mode 0600, and not symlinks. A listener can check only its own workspace/environment and cannot report progress as the worker. Different agents need different credentials and confirmed routes. Unsupported runtime dispatch remains an explicit missing route.

## Recovery and inspection

```sh
python3 -m unblock --config .state/worker.json attention
python3 -m unblock --config .state/worker.json show REQUEST_ID
python3 -m unblock recent
```

The original worker process can end before an answer arrives. A replacement with the same authorized agent credential retrieves the saved goal, answer revision and prior progress. For a different identity, use owner-authorized enrollment and a deliberate handoff; do not copy another agent's identity casually. Restart the listener using its same delivery ledger. A changed trusted local route is retried independently of an earlier failed route.

Reading or delivering a result does not remove it from pending work. A zero-exit worker that does not report progress is shown as queued, with bounded retry. A failed source read retains known pending items and reports uncertainty. Stale answers remain in history but cannot authorize progress against a newer request revision. Conflicting answers remain visible for reconciliation. Progress against multiple current answers must include the `answer_revision` returned by `show`; this prevents delayed reports from hiding a newer answer. Open unanswered requests remain discoverable by the agent, and uncertain actions remain in attention even after continuation.

For consequential external actions, the core exposes `declare` and `settle` operations to retain intent and evidence. An interrupted action remains uncertain; a successor must inspect the actual result or obtain reconciliation. This local proof does not offer universal exactly-once execution.

If a listener dies during dispatch, its durable execution claim prevents a second listener from launching overlapping work. Claims remain exclusive for the command timeout plus 30 seconds. After expiry, pickup reports `dispatch_recovery_required` rather than silently retrying. Verify that the previous worker stopped and reconcile any external actions, then release that claim with retained evidence:

```sh
python3 -m unblock --config .state/listener.json recover-dispatch REQUEST_ID --environment local --routes .state/routes.json --state .state/delivery.db --evidence 'Verified prior worker stopped; describe the observed result and reconciliation'
```

An active claim cannot be released. All listeners for an environment must share the same delivery ledger; separate ledgers cannot coordinate execution. A queued asynchronous route must deduplicate deliveries at its target as well. Settlement of an uncertain action changes the delivery revision, releasing the old blocked attempt for a fresh check.

Continuation artifacts and credential files are published atomically. Existing continuation artifacts must match the current request, answer and context; empty, truncated or mismatched output causes a visible failure instead of a resumed claim.

## Observed evidence

The automated suite covers account/agent isolation, revocation, concurrent retry convergence, stale and conflicting responses, replacement-store recovery, uncertain actions, HTTP boundaries, listener failure/restart, wrong-environment/agent routing, and queued delivery without acknowledgment. `scripts/smoke.py` adds the independent-process delayed-answer proof. The local dashboard was inspected with a synthetic account and its answer submission was verified to show “Waiting for the agent to pick up the answer.”

The independent-process `--claude` smoke also passed on Claude Code 2.1.301 using a new restricted synthetic session and a simple UUID-only command. Earlier heredoc attempts were correctly blocked by native command approval; the simpler authorized command passed without bypass flags. This establishes one local native route. It does not establish marketplace installation, busy-session routing or universal wake.
