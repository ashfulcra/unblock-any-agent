# Local entrypoints final review

Date: 2026-10-16. Independent reviewer: delegated `review_entrypoints` agent.

Disposition: **No actionable findings in the reviewed local slice.** This is one final review of the newly added entrypoints, not a re-review of the prior local-loop fixes. It is not production, host-installation, or marketplace acceptance.

## Scope and requirements

Baseline: `2f984f9`. Reviewed the uncommitted `unblock/mcp_bridge.py`, `requirements-mcp.txt`, `scripts/run_mcp.py`, `scripts/build_plugins.py`, `skills/unblock/SKILL.md`, `skills/unblock/references/setup.md`, `tests/test_mcp.py`, `tests/test_packages.py`, and `docs/superpowers/plans/2026-10-16-local-plugin-entrypoints.md`.

Read repository `AGENTS.md`, the requirements record, first-release specification, marketplace release plan, and local proof instructions. Read the existing client, HTTP service, store access checks, CLI, listener, and Claude adapter as dependencies of the new entrypoints. Existing behavior outside the new slice was context, not a separate comprehensive audit.

Focus: credential-derived agent/workspace identity; denial of neighbor and foreign-workspace access; tool inputs and routing; credential exposure; contained, regular-file exports; copied runtime usability; and accurate boundaries around native hosts, wake behavior, public distribution, naming, and licensing.

## Verification performed

Ran `.venv/bin/python -m unittest discover -s tests -v` independently. Result: **41 tests passed**, zero skips or failures, in 16.889 seconds. This included real SDK stdio discovery, help creation, replacement-process recovery, authenticated progress, revocation, malformed request identifiers, neighbor isolation, both copied MCP runtimes outside the checkout, export inspection, and the existing local loop regression suite.

Also ran a disposable, in-memory-controlled review scenario using temporary SQLite state, synthetic owner/agent/listener credentials, a loopback server on an ephemeral port, and a real MCP SDK stdio client. All assertions passed:

- Owner and listener credentials each fail bridge startup with the sanitized `agent_setup_required` error; no synthetic credential appears in captured output.
- For a neighboring agent in the same workspace and an agent in a different workspace, all five operations (`get_work`, `revise_need`, `begin_action`, `record_progress`, `reconcile_action`) return errors. The private need is absent from tool errors and remains unchanged in storage: ten denials total.
- The authorized agent's recovery returns an empty successful result when only foreign work exists.
- Stopping the loopback service during an established MCP session makes recovery return `source_unavailable_work_remains_pending`, rather than a successful empty queue.
- Both exports build in a temporary directory; the copied runtime is present. Temporary state and exported artifacts were removed by their context managers.

Read the installed MCP SDK's tool error handling and the local `uv` command help. Did not substitute a model-backed run for local verification.

## Review conclusions

The bridge obtains identity from one private absolute config and checks its authenticated role before exposing tools. Its public tools provide no enrollment, arbitrary endpoint, shell, listener-route, or sender-selection parameter. Request identifiers are parsed and canonicalized as UUIDs before entering URL paths. Write operations continue through the service's existing authenticated access checks, and revocation remains enforced by that service after bridge startup.

The exporter copies explicit regular-file allowlists and rejects symlinked/escaping source files. Its exports contain the runtime, web assets, shared skill, setup reference, MCP launcher and dependency declaration; runtime bindings and operational state are not part of the copied tree. The package's declared prerequisites include a separately running loopback service and an enrolled private config. Setup deliberately directs initial service/enrollment provisioning to the canonical checkout. This is not an offline or independently authenticated hosted product.

The skill and generated README preserve pending obligations and action uncertainty, distinguish receipt from observed continuation, and require an explicit listener route. They accurately describe these as local development exports. They do not claim ChatGPT web connectivity, persistent wake installation, remote OAuth, marketplace eligibility, a selected public license, a bare slash-command reservation, or successful native host loading.

## Remaining evidence and declined scope

The tests launch copied MCP scripts with the already prepared Python interpreter. They do **not** establish that either host expands its plugin-root variable, inherits `UNBLOCK_AGENT_CONFIG`, locates `uv`, or starts the exact generated manifest command in a fresh installation. The manifest's `uv --with mcp==2.3.0` dependency acquisition was not run against a clean cache or an external package index in this review. These are remaining integration checks, not acceptance claims supported by this report.

Did not invoke native models, install/configure hosts, inspect unrelated credentials or private operational state, publish to any network destination, contact V5, change permissions, or modify implementation. Did not verify live marketplace schemas/policies or re-run native strict host validation. Did not certify OAuth, production security, remote MCP/Events, actual ChatGPT/Claude plugin discovery or pickup, licensing decisions, clean-account deployment, or public distribution. Those remain separate prerequisites already identified by the package and project plan.

No corrective implementation or regression request is raised because this review found no demonstrated defect. The extra denial and disconnection cases above would be useful durable coverage when the adapter is extended, but their absence did not conceal a failure in the independently executed scenarios.
