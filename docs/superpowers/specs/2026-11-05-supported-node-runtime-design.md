# Supported deployment runtime

Fresh Fulcra deploy projects can default to Node 26, which the current Svelte Vercel adapter rejects. A successful deployment after manually changing one project's runtime does not repair the fork instructions or source defaults.

Constrain the web package's Node engine to `22.x || 24.x`, preserving the existing Node 22 CI and the verified Node 24 deployment. Keep package-lock root metadata consistent and document the local prerequisite. Do not change dependencies, authentication, server configuration or persistent resources.

Package metadata is the smallest portable fix. Changing each user's project setting leaves the source problem intact; replacing the adapter or suppressing its checks adds unrelated behavior. This is an agent implementation choice under Ash's standing instruction to resolve reversible choices and keep working.

Verify with the actual existing disposable deployment: unchanged source must fail under project default 26; the corrected source must select supported 24 and pass despite that default. Restore the saved project runtime after the probe, retain the prior healthy deployment and all private configuration, and run the existing regression suites.
