# Fulcra Self Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make account-owned Fulcra deployment repeatable and apply the approved public publisher/license choices.

**Architecture:** Preserve the deployed Svelte/Fulcra backend. A Python setup verifier uses existing CLI authentication and verified Fulcra resources to generate private environment configuration; the Fulcra skill continues to own resource creation/deployment.

**Tech Stack:** Python standard library, existing Fulcra API client helpers, Svelte, generated Claude/OpenAI packages.

**Spec:** `docs/superpowers/specs/2026-10-23-fulcra-self-deployment-design.md`

## Global Constraints

- Keep existing template sign-in and worker/owner scopes unchanged.
- No shared issuer/GCS service changes or copied maintainer credentials.
- Source license Apache-2.0; publisher Fulcra Dynamics; canonical source remains ashfulcra/unblock-any-agent.
- Private setup journal outside source, mode0600; never overwrite different environment data or rotate an existing signing key.
- Follow existing Fulcra workspace/harness; second-account acceptance remains separate until actual Gatekeeper sign-in.

## Review Focus

- Shared/foreign annotations must not pass ownership checks.
- Account/resource switches must not reuse another user's signing key.
- Retry after partial output must retain the same key and private state.
- Existing/symlink/non-private output must not be overwritten or disclosed.
- Exported packages must include license/notices and no private setup files.

### Task 1: Verified private setup

Files: `unblock/fulcra_setup.py`, `tests/test_fulcra_setup.py`, `docs/personal-dashboard.md`, `web/README.md`.

- [ ] Write failing behavioral tests for two owners, foreign resources, binding changes, retries, output collision and private permissions.
- [ ] Run the tests and observe failures before implementation.
- [ ] Implement `configure(project_id, harness_annotation, product_annotation, state_path, env_path, workspace, *, check_only=False, token_provider=cli_token, platform=platform_request)` with fixed Fulcra API reads, private journal and create-only environment output. Add `python3 -m unblock.fulcra_setup` CLI.
- [ ] Run targeted and full Python tests. Exercise the real CLI preflight against the existing owned deployment without changing its configuration.
- [ ] Update the agent setup recipe with the exact Fulcra skill resource creation, command, deployment and evaluation steps.

### Task 2: Approved metadata and delivery

Files: `LICENSE`, `THIRD_PARTY_NOTICES`, `scripts/build_plugins.py`, generated `plugins/`, `README.md`, current release docs, export tests.

- [ ] Add regression asserting generated publisher/license/notices and existing containment behavior.
- [ ] Add Apache 2.0 source license, preserve upstream notices and apply Fulcra Dynamics metadata. Regenerate exports.
- [ ] Run the full Python/web checks and exports; evaluate the intended setup workflow and read back published source/release changes.
- [ ] Record actual native progress against both reviewed answers. Withdraw the obsolete shared-target question for the core Fulcra path; preserve optional remote integration limits and Gatekeeper sign-in.
- [ ] Update own V5 tasks/checkpoint and Fulcra harness with accepted evidence. Continue returned review; exit only after exact-source check.
