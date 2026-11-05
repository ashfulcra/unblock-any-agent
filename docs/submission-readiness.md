# Public submission preparation

This checklist describes the 0.7.7 source candidate. It is not an uploaded draft,
review approval, public release, or installed private-plugin update.

## Prepared in the package

- Separate, self-contained Claude and portable OpenAI exports, including the
  approved Fulcra Dynamics publisher, Apache-2.0 license and retained notices.
- A real 512 × 512 PNG listing/composer icon, derived from the dashboard's
  existing `u ↗` mark. Its editable source is `assets/unblock-icon.svg`; render it
  with `rsvg-convert -w 512 -h 512 assets/unblock-icon.svg -o assets/unblock-icon.png`.
- Product and support links to the public canonical repository and its issue
  tracker. Both destinations were opened and inspected on November 5, 2026.
- Three starter prompts, three reviewer prompts, five positive and three
  negative draft cases, plus release notes in the portable manifest.
- The existing local worker MCP and optional, separate human inbox runtime.
  No credential, private profile, owner operation, listener startup or invented
  remote endpoint is added by this preparation.

The canonical review cases live in `packaging/openai-review.json` and are copied
into the generated portable manifest. Their setup uses a dedicated, scoped test
worker and a separately authorized human interface. They describe supported
behavior; they are **not recorded host-review results**. Source regression tests
cover request/revision/action/expectation boundaries, while an actual review run
must retain its own tool and outcome evidence.

## Local CLI verification

The previous 0.7.5 candidate was actually installed from both a local catalog and
the public GitHub candidate branch in empty isolated Claude Code 2.1.312 configs.
List/details, duplicate install, disable/enable, same-version update and removal
were checked. The remote clone matched the expected commit and all 31 copied
plugin files matched the candidate bytes. All registrations were removed.
Candidate 0.7.6 was also installed from its public GitHub source branch in a fresh
configuration, byte-checked and removed.
This is CLI installation evidence, not model tool-use or an official listing.

That testing found a malformed-profile startup traceback. Candidate 0.7.6 returns
the existing structured MCP setup error for non-object profiles and non-string
URL/token fields. The local/native clients and Claude route reject these profiles
before network access or worker launch. Generic private JSON artifacts retain
their original behavior. Candidate 0.7.7 additionally rejects non-object human
profiles and non-string journal paths before account or journal access, preserving
the exact human-only schema and owner/project binding. The original failing
probe and the default official-marketplace cache hash change remain retained;
full global configuration preservation is not certified.

## Remaining preparation and online checks

| Item | State and exact next step |
| --- | --- |
| Public privacy and terms URLs | Missing. The publisher must supply or approve pages covering this plugin's actual practices. Do not substitute the source license for service terms or invent retention/deletion commitments. |
| Countries and commerce declarations | Not supplied. Leave these manifest fields absent until the publisher provides the actual choices; omission is not a claim of worldwide availability or no commerce. |
| Recorded demo | Not recorded for this candidate. Follow the walkthrough below in an authorized, supported host, capture actual interactions with a recording tool, inspect playback for secrets/readability, and verify a reviewer-accessible hosting URL. Screenshots and this script are not a video. |
| Reviewer access | Unverified. Arrange a dedicated test account and scope through secure portal fields; never include credentials in the ZIP or reuse maintainer credentials. |
| OpenAI desktop/local-MCP eligibility | Portal/account check remains required. Preserve the actual stdio MCP package; do not remove it to masquerade as skills-only or claim a ChatGPT web connection. |
| Remote ChatGPT web | Separate incomplete integration/acceptance. No OAuth endpoint or live web-worker connection is invented by the local package. |
| Portal draft, scans, attestations, review and publication | Not performed. Verify the publisher account for the approved Fulcra Dynamics name; complete the applicable preparation above, then inspect the saved draft and required scans. An authorized developer must complete legal attestations. |
| Official Claude directory/Code marketplace | Separate actual account, submission and destination checks remain required. The owned GitHub catalog is a source install route, not an official listing. |

## Demo walkthrough to record

Use one dedicated test profile and disposable report artifact. Keep its credential
file outside the plugin and recording. Do not start a new participant or grant
without applicable authorization.

1. Show the candidate version and scoped tool discovery in the intended host.
2. Ask: “I need a choice between bullets and a short paragraph before I can
   finish this demo report. Ask me clearly and preserve what you need to continue.”
   Show the actual read-back request and the separate human decision interface.
3. Submit an actual answer through that human interface. Ask the responsible
   worker to continue. Show the original revision, complete answer snapshot,
   declared action, real report readback and observed completion.
4. In a fresh authorized model context, recover the same completed task. Show
   that the report and stable action remain unchanged rather than duplicated.
5. Ask the worker to enroll another agent with owner access. Show its boundary
   explanation and absence of an owner operation. Do not expose credentials.

Record the actual outcome of each applicable case as Passed, Failed, Blocked or
Not run outside the manifest. Do not infer automatic idle pickup from a prompted
continuation, or arbitrary desktop/ChatGPT web recovery from a CLI session.

## Build and inspect

Run `python3 scripts/build_plugins.py --out <fresh-directory>`, inspect the final
archives including hidden manifests, and run the package regression suite. The
build refuses to overwrite an existing export and copies only explicit contained
source files. Regenerate both checked-in candidates after canonical changes.

A source/ZIP preparation can finish without portal access. The remaining online
or publisher-dependent items must remain explicit; an incomplete candidate is
not submission-ready.

Primary requirements: [OpenAI submission flow](https://developers.openai.com/plugins/deploy/submission),
[remote MCP review](https://developers.openai.com/plugins/deploy/app-review), and
[Claude publication routes](https://code.claude.com/docs/en/plugins/publish).
