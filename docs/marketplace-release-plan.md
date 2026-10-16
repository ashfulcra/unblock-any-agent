# Unblock Marketplace Release and Naming Plan

Planning baseline: 2026-10-16. Goal: publish useful Claude and ChatGPT plugins through their official public distribution surfaces, moving quickly toward the short `unblock` identity. This document records current requirements and proposed packaging; no package, portal draft, namespace reservation, or public submission has been created.

## Preferred names

| Surface | Proposed identity | Status |
| --- | --- | --- |
| Canonical source and skill repository | `ashfulcra/unblock-any-agent` | User-selected repository destination; local planning files exist. |
| Stable plugin identifier | `unblock` | Preferred candidate, subject to actual validation and availability. |
| Public display name | Unblock Any Agent | Proposed descriptive brand; distinguish from the package identifier. |
| Primary skill | `unblock` | Proposed shared workflow name. |
| Short invocation | `/unblock` | User's preferred target; host support and collisions need verification. |
| Claude Code native mod command | `/unblock` through `$.command.register` | Current official API documents bare commands; test registration, collisions, and behavior in the shipping host. |
| Claude standard plugin invocation | `/unblock:help` or another concise namespaced skill | Documented namespacing supports this form; choose and test the actual entry skill before release. |
| ChatGPT invocation | Installed plugin/skill selection and native app entry points | Do not promise a globally reserved slash command; use the host's supported invocation and discovery surfaces. |

Retain `unblock-any-agent` as a descriptive fallback package candidate if `unblock` is unavailable or fails naming review. Naming remains open until validated. Do not rename an established package casually: installation identity and component namespace depend on it.

Claude's manifest reference documents standard commands as `/plugin-name:command`. The current mod API explicitly supports a bare slash command through `$.command.register`; this provides a credible `/unblock` entry on compatible Claude Code hosts. It also documents taken-name failures, so test collisions and preserve the namespaced entry. A runtime command registration is not a global marketplace reservation. [Claude manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference#commands), [native mod command API](https://code.claude.com/docs/en/plugins/mods/api#add-a-command)

OpenAI's guidelines discourage generic dictionary-only public names. The proposed descriptive display brand and accurate workflow description should accompany a short identifier; they do not guarantee acceptance. [OpenAI naming guidance](https://developers.openai.com/plugins/plugin-guidelines)

## Actual official destinations

For Claude, the public directory accepts plugin submissions backed by a GitHub repository and optional plugin subdirectory. That listing reaches supported Claude surfaces. Current documentation distinguishes this from `claude-plugins-official`, whose listing route requires an Anthropic partner contact rather than the directory portal. Track the official Code marketplace goal separately; an owned GitHub marketplace alone does not satisfy it. [Claude distribution routes](https://code.claude.com/docs/en/plugins/publish)

The old official-repository submission link currently redirects to the directory publishing documentation, so it does not establish a separate self-service route into `claude-plugins-official`. [Current redirected submission destination](https://clau.de/plugin-directory-submission)

For ChatGPT, target OpenAI's public plugin directory. Use the chosen verified publishing identity and the actual submission portal, including its access checks, scans, review, and publish step. [OpenAI submission flow](https://developers.openai.com/plugins/deploy/submission)

## Package shape

Keep one canonical source repository with shared skills and product logic. Produce separate, self-contained platform export directories or archives from that source. Every exported skill is a regular directory containing its own `SKILL.md`; package-relative references must resolve inside the export. Avoid maintaining hand-edited copies of the workflow.

| Target | Required package direction |
| --- | --- |
| Claude | A complete GitHub plugin folder with `.claude-plugin/plugin.json`, skill files, README, license declaration, and declared MCP/components. Use supported relative paths and release versions. The directory validates the chosen repository commit and plugin path. |
| OpenAI | A portable root `plugin.json`, root `skills/`, and root `mcp.json` when using MCP. Put OpenAI presentation metadata under `extensions.com.openai`. Include explicit semantic versioning and self-contained assets. |

The root source repository can remain skill-first while exports meet each marketplace's layout. For the GitHub-backed Claude portal, publish a reproducibly generated, complete export at a stable repository path or release branch/tag; validation cannot depend on a local build or on files outside that plugin folder. [Claude package layout](https://code.claude.com/docs/en/plugins/manifest-reference), [OpenAI package layout](https://developers.openai.com/plugins/build/plugins)

OpenAI's public package cannot contain lifecycle hooks or pre-registered app references. Since adding MCP to an existing skills-only plugin is currently unsupported, include the intended remote MCP capability in the initial submission. Keep Claude-only mods/hooks out of the OpenAI export. [OpenAI submission constraints](https://developers.openai.com/plugins/deploy/submission), [public hook eligibility](https://developers.openai.com/plugins/build/plugins#bundled-mcp-servers-and-lifecycle-hooks)

Claude surfaces load different component subsets. Skills are broadly supported, while native lifecycle and UI features vary. If the product supplies its own remote MCP server, the Claude directory currently requires its connector to be submitted separately as well as referenced from the plugin. A complete Claude Code mod alone does not establish a complete Claude chat or Cowork experience. [Claude platform support](https://claude.com/docs/plugins/platform-support), [plugin and connector submission](https://claude.com/docs/plugins/submit)

## Name availability and acquisition

The public `claude-plugins-official` catalog inspected at commit `ea10b213686c90bb1984b2016937310e05336cf3` contained 315 entries and no plugin name/display-name match for `unblock`. This is a bounded public catalog check. It does not cover pending submissions, all Anthropic directory entries, trademarks, or private allocation. [Inspected official catalog](https://github.com/anthropics/claude-plugins-official/blob/ea10b213686c90bb1984b2016937310e05336cf3/.claude-plugin/marketplace.json)

Claude's current portal checks names against other organizations' plugins and can reject collisions or hold confusing/generic names for review. Treat portal validation as a real early check. The reviewed documentation does not establish when a draft or submission reserves a name. OpenAI name availability and allocation timing also remain unverified. [Claude name checks](https://claude.com/docs/plugins/pre-submission-checklist)

A local manifest, GitHub repository, or successful local install does not reserve either official namespace. Preserve evidence of the actual portal validation and assigned listing identity when those steps occur.

## Fast release path

1. Settle the preferred identifier, descriptive display brand, publisher identity, primary skill, and supported invocation forms while finalizing the first slice.
2. Audit publishing access early: an eligible Claude account and OpenAI organization/project permissions with a verified publisher. Identify the official Code marketplace contact route. These account checks are pending.
3. Build the smallest complete help-and-continuity workflow and both directory-compatible exports together. Keep the production remote MCP boundary in scope from the first OpenAI submission. Deliver a real useful workflow that meets the listing requirements.
4. Validate self-contained packages, clean installs, authentication, the actual command/skill entries, human answering, and replacement-session recovery. For Claude use strict plugin validation plus real-host checks; the portal applies additional rules.
5. Prepare the live endpoint, domain verification, listing assets/copy, user-facing setup, support, privacy, terms, reviewer access, and reproducible evaluation evidence. Use the official field/check references below as the release checklist; do not infer eligibility from a successful ZIP upload.
6. Submit the complete packages through the actual official routes as soon as this slice is ready. Track validation, review, name status, and publication independently. Keep source links directed to the canonical skill repository for discovery and stars.

Broader features can follow this first useful release. Official packaging and distribution are now part of the early critical path rather than postponed until every planned feature is finished. Public submission/publication will be a concrete, reviewable action once the package exists; this plan does not create placeholder listings.

## Release checks

- Verify allowed package identifiers, immutable identity expectations, semantic versions, manifest fields, and actual invoked skill names.
- Check the exported file tree, regular skill directories, valid YAML, supported paths, license, README, and platform-specific component eligibility.
- Verify publisher access, production service authentication, host capabilities, metadata/scans, reviewer access, and public listing URLs.
- Test a fresh install and reconnect, answers from another surface, absent-session recovery, and the limitations actually advertised.
- Keep official-directory acceptance, official-Code-marketplace placement, name allocation, and GitHub distribution as distinct results.

Use the current [Claude pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist), [OpenAI field requirements](https://developers.openai.com/plugins/deploy/submission#manifest-fields), and [OpenAI validation errors](https://developers.openai.com/plugins/deploy/submission-errors) rather than freezing all portal limits into product code. Re-check these requirements for the actual release date.
