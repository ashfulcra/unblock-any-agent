# Supported Node Runtime Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans. Ash explicitly requested autonomous continuation; do not add plan-approval pauses for this reversible configuration correction.

**Goal:** Make a clean Fulcra deployment select an adapter-supported Node runtime.

**Architecture:** Declare supported majors in existing package metadata and lockfile. Preserve the adapter and deployment route.

**Tech Stack:** npm, SvelteKit, Fulcra managed Vercel deployment.

**Spec:** `docs/superpowers/specs/2026-11-05-supported-node-runtime-design.md`

## Global Constraints

- Use `22.x || 24.x`; retain the Node 22 CI.
- Change no dependency versions, auth behavior, private key, annotation or deployment identity.
- Retain actual failure evidence and restore the saved disposable project's runtime after the probe.

## Task 1: Runtime selection and verification

Files: `web/package.json`, `web/package-lock.json`, `web/README.md`, `docs/personal-dashboard.md`.

- [ ] Reproduce unchanged current source under managed project default 26. Expected: deployment build fails specifically because the adapter rejects Node 26; existing healthy production remains.
- [ ] Add the supported engine range to package and lockfile root; document Node 22/24 setup. Do not add a test that only repeats the JSON value.
- [ ] Deploy the corrected source to the same project still defaulting to 26. Expected: real build chooses Node 24 and production succeeds; owner/source/isolation checks pass and private environment bytes remain unchanged.
- [ ] Restore the saved project setting to 24 and read it back.
- [ ] Run complete web and Python/MCP suites, Svelte check and build. Expected: no failures; retain inherited warnings separately.
- [ ] Obtain a fresh whole-diff review, address material findings, then commit and verify source publication/readback as authorized.

## Review Focus

- Node 22 CI must still install; Node 24 must remain supported.
- New default 26 must not be selected after the fix.
- The lockfile must not introduce dependency churn.
- A failed probe must preserve healthy production and restore the project setting.
- No credentials, environment, deployment binding or private test evidence may enter Git.
