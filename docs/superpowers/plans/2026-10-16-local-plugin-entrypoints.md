# Local skill and plugin entry points

Continue inline under the approved first-release scope and standing autonomy instruction. This is a local integration slice; it does not claim ChatGPT web access, official listing, or production OAuth.

Architecture: reuse the authenticated loopback application service. A stdio MCP adapter binds to one private agent credential; no caller-supplied identity, arbitrary request URL, shell, or owner enrollment tools. Use the maintained MCP Python SDK 2.3.0. Canonical `skills/unblock` contains one portable workflow plus contained setup reference. Reproducible exports copy that skill and the existing runtime into separate self-contained Claude and Agent Plugins packages. The latter is a local desktop development package; remote HTTPS and host pickup remain required for the web surface.

1. [x] Write real MCP client tests for tool discovery, help/recovery/progress, revoked credentials, neighbor isolation and malicious identifiers. Observe missing adapter failure, implement, then pass the tests.
2. [x] Run a missing-skill baseline, write the concise reference skill, validate metadata and exercise a fresh-context recovery/setup scenario. Keep scripts/references self-contained.
3. [x] Write export tests for self-contained packages, contained regular files, synchronized identity/version and usable copied runtime. Implement explicit allowlist copying; export outside source with no credentials or local paths. Run Claude strict native validation and a portable schema check.
4. [x] Verify the packaged MCP process with a real client. Do not claim a host install until that host has loaded it; no account upload or global plugin configuration is needed for source development.
5. [ ] Record evidence and exact remaining integration prerequisites; publish/read back own V5 progress; run the identity-specific exit check and continue safe work.

Provisional choices: package ID `unblock`, display Unblock Any Agent, local development version 0.1.0. No namespace is reserved. No project license has been selected. Do not invent a production endpoint or treat a local package as the public release.
