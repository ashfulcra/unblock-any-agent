# First Local Unblock Loop Implementation Plan

> **For agentic workers:** Implement inline using superpowers:executing-plans and test-driven-development. Ash requested continuous safe execution without repeated handoffs. Preserve the execution ledger and run the exit check before yielding.

**Goal:** A local owner can answer an authenticated agent’s request; an environment listener routes it to the right worker, and a replacement can recover context and report continuation.

**Architecture:** Python standard-library application service, transactional SQLite local store, loopback-only HTTP JSON API, minimal response UI, CLI client and environment listener with trusted local command adapters. Production OAuth, remote MCP, Fulcra artifact linking and public hosting are subsequent integrations and must not be claimed by this proof.

**Tech Stack:** Python 3.13+, sqlite3, http.server, urllib, unittest; plain HTML/CSS/JavaScript for the minimal local view.

**Spec:** ../specs/2026-10-16-unblock-first-release.md and ../specs/2026-10-16-agent-work-pickup.md.

## Global constraints

- No legacy Coord dependency or private bus/session identifiers in source.
- Authenticate owner, agent and listener separately; scope each to owner/workspace/environment and reject impersonation.
- Bind the proof to loopback. Reject wrong Host/Origin; no public production-auth claim.
- Preserve context revisions, responses and pending pickup across restart; no receipt implies progress.
- Routes are trusted local argv configurations, never a remote shell command or model-provided destination.
- Preserve /unblock naming intent; do not publish placeholder packages.

## Review focus

- Neighboring agents and other accounts must not access or acknowledge the same private request.
- Reused logical keys with changed payloads and concurrent duplicates must not silently overwrite or multiply work.
- Old answers and interrupted external actions must not become fresh permission to repeat actions.
- Queued delivery, wrong routing, failed commands and disconnected sessions must leave work pending.
- Owner browser access must not expose agent tokens or allow another origin to write.

### Task 1: Authenticated durable core

Files: `unblock/store.py`, `unblock/__init__.py`, `tests/test_store.py`.

Interfaces: Store(path); bootstrap_owner(name); create_workspace(actor,name); enroll(actor,workspace,name,kind,environment); authenticate(token); request_help(actor,key,need,context); revise_request(actor,id,need,context); answer_request(actor,id,revision,answer,key); get_request(actor,id); get_attention(actor); report_progress(actor,id,response_id,state,evidence); revoke(actor,principal_id).

- [ ] Write tests for the complete loop, principal isolation, revocation, same-key retries, two concurrent submissions, stale/conflicting answers and new Store instance recovery.
- [ ] Run unittest and observe missing behavior fail.
- [ ] Implement the smallest transactional schema and access checks; keep tokens hashed and responses/revisions immutable.
- [ ] Run the task suite, inspect the output and commit.

### Task 2: Local service, CLI and response view

Files: `unblock/server.py`, `unblock/client.py`, `unblock/__main__.py`, `unblock/static/index.html`, `unblock/static/app.js`, `unblock/static/style.css`, `tests/test_http.py`.

Interfaces: server.serve(Store,host=127.0.0.1,port=8765); Client(url,token).call(method,path,data=None); CLI init/serve/workspace/enroll/ask/attention/show/answer/progress/revoke.

- [ ] Write HTTP tests for authorized operations, wrong-account requests, absent/revoked tokens, forbidden Origin/Host and malformed inputs.
- [ ] Observe failure, implement loopback service and CLI. Use HTTP-only SameSite owner session for the browser, with authenticated local login and no token in page links.
- [ ] Build the minimal request/answer/history view; show saved answers separately from agent progress.
- [ ] Run integration tests plus actual CLI/server smoke; inspect the UI and commit.

### Task 3: Environment listener and replacement recovery

Files: `unblock/listener.py`, `tests/test_listener.py`, `docs/local-proof.md`.

Interfaces: Listener(Client,environment,routes,state_path).tick(); private local routes map agent IDs to argv/cwd/timeout; worker payload JSON via stdin. Worker acknowledges and reports via its own credential.

- [ ] Write tests with real local subprocess workers for the delayed reply, wrong environment, failed/queued command, repeated ticks, restart and replacement routes.
- [ ] Observe failures, implement bounded checks and routing with no shell interpolation; validate config ownership/mode and use a private SQLite delivery ledger.
- [ ] Retain delivery attempts until worker progress proves continuation. Reconcile current server state on restart.
- [ ] Run a full synthetic ask → human answer → listener → worker progress scenario with a replacement worker; attempt a bounded real Claude native route only when authenticated and authorized. Record actual capability limits and any credentials needed.
- [ ] Commit code, usage and observed evidence.

### Task 4: Integration handoff and independent review

- [ ] Run the entire suite, CLI smoke and source secret/private-state checks.
- [ ] Obtain a fresh review of the local slice, fix consequential findings with regression tests, and retain the raw result.
- [ ] Keep production OAuth/provider setup, remote MCP/Events, actual-host package installation, Fulcra connection and hosting as explicit remaining tasks with their exact prerequisites.
- [ ] Update the implementation ledger and own V5 fold; continue safe unblocked work rather than declaring the complete product shipped.
