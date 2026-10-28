# Fulcra per-user deployment and release metadata

Ash's actual native answer says: “this is meant to be built on fulcra as the backend / communication layer,  and deployable by any user via the fulcra build and deploy a webapp skill. figure it out.” Ash also answered “Sure that sounds good” to the displayed Fulcra Dynamics / Apache 2.0 recommendation. These are real owner decisions; preserve their original request/revision/answer evidence privately.

Keep the existing Svelte template sign-in, native Fulcra annotation backend and Fulcra deployment route. The core dashboard needs no shared issuer rollout, separately registered OAuth client, external GCS bucket or personal Vercel account. The optional issuer adapter remains disabled and separately scoped; no shared service changes are authorized here.

## Approach

Fulcra's current build-and-deploy skill creates/reuses the user's own harness annotation, product annotation and deployment project. Add a small configuration command which verifies those resources through the current CLI login and writes private server configuration. It performs no resource creation or deployment itself, so interrupted creation remains in the skill's existing workflow. Reuse the template defaults. Keep a private account/resource-bound setup journal outside source, generate the server signing key once, and never print it. Repeated setup preserves the key; changed account/resources, foreign/shared annotations, unsafe files or conflicting environment content fail without overwriting anything.

A fully automatic resource creator would duplicate the Fulcra skill and add uncertain-create recovery. Documentation alone leaves manual secret/config mistakes unprotected. The focused verifier/configuration command makes the existing workflow repeatable with a small change.

## Acceptance

- Derive owner from authenticated Fulcra user-info; verify exact owned deploy project and two distinct owned moment annotations.
- Write server-only owner/product/key settings and the template's existing public sign-in defaults to a private environment file. Reuse the actual returned origin for native MCP.
- Preserve private state, signing key and existing environment content on retry/failure/account switch; no private bindings or credentials enter exports/source.
- Document a complete agent-driven Fulcra skill setup and deployment flow usable from a clean fork. Gatekeeper remains the selected actual second-account acceptance target; its sign-in is separate evidence.
- Apply Fulcra Dynamics publisher and Apache-2.0 source license to canonical metadata and generated packages; preserve applicable upstream notices.
- Evaluate configuration/access/failure behavior, full existing tests, exports, source publication/readback and live existing-owner preflight. Do not infer a second-account deployment, remote ChatGPT OAuth, public publisher verification or marketplace acceptance.
