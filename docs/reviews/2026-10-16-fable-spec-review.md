<!-- Historical independent review; platform assertions are reviewer findings, not accepted implementation decisions. -->

Tycho supplied this report after launching a fresh subagent with the `fable` model override. The reviewer self-reported Claude Fable 5.1; the served model was not independently verified. The original report was retrieved and its full SHA-256 verified: `09eaa5c584f42c50569b637b5ef29d4aad3abd4bee692553ea3e0a45ccf305cf`.

Maintainer disposition: review received; **revise first** retained as the reviewer verdict. Findings require technical validation before incorporation. No naming, architecture, release-scope, or user-preference change is approved by this review. In particular, F7's proposed write-ahead intent is a candidate contract, not a requirement to adopt legacy machinery; F15's deterministic identity is one possible retry design, not the only solution.

Follow-up tasks for the specification revision:

- F1/F2: verify independent execution and credential custody, and select the OAuth authorization-server path. Prerequisite: supported runtime and authorization capabilities demonstrated; unblock action: document and test the selected contracts.
- F3/F4: define enforced agent identity and the future second-human response write path. Prerequisite: explicit application trust/storage model; unblock action: specify attribution, membership and revocation behavior.
- F5/D1: validate package-name guidance and portal availability while preserving the requested `/unblock` goal. Any permanent naming change remains a proposal.
- F6/F8/F13/F14: verify delivery and continuity behavior for each supported host and narrow public claims to observed capabilities.
- F7/F9/F10/F15: specify and test interrupted actions, immutable revision references, source freshness and retry/replacement behavior without prematurely prescribing architecture.
- F11/F12: verify dated listing requirements and complete fork/deployment guidance.
- D2–D7: retain proposed defaults and scope decisions as open; do not treat reviewer recommendations as user approval.

---

# Independent specification review: Unblock first-release spec

## 1. Header

- Reviewer model: **Claude Fable 5.1** (model id `claude-fable-5-1`), as reported to me by my runtime environment. I cannot independently verify my own served model beyond that statement.
- Snapshot commit reviewed: `102e3ce97649e6f9db7e7e24bd9344ee952915ab` (planned `ashfulcra/unblock-any-agent`, not published).
- Bundle SHA256: `40313c5c605e002b4185f609a0434212b3253635aa597a44755ed01dd3d9de64` (recomputed locally; matches the requested digest).
- Primary target: `docs/superpowers/specs/2026-10-16-unblock-first-release.md` (SHA-256 `866a6c3f…`). Supporting: `docs/requirements.md`, `docs/current-platform-assessment.md`, `docs/marketplace-release-plan.md`, `docs/superpowers/specs/2026-10-16-unblock-any-agent-design.md`, `README.md`.
- Date: 2026-10-16.
- Scope discipline: review only. Nothing was published, messaged, or written outside this file and a scratch download directory.

## 2. Verdict

**Revise first.**

The spec is close: the release outcome, the six operations, the information contracts, and the acceptance cases are the right shape, and it correctly refuses to inherit Coord machinery. But two things it relies on are not yet shown to exist on the chosen platform-first architecture, and both decide the architecture rather than a detail of it. First, every verified host mechanism for "monitoring that runs independently of the originating session" is session-bound (Claude mods, `/loop`, monitors, channels) or model-invoking in the cloud (Routines), and the web-app template holds credentials only in per-browser cookies, so the spec's required independent detector has no named runtime or credential custody. Second, the ChatGPT entry point is a remote MCP server that must authenticate end users with OAuth 2.1 (PKCE, CIMD/DCR, audience-bound tokens, no machine-to-machine grants) and must ship in the first OpenAI ZIP, yet no authorization-server component appears in the architecture. Add to that an agent-identity model that, as written, violates the spec's own rule against trusting model-supplied sender labels, and the first-release boundary is not yet safe to plan from. None of these require a legacy bus or replay engine; each needs one explicit decision in the spec.

## 3. Findings

### P0

**F1 — No viable independent detector route or credential custody is identified.**
File/section: first-release spec, "Continuity and detection"; acceptance case 3.
Problem: The spec requires that "Unattended monitoring requires a configured route that actually runs independently of the originating session" and that the plan "must include at least one supported independent monitoring route for the public release and keep model invocation out of quiet checks where possible." Verified host facts contradict every route the supporting docs name: Claude mod timers, `/loop`, cron tasks and monitors "only fire while Claude Code is running" (scheduled-tasks doc); channels require a live session; ChatGPT hooks are "not supported in cloud-orchestrated ChatGPT Work"; cloud Routines run without a session but invoke the model every run. The deployed web app cannot run a quiet check either: the template stores the Fulcra token "in HTTP-only cookies" and proxies "server-to-server" with that cookie, so with no browser session open the server holds no credential.
Consequence: Acceptance case 3 ("original session is unavailable… enabled independent monitor notices it") and R3 are unachievable as architected. Shipping without it violates the spec's own "do not advertise background detection."
Evidence: spec §Continuity and detection; https://code.claude.com/docs/en/scheduled-tasks ("Tasks only fire while Claude Code is running and idle"; comparison table: Cloud routines "Requires open session: No", runs model); https://code.claude.com/docs/en/channels ("Events only arrive while the session is open"); https://learn.chatgpt.com/docs/plugins; app template README (device flow, HTTP-only cookies).
Fix: Name the detector's runtime and credential model in the spec, not the plan: (a) a server-side scheduled check in the deployed app holding a scoped long-lived Fulcra credential (refresh-token/device grant) in server secrets, or (b) a Desktop scheduled task on the owner's machine, or (c) a cloud Routine with a documented model cost. State which one the first release ships, what credential it holds, where it lives, and how revocation works. Add the credential-custody check to the "two integration contracts" list (it becomes three).

**F2 — Remote MCP end-user authentication has no named authorization server; the ChatGPT entry point depends on it from the first ZIP.**
File/section: first-release spec, "Architecture decision" and "Distribution and personal dashboards".
Problem: The spec promises "web and remote MCP interfaces" and an OpenAI package that "includes the intended remote MCP capability from its first submission." OpenAI requires the MCP server to implement OAuth 2.1 with PKCE (S256), publish protected-resource metadata, support CIMD or DCR or a predefined client, bind `resource` audience, fully validate every token, and explicitly does not support client-credentials grants. The Claude directory additionally requires the server be submitted separately as an MCP connector. The spec names Fulcra "identity" as the base but does not say whether Fulcra's Auth0 tenant will issue tokens whose audience is this product's server, or whether the product runs its own authorization server fronting Fulcra device-flow tokens. "MCP credentials resolve to the intended human/account" is listed as a contract to demonstrate, but the OpenAI submission flow runs connection and domain-verification checks on the live server, so this cannot be discovered late.
Consequence: R6 and acceptance case 4 (start/answer via ChatGPT) cannot be delivered; the OpenAI package cannot pass automated checks; "Adding an MCP server to an existing skills-only plugin is not currently supported," so a skills-only first submission forecloses the fix.
Evidence: https://developers.openai.com/plugins/build/auth ("you are expected to implement an OAuth 2.1 flow that conforms to the MCP authorization spec"; "ChatGPT does not support machine-to-machine OAuth grants"); https://developers.openai.com/plugins/deploy/submission ("Include any MCP server in the initial ZIP"; "only one MCP server can be connected per plugin"); https://claude.com/docs/plugins/submit (connector submitted separately).
Fix: Add an "Authorization" paragraph to the architecture decision naming the authorization server (Fulcra Auth0 tenant with a registered resource for this product, or product-owned AS), the token audience, and the mapping from token to Fulcra account and team. Make "OAuth 2.1 discovery + PKCE + audience check passes against ChatGPT and Claude connector clients" an explicit pre-build contract. Verify with Fulcra (the live `mcp__Fulcra__*` connector in this session is evidence Fulcra already runs an OAuth-fronted remote MCP; whether a third-party product server can share that tenant is unverified).

### P1

**F3 — Agent identity is unverifiable under the single-account credential model, contradicting the spec's own rule.**
File/section: "Minimal shared information" (Agent, Response rows); "Common operations".
Problem: The spec says "Never rely on a sender label supplied by the model as authentication" and requires `report_progress`/`save_context` to be attributable to a "Stable product identity" per agent. But every agent on the owner's account that calls Fulcra directly (skills entry point, mod `$.http`/`$.mcp`) authenticates as the same Fulcra user. The only thing distinguishing agent A from agent B is the name the model writes, which is exactly the label the spec forbids trusting. The spec does not define per-agent credentials or how an agent identity is issued and bound.
Consequence: Attribution in "Continuation result" and "Response" rows is forgeable by any agent (or prompt injection) on the account; `get_attention` "caller's permitted requests" cannot scope per agent; replacement-session identity ("A replacement session does not become a different agent by default") has no enforcement.
Evidence: spec text quoted above; Fulcra MCP `record_data` and `write_file` take no actor parameter (tools.py); app template proxies with the signed-in user's token.
Fix: Decide and state the agent identity binding: app-issued per-agent credentials (an agent key or scoped token minted by the product, carried in the MCP/HTTP call), or accept account-level attribution for the first release and say so explicitly in the Response/Continuation contracts ("responder = authenticated account; agent name is a claim"). Either is acceptable; silence is not.

**F4 — A second human cannot write into the owner's request store with platform primitives; the "join later" promise has no write path.**
File/section: "Release outcome"; acceptance case 7; "Minimal shared information" (Response).
Problem: Fulcra shares are read-only: "Recipients read them … they can never write here." The web app proxies each signed-in user's own token to the Fulcra API. So human B's `answer_request` lands in B's account, not in the owner's, and the owner's agent must read it from a share B creates back. The spec reserves team/human separation "so additional humans can join later" but never says where a non-owner's response lives or who reads it. That choice changes the Response contract (request and response in different accounts), `get_attention` fan-in, and revocation semantics ("Revoked membership prevents new actions").
Consequence: Acceptance case 7 is specified as an "integration test" with no feasible design; the single-human data model may have to be reworked when the second human arrives, which is what R11 asked to avoid.
Evidence: fulcra-context-mcp `create_share` docstring (read-only; "each agent writes to its own account and reads the other's"); app template README.
Fix: State the chosen pattern in the spec: (a) resolver writes to own account and shares read-only to the team (request/response may live in different accounts; agent folds across shares), or (b) an application service owns request/response state under app auth (then the "no local database" sentence needs qualifying), or (c) a team-owned Fulcra account. Pick one for the first release even if only one human uses it.

**F5 — `unblock` as the immutable package identifier is likely to be held or discouraged on both directories; the spec treats the hold risk as a later concern.**
File/section: "Human and agent experience" ("Keep the proposed public plugin identifier `unblock` …").
Problem: Claude's checklist holds "a name made only of generic words" for a reviewer; OpenAI's guidelines say "Avoid overly generic names, especially single-word dictionary terms that aren't explicitly tied to your brand." Claude: "Never change a published plugin's name. After a rename, users who already installed it lose the plugin." OpenAI: `plugin_name_mismatch` on update. So the identifier chosen for the first submission is permanent.
Consequence: A hold is not a rejection, but a rename after publication strands installs; a first submission under a name that is later refused delays R15/R16 by a full review cycle.
Evidence: https://claude.com/docs/plugins/pre-submission-checklist ("Held for a reviewer for a name made only of generic words"); https://developers.openai.com/plugins/plugin-guidelines; https://code.claude.com/docs/en/plugins/publish ("Never change a published plugin's name").
Fix: Separate the three names explicitly in the spec: immutable package identifier (recommend `unblock-any-agent`, brand-tied, low hold risk), skill name `unblock` (`/unblock-any-agent:unblock` on Claude, `@`-mention on ChatGPT), and the mod command `/unblock`. Run portal **Validate** on both directories as the first marketplace deliverable and record the outcome. See open decision D1.

**F6 — The "Claude live delivery" premise is overstated: channels are allowlist-gated and session-bound; mods are session-bound.**
File/section: current-platform-assessment "Claude live delivery" row; spec "Continuity and detection" ("Automatic delivery… require their own observed acceptance").
Problem: The assessment says "Current channels documentation supports events into running sessions" and the spec leans on "verified host lifecycle mechanisms." Verified: channels are a research preview; `--channels` "only accepts plugins from an Anthropic-maintained allowlist, or from your organization's allowlist"; a third-party plugin needs `--dangerously-load-development-channels`. Mods run in Claude Code CLI/Desktop Code tab/VS Code only, never in claude.ai chat or Cowork; `$.prompt.submit` and `$.clock.every` work only inside the open session.
Consequence: For a public plugin, the only delivery into a running Claude Code session is a mod polling timer (`$.clock.every` → `$.prompt.submit`), which is correct but is polling, not push; there is no delivery at all into chat/Cowork. The spec's claim "Keep Claude-specific mod capabilities in the Claude export" is fine; the assessment's premise should be corrected so the plan does not budget a channel.
Evidence: https://code.claude.com/docs/en/channels ("During the preview, --channels only accepts plugins from an Anthropic-maintained allowlist"); https://code.claude.com/docs/en/plugins/mods/overview ("Mods work in the Claude Code CLI, the Code tab of the Claude Desktop app, and the VS Code extension"); https://code.claude.com/docs/en/plugins/mods/api.
Fix: In the spec, name the first Claude delivery route as "mod poll timer with `$.prompt.submit`, Claude Code only; manual Continue elsewhere" and strike channels from the first release. Keep "busy-session handling" as its own acceptance item (`$.prompt.submit` "waits until the session is idle").

**F7 — Recovery of uncertain external actions needs a write-ahead intent, not only a post-hoc continuation result.**
File/section: "Common operations" (`report_progress`, "Repeated delivery or repeated resume must not repeat an external action without checking its result"); acceptance case 6.
Problem: The Continuation result records "what the agent did next" after the fact. If the session dies between performing an action and recording it, a successor has nothing to check against: for actions without a natural query (sending a message, triggering a deploy, posting a comment) "checking the actual result" is impossible unless the intent and an idempotency key were persisted before execution. `record_data` with a client `record_id` and the workspace-agent `Idempotency-Key` both exist, but only help if the key was chosen before the first attempt.
Consequence: Acceptance case 6 passes only for actions that happen to be queryable; duplicated consequential actions remain possible.
Evidence: spec text; fulcra-context-mcp `record_data` ("a record sent again with the same id is stored as the same record"); https://developers.openai.com/workspace-agents/trigger-runs (Idempotency-Key).
Fix: Add to `report_progress` (or a small `declare_action`) a required pre-step: persist `{work_context, action, idempotency_key, declared_at}` before the external call; `resume_work` must surface declared-but-unconfirmed actions as "check before repeat" and refuse to recommend re-execution without a result check. This is a contract line, not machinery.

**F8 — The Claude export's contents for claude.ai chat and Cowork are unspecified; without the remote MCP connector those surfaces have no path to the product.**
File/section: "Distribution and personal dashboards"; acceptance case 4.
Problem: On claude.ai chat, hooks and mods are ignored, `bin/` is refused, commands "load as a skill; Claude applies it when it fits," and a remote MCP server is "Listed on the plugin's Connectors tab; works once you add or connect it there." A skills-only Claude plugin in chat therefore cannot read or write a request. The spec says to keep mods in the Claude export but does not say the Claude export includes the remote MCP server, nor that the connector must be submitted separately (the marketplace plan does).
Consequence: Acceptance case 4 ("start through each of web, Claude, ChatGPT, and skills") is only true for Claude Code unless the Claude plugin bundles the connector; the directory listing would advertise chat/Cowork support it cannot deliver.
Evidence: https://claude.com/docs/plugins/platform-support (component table); https://claude.com/docs/plugins/submit ("If the plugin references a remote MCP server you run, submit that server as an MCP connector too").
Fix: State that the Claude export = skills + mod + the same remote MCP server, and that connector submission is part of the first Claude release; or scope acceptance case 4's Claude leg to Claude Code and say so in the listing.

### P2

**F9 — "Request/context version shown to the responder" needs a server-assigned version identity.**
File/section: "Minimal shared information" (Response row); acceptance case 5.
Problem: Fulcra records are append-only with no update; files get "a new version" on write but no conditional write; neither exposes compare-and-swap. A version token derived from client clocks cannot detect a stale browser view. The spec leaves the type choice open (good) but should require the version to be a server-assigned identity (file `version_id`, or the record id of the latest request revision).
Evidence: tools.py `write_file` ("Writing to an existing path creates a new version"); `record_data` (no update); https://docs.fulcradynamics.com/fulcra-platform/ ("Files are versioned"; no CAS documented).
Fix: Add one sentence: request revisions are immutable records or file versions; a response names the server-assigned revision id it answered; a response naming a superseded revision is retained and flagged, never applied.

**F10 — The detector's "checked-and-quiet" state cannot be inferred from an empty `get_data_updates` answer.**
File/section: "Continuity and detection"; "Common operations" (`get_attention` "Distinguish unavailable sources from checked-and-quiet sources").
Problem: Repo-recorded measurement (fulcra-tools `AGENTS.md`, 2026-10-02, raw HTTP) shows `data-updates` intermittently returning HTTP 200 with an empty `file_changes` on a range that otherwise returns thousands of changes, and HTTP 500 on wider windows. An empty answer is shape-indistinguishable from quiet. The MCP docstring also notes the range filters on processing time, not record time.
Evidence: fulcra-tools `AGENTS.md` (`data-updates` paragraph); tools.py `get_data_updates` docstring. This is a private measurement, not public documentation; treat as a test case to reproduce, not a fact about the current API.
Fix: Require the detector to corroborate an empty update window against a direct read of the watched requests before reporting "quiet," and to report "unverified" otherwise. Reproduce the measurement during slice 1.

**F11 — Listing requirements the spec/plan do not yet enumerate.**
File/section: "Distribution and personal dashboards" ("Audit publisher access, name validation, … supported package fields").
Problem: Verified concrete requirements not named anywhere in the bundle: OpenAI individual/business verification; `displayName` ≤30 chars and `shortDescription` ≤30; five positive and three negative test cases, a video walkthrough URL, reviewer credentials, release notes; HTTPS `websiteURL`/`supportURL`/`privacyPolicyURL`/`termsOfServiceURL`; "Trial or demo plugins will not be accepted"; public URLs must identify the same publisher. Claude: README ≥40 words, LICENSE or `license` field, listing fields (`icon`, `documentationUrl`, `supportUrl`, `privacyPolicyUrl`, `termsOfServiceUrl`) in `plugin.json`, data-handling questionnaire, repository public before publish, one submission per repo+folder, 10 submissions/24h, 256 KiB per non-image file and ≤512 files or a reviewer hold, paid claude.ai plan to submit.
Evidence: https://developers.openai.com/plugins/deploy/submission; https://claude.com/docs/plugins/pre-submission-checklist; https://code.claude.com/docs/en/plugins/manifest-reference#directory-listing-fields.
Fix: Fold these into the release checks as dated line items; add privacy policy and ToS pages to the web app deliverable (both directories need them).

**F12 — Fork-and-deploy: forks of a public repo are necessarily public; the deploy path needs a terminal; dashboard names collide globally.**
File/section: "Distribution and personal dashboards" ("fork the canonical repository … deploy at the returned Fulcra address").
Problem: GitHub: "Public repository forks are public … You cannot change the visibility of a fork by itself." So the fork must contain zero personal configuration (the template's env-var model supports this; say so). The deploy flow uses `uvx fulcra-api auth print-access-token` and `npx vercel deploy`, i.e. a terminal or an agent, not a click-through. Deploy project names are global DNS labels; `409` means "the name is taken, possibly by another user." The design's example `project.my.fulcra.ai` suffix is not documented; the spec's "returned Fulcra address" wording is correct. Stars on a fork accrue to the fork (inference: a fork is its own repository; GitHub's stars page does not address forks), so the spec's canonical-link mitigation is right but should also set `repository`/`homepage` in both manifests to the canonical repo.
Evidence: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks; https://github.com/fulcradynamics/agent-skills/blob/main/skills/build-and-deploy-a-web-app/references/deploy.md; https://docs.github.com/en/get-started/exploring-projects-on-github/saving-repositories-with-stars (no fork statement).
Fix: State "forks are public; all personal configuration is deployment environment, never committed"; offer "Use this template" as the private alternative (loses fork lineage, see D4); require the visitor to choose the dashboard name; keep the suffix unstated.

**F13 — Continuity capture is instruction-driven on three of the four surfaces; acceptance case 2 should be run off Claude Code.**
File/section: "Continuity and detection" ("through verified host lifecycle mechanisms where available").
Problem: Only Claude Code has lifecycle hooks a plugin can use (`session.compact`, `session.end`, PreCompact settings hooks). claude.ai chat ignores hooks; Cowork runs hooks but not mods; ChatGPT cloud Work has no plugin hooks. Elsewhere, capture happens only because the `unblock` skill tells the model to call `save_context`. The spec acknowledges "where available" but the acceptance case does not force the weaker path to be tested.
Evidence: https://claude.com/docs/plugins/platform-support; https://code.claude.com/docs/en/plugins/mods/reference (Session events); https://learn.chatgpt.com/docs/plugins.
Fix: Run acceptance case 2 at least once from a surface with no lifecycle hooks (ChatGPT or claude.ai chat) and record it; state in the spec that mechanism-driven capture is a Claude Code bonus, not the baseline.

**F14 — The ChatGPT workspace-agent trigger cannot return the agent's response.**
File/section: current-platform-assessment "ChatGPT interaction and continuation" row; spec acceptance cases 1 and 3.
Problem: "The agent's response cannot currently be retrieved through the API." So a trigger-based wake proves dispatch, never continuation; "observed next action" evidence must come from the agent calling `report_progress` over MCP.
Evidence: https://developers.openai.com/workspace-agents/trigger-runs.
Fix: One sentence in the spec: a trigger run status is delivery evidence only; continuation evidence always arrives via `report_progress`.

**F15 — `request_help` retry-safety needs a deterministic request identity that survives session replacement.**
File/section: "Common operations" (`request_help`: "A retry must not create a second logical request").
Problem: `record_data`'s `record_id` dedupes only when the retry carries the id from the first attempt; a replacement session that never saw the first attempt will mint a new id. The spec's "stable identifier" should be derived from (work context, blocker condition revision) so any session re-raising the same need converges on the same request.
Evidence: tools.py `record_data` docstring.
Fix: Specify the derivation (or an application-side lookup-before-create under the same key) and add "re-raise from a fresh session does not duplicate" to acceptance case 2 or 3.

## 4. Open product decisions

**D1 — Immutable package identifier.** Options: (a) `unblock` on both directories, accept a likely reviewer hold and no fallback once published; (b) `unblock-any-agent` as the permanent identifier, `unblock` as the skill and `/unblock` as the Claude Code mod command. Recommendation: (b). The user's goal ("fast towards `/unblock`") is met by the command and skill names; the identifier is the one thing that cannot be changed later, and the brand-tied form is what both directories ask for.

**D2 — Uncertain-stall default (agent-first).** My view: agent-first is the right default, with three conditions the spec should make explicit. (1) The investigation is visible to the human immediately in "Checking" even though no notification fires, so nothing is hidden, only quieted. (2) Agent-first is bounded: a declared escalation deadline (and an attempt cap) after which the item moves to Needs you as "investigation unresolved," not silently parked. (3) The agent query is a model invocation and therefore has a cost and a reachability precondition; when no verified route to the agent exists, skip straight to Needs you with "agent unreachable" rather than queueing a question nobody will read. Note also that "declared expected update overdue" is a strong signal precisely because the agent committed to it; the agent-first ask is reasonable there and less so for weaker heuristics. Options: agent-first-bounded (recommended), human-first, or per-request urgency policy. Recommendation: agent-first-bounded as the shipped default, with the deadline a per-team setting.

**D3 — Where a non-owner human's response lives (F4).** Options: resolver's own account + read-only share; application-owned store; team account. Recommendation: decide now; if the owner wants the "no local database" stance to hold, choose resolver-own-account-plus-share and design `get_attention` to fold across shares from the start.

**D4 — Fork vs template for personal dashboards (F12).** Options: fork (public, lineage and "forked from" link preserved, no private fork possible); "Use this template" (can be private, no lineage, no fork count). Recommendation: offer fork as the default for the star/discovery goal, template as the documented private alternative.

**D5 — Independent monitor host (F1).** Options: server-side quiet check in the deployed app with a stored scoped credential; Desktop scheduled task on the owner's machine; cloud Routine (model cost per check). Recommendation: server-side quiet check if Fulcra can issue a long-lived scoped credential to the app and the deploy target supports scheduled execution (both unverified); otherwise Desktop scheduled task for the first release with Routines as the cloud option.

**D6 — Claude export scope for the first release (F8).** Options: skills + mod + remote MCP connector (full chat/Cowork/Code support, two submissions); skills + mod only (Claude Code useful, chat/Cowork listing partial). Recommendation: include the connector; it is the same server the OpenAI package requires anyway.

**D7 — Release gating order.** Whether the first public release waits on both directories or ships Claude first. Not a correctness question; flagging because the OpenAI auth work (F2) is the longest pole.

## 5. Requirements coverage

| Req | Coverage | Where in first-release spec | Note |
| --- | --- | --- | --- |
| R1 Agents needing the user are priority zero | Covered | "Human and agent experience" (Needs you first) | |
| R2 Human / own-agent / other-person's-agent in one system | Partially | "Release outcome" (basic scoped help from an existing authorized connection); acceptance case 9 | Other person's agent explicitly later; request model is shared. Acceptable deferral, stated. |
| R3 Explicit requests and detection in v1 | Partially | "Continuity and detection" | Detector specified; independent route unresolved (F1). |
| R4 Web app entry point | Covered | "Release outcome", acceptance 4 | |
| R5 Claude plugin entry point | Partially | "Human and agent experience", "Distribution" | chat/Cowork path unspecified (F8). |
| R6 ChatGPT plugin entry point | Partially | same | Auth server unnamed (F2). |
| R7 Skill repository entry point | Partially | same | Bare-skill auth/identity path unspecified (F3). |
| R8 Stars on the skill repo | Covered | "Distribution" (source and star links to canonical repo) | Thin; add manifest `repository`/`homepage` (F12). |
| R9 Fork instructions for personal dashboard | Covered | "Distribution and personal dashboards"; acceptance 10 | Public-fork caveat missing (F12). |
| R10 Record distribution requirements now | Covered | whole doc + marketplace plan | |
| R11 Plan for multiple humans | Partially | "Release outcome"; acceptance 7 | Write path undefined (F4). |
| R12 Supersede existing tooling; V5 not a dependency | Covered | "Release outcome" ("no inherited Coord architecture constraints") | |
| R13 No legacy constraints | Covered | "Architecture decision" | Honoured throughout; no finding here requires legacy machinery. |
| R14 Continuity in the plan | Covered | "Continuity and detection"; acceptance 2, 8 | Surface asymmetry to state (F13). |
| R15 Official marketplaces, package/naming/review rules | Partially | "Distribution"; marketplace plan | Several concrete requirements missing (F11); connector submission (F8). |
| R16 Short identity `unblock` / `/unblock`, namespace competition | Partially | "Human and agent experience" | Hold risk on both directories (F5, D1). |

Deferred explicitly and acceptably: full multi-human administration, quorum approvals, agent-universe map, legacy imports, universal scheduler.

## 6. Platform claims checked

| Claim (from bundle) | Result |
| --- | --- |
| Claude plugin commands/skills invoke as `/plugin-name:command`; skills as `/plugin:skill` | VERIFIED — https://code.claude.com/docs/en/plugins/manifest-reference#commands ; https://code.claude.com/docs/en/plugins/components |
| Mod API registers a bare `/unblock` via `$.command.register`; throws on a taken name; cannot overwrite | VERIFIED — https://code.claude.com/docs/en/plugins/mods/api ("`$.command.register` throws for a taken name") |
| Mods run only in Claude Code CLI / Desktop Code tab / VS Code (not chat, Cowork) | VERIFIED — https://code.claude.com/docs/en/plugins/mods/overview |
| Mod lifecycle: `session.start/end/compact`, `$.store` machine-shared, `$.prompt.submit`, `$.session.send`, `$.clock.every` | VERIFIED — https://code.claude.com/docs/en/plugins/mods/reference ; mods/api |
| Anthropic directory accepts GitHub-backed plugin submissions (portal, optional subdirectory, tracked branch/tag); `claude-plugins-official` needs a partner contact, not the portal | VERIFIED — https://code.claude.com/docs/en/plugins/publish ; https://claude.com/docs/plugins/submit |
| `clau.de/plugin-directory-submission` redirects to directory publishing docs | VERIFIED — HTTP 302 → https://claude.com/docs/directory/publish |
| Directory reaches claude.ai, Cowork, and Claude Code (synced) | VERIFIED — https://code.claude.com/docs/en/plugins/publish |
| Remote MCP server referenced by a Claude plugin must also be submitted as a connector | VERIFIED — https://claude.com/docs/plugins/submit |
| Claude portal checks names against other organizations; generic/confusing names held for review; name permanent | VERIFIED — https://claude.com/docs/plugins/pre-submission-checklist ; publish page |
| Claude component support varies by surface (hooks ignored in chat, `bin/` refused, remote MCP via Connectors tab) | VERIFIED — https://claude.com/docs/plugins/platform-support |
| Claude channels push events into a running session; require live session | VERIFIED — https://code.claude.com/docs/en/channels ; plus allowlist restriction the bundle omits |
| Claude manifest required fields / `./` path rules / `.claude-plugin/plugin.json` | VERIFIED — manifest reference (`name` only required key; listing URL fields) |
| `claude-plugins-official` at `ea10b213…` has 315 entries, none named `unblock` | VERIFIED — raw marketplace.json at that commit: 315 plugins, 0 matches |
| OpenAI public plugin: no lifecycle hooks, no `apps`/`.app.json`; MCP must be in initial ZIP; adding MCP to skills-only later unsupported | VERIFIED — https://developers.openai.com/plugins/deploy/submission ; https://developers.openai.com/plugins/build/plugins |
| OpenAI package layout: root `plugin.json`, `skills/`, `mcp.json`, `extensions.com.openai`; semver | VERIFIED — build/plugins ; submission-errors (`plugin_version_not_semver`) |
| OpenAI name rules (≤64, lowercase/hyphen) and generic-name guidance | VERIFIED — submission ; https://developers.openai.com/plugins/plugin-guidelines |
| OpenAI end-user auth via OAuth 2.1/PKCE, server-side checks, no M2M | VERIFIED — https://developers.openai.com/plugins/build/auth |
| ChatGPT invocation: `@` to invoke plugin/skill; no global slash on web; `/plugins` in Codex CLI | VERIFIED — https://learn.chatgpt.com/docs/plugins |
| ChatGPT lifecycle hooks unsupported in cloud-orchestrated Work; synced Work admin MCP hooks only | VERIFIED — https://learn.chatgpt.com/docs/plugins |
| OpenAI UI extensions: sidebar/thread/file entry points; `ui/message` to active or new conversation on desktop and Work web | VERIFIED — https://developers.openai.com/plugins/build/extensions ; https://github.com/openai/mcp-extensions/blob/main/docs/spec.md |
| Workspace-agent triggers: conversation keys, Idempotency-Key, statuses; cannot reach arbitrary chats | VERIFIED (first three) — https://developers.openai.com/workspace-agents/trigger-runs ; "arbitrary chats" NOT stated either way in docs; response not retrievable via API (verified) |
| Fulcra deploy: create/reuse project, returns `id` and `domain`; 409 on taken name | VERIFIED — agent-skills deploy.md ; `my.fulcra.ai` suffix NOT verified (doc does not state it) |
| Fulcra app template: device-flow sign-in, HTTP-only cookies, server-side API proxying | VERIFIED — app-template-svelte README at `613a3d8…` |
| Fulcra MCP: `record_data` custom fields, client `record_id`, idempotent retry; `get_data_updates`; `write_file` versions | VERIFIED — fulcra-context-mcp `tools.py` (main) |
| Fulcra "supports selective sharing of owner-scoped context" | VERIFIED as read-only sharing — `create_share` docstring ("they can never write here"); write-back NOT supported |
| Fulcra files versioned | VERIFIED — https://docs.fulcradynamics.com/fulcra-platform/ ; conditional update/CAS NOT documented |
| Fulcra catalog returns recordable v1 `Event`/`Metric` base types | NOT verified (private authenticated check per the assessment; not reproduced here) |
| GitHub forks of public repos are public; visibility can't be changed on the fork alone | VERIFIED — https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks |
| Stars on a fork do not count toward upstream | NOT verified from docs (stars page silent on forks); inference from forks being separate repositories |
| Claude Code scheduled tasks / `/loop` / monitors are session-bound; Routines run in cloud without a session | VERIFIED — https://code.claude.com/docs/en/scheduled-tasks |
| Vercel/Fulcra deploy target supports scheduled server-side execution (needed for D5 option a) | NOT verified |
| Fulcra Auth0 tenant can act as authorization server for a third-party MCP resource (F2) | NOT verified |
