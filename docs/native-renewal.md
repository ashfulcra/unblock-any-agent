# Keep native connections renewed

The native pilot issues sealed worker/listener grants bounded to the originating Fulcra access token and one hour. A separately configured trusted operator can renew the same authorized connections using the existing Fulcra CLI login. No new OAuth client registration or database is required. This operator is opt-in; no scheduler or startup service is installed.

## Prepare in the owner's trusted environment

Use the current canonical checkout, Python3.13+ and an existing `fulcra-api` CLI authenticated as the dashboard owner. If it needs login, use the CLI's normal Fulcra sign-in. Owner authentication stays in that CLI's existing credential handling; the operator captures only an access token in memory. It does not copy a refresh token or owner token into worker profiles, plugin packages, requests, state or logs.

Enroll the worker and separate environment listener in the dashboard. Save their native profiles as owned mode0600 files outside source/plugin caches. The listener enrollment selects its environment and explicit worker IDs. Each file needs only `transport: fulcra-native`, the actual saved dashboard `url` and its sealed `token`. Prepare while those credentials are usable:

```sh
python3 -m unblock.native_renewal --owner-auth fulcra-cli --config /PRIVATE/operator.json --state /PRIVATE/operator-state.json --prepare --profile /PRIVATE/native-worker.json --profile /PRIVATE/native-listener.json
```

The helper authenticates each profile's own enrollment metadata, checks it against the owner's current source, and writes a private configuration selecting those existing grants and profile destinations. It starts nothing and refuses to replace an existing configuration. Internal enrollment IDs are derived from verified connections. All selected profiles must use the same dashboard and owner. A credential that expired before preparation needs owner-authorized reconnection first; a previously prepared operator can renew an expired, unrevoked anchor.

The operator modules are deliberately outside worker-plugin exports. Run them from this trusted canonical checkout. Worker/listener profiles continue to contain only narrow sealed credentials and lease metadata. The feature does not establish OS-level isolation between processes that already share an operating-system account.

## Run and verify

For one bounded check:

```sh
python3 -m unblock.native_renewal --owner-auth fulcra-cli --config /PRIVATE/operator.json --state /PRIVATE/operator-state.json --once
```

For a separate running operator process:

```sh
python3 -m unblock.native_renewal --owner-auth fulcra-cli --config /PRIVATE/operator.json --state /PRIVATE/operator-state.json --interval 30
```

Defaults renew within five minutes of a grant's expiry, with each new lease still bounded to one hour and the owner session. Keep all invocations for these profiles on the same private operator state/lock. An actual environment scheduler can run `--once`; establish its owner, next firing, lifetime and restart procedure separately. A running terminal loop stops when its process or machine stops. No always-on coverage follows from installing the skill or plugin.

Before enrollment, the operator saves the exact body, fixed expiry and stable intent. A lost response or delayed ingestion retains that pending attempt. Only exact native grant readback permits atomic profile replacement. The native listener reopens its narrow profile each tick, preserving its source/identity/scope-bound dispatch ledger across grant rotation. Replacements remain private regular files with the same owner. A crash after profile publication is reconciled against the saved candidate instead of blindly overwriting again.

`checked: true` means the owner source was checked; inspect `pending`, `errors` and `renewed` as well. An expired pending intent remains pending until its original record is visible. A verified expired record can be retained historically before a later tick creates a new intent. Failed/unknown reads retain previous profiles and pending state. A changed owner, origin, anchor scope or managed profile stops for reconciliation. Renewals name their preceding grant and preserve its exact scope. The server checks that chain and rejects descendants after any ancestor is revoked, including a revocation that races profile publication. Parent lease expiry alone does not invalidate a valid renewal. Revoking the anchor or latest grant stops renewal rather than reenrolling it. Renewing access does not resolve work or grant an agent broader authority.

If the CLI can no longer authenticate, reconnect that existing owner account. Reconcile explicit configuration/profile changes against retained state before restarting. Changing the configuration or replacing the ledger to forget an uncertain enrollment is not a recovery procedure.

## Observed bounded proof

The maintainer exercised two dedicated short-lived synthetic connections against the deployed native service. Existing 45-second grants expired and were denied; a separate operator renewed 60-second grants with identical worker/listener scopes. Stopping the operator allowed the replacements to expire, and the running listener reported source unavailable while retaining the exact pending request. Restarting the operator restored access and the same source/identity/listener ledger recovered that obligation. The probe then completed its synthetic request, stopped both processes and revoked all six test grants. Revocation prevented further renewal, and the owner token was absent from state, profiles and logs.

Two early harness errors were retained and corrected while resuming the same saved enrollments/request. The final acceptance did not create substitute identities to hide those attempts. This verifies bounded grant renewal and outage recovery through the existing CLI. It does not assert a forced upstream refresh-token exchange, perpetual authentication, a persistent scheduler, remote ChatGPT authorization or arbitrary-host wake.

A second live probe exercised the actual preparation command without copied enrollment IDs, then renewed a 30-second predecessor into a 60-second child. Expiring the predecessor denied its own access while preserving the valid child. A further descendant was denied after its predecessor was revoked, and the operator stopped without changing the managed profile. The dedicated family was revoked after evaluation; no persistent process was started.
