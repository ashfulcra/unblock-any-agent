# Unattended native renewal and uncertain pickup

Ash authorized execution on November 8 after prioritizing unattended reliability.
The maintainer review stays every three hours. Native grants remain bounded to
one hour and their original selected families.

## Approach

Reuse the existing owner CLI and renewal operator in a trusted local process,
with a private configuration selecting existing operator configurations/states.
An explicit launchd installation supervises that process independently of model
turns. No owner credential is written into its configuration, health or logs.
The CLI retains responsibility for refreshing its own existing authentication.

Longer worker grants would broaden authority and still not fix pickup. More
frequent model turns would restore the maintenance dependency Ash asked to
remove. A new backend or universal agent launcher is unnecessary for renewal.

The runtime persists a sanitized, atomic health snapshot after each pass, keeps
the last successful time on failure, refuses overlapping state/profile targets
or changed configuration, and uses a process lock. Failed/pending operations use
the existing exact-intent reconciliation; they never erase or replace ledgers.
Its process must actually run before independent renewal is claimed. launchd
restart is verified separately from a foreground run. It installs no new listener
grant, participant, destination or model wake route.

## Pickup safety

When a worker was launched but subsequent source readback is unavailable, retain
its claim as requiring reconciliation, including across listener restarts.
Passing time and source recovery alone cannot authorize another dispatch.
Existing explicit recovery still requires a stopped process and reconciled
effects. Observed acknowledgment/completion remains separate from launch receipt.

## Scope and evidence

Deploy renewal only for the existing separate selected14 and selected2 operator
configurations. Leave the frozen maintainer family and other services unchanged.
Do not assert automatic Codex answer pickup from independent renewal. Existing
actual-host gaps remain until a supported route produces responsible-model
continuation evidence. Public/plugin publication remains separate.
