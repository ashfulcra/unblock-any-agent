# Nurse repair: incomplete harness run badges

Actual deployed harness shows M2-3attempt1completed despite its retained latest RUN_COMPLETE status being incomplete. Current M2-3attempt2completion and all product evidence remain valid. Act as Nurse; only harness status interpretation changes. No product specification or milestone acceptance changes.

## Harness

Separate HARNESS-1repair run,30minute override, up to2harness-fix retries unchanged. Save completed M2-3run configuration before starting. Record observed defect and repair/evaluation/source readback. Do not emit a product MARK_COMPLETE or change fullM3’s incomplete state.

1. Extract the existing latest-event status contract into a pure helper; write regressions for actual RUN_COMPLETE incomplete/failed/completed, legacy incomplete/escalated states and unknown status. Watch tests fail before implementation.
2. Use the helper in HarnessDashboard. Verify web unit/check/build; deploy with the same saved project/auth.
3. Actual browser must show the older M2-3attempt1incomplete and attempt2completed. Publish/read back PR/CI/main; record Nurse repair completion and own V5 evidence. Preserve all historical events.
