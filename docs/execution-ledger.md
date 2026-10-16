# Execution ledger

2026-10-16: Ash requested an exit check every turn and continuous safe execution. The maintainer’s private exit check now includes addressed replies as well as V5 work. Four regression checks passed; live source verification remains to be recorded.

Decision: proceed inline in the clean checkout on a local feature branch. No other agent is editing this repository; avoid unnecessary worktree setup. Shared backend is a provisional choice, not a user preference. Local SQLite and owner bootstrap auth are limited to the loopback proof, not a claim of production or marketplace readiness.

Plan: [first local loop](superpowers/plans/2026-10-16-first-local-loop.md). Spec: [first release](superpowers/specs/2026-10-16-unblock-first-release.md).

Task 1 complete: 10 durable-core tests failed for the missing store, then passed against the implementation. Verified account/agent isolation, environment listener scope, credential revocation, concurrent request convergence, retry conflicts, stale answers, retained conflicting answers, replacement recovery and uncertain-action reconciliation. Local store has no V5 dependency.

Task 2 complete: real loopback HTTP tests cover authentication, revoked credentials, identity isolation, Host/Origin checks, bounded JSON, owner cookie/logout and private-path rejection. The response UI renders pending answers and observed recent progress separately.

Task 3 local route complete: real subprocess workers prove delayed pickup, wrong-agent/environment isolation, failed-route replacement, queued-without-ack behavior and restart recovery. A resource-leak regression failed, then passed after explicitly closing listener database connections. Full suite: 23 passed. These are synthetic worker tests, not yet evidence of native Claude or ChatGPT pickup.
