# Decision workspace correction

The primary user is a human deciding what agents need to continue. Lead with the actual agent name and original elapsed wait, a concise question and relevant context. Keep forms out of the overview; open one focused decision panel with context, recommendation, next action, saved decisions and observed progress.

The overview provides Needs you / With agents / Done, search across decision and context, agent filter, longest-waiting sort, board/list and a map of real agent ownership. Do not infer dependency relationships. Preserve source history, conflict states, pending write intents and drafts across refresh and panel closing. A revised question requires explicit review of the draft. Sending an answer is distinct from worker resumption or completion.

Use retained upstream record dates as presentation metadata without changing signed event identities. Derive original dates from root question records; missing original dates remain unknown even when later revisions are timestamped. Completed answers remain visible. Failed first reads show unknown work; later failures retain last-known work.

Keep template sign-in and owner/worker authorization unchanged. Verify desktop and narrow layouts, keyboard close/focus, changed-question guard, source failure and a bounded real-source answer→worker result. Reuse the existing deployment and harness.

The next in-chat slice is a separate human inbox using explicit owner authentication, compact decisions and the same reviewed snapshots. Never expose owner answering through a worker profile. Validate actual host rendering and transport separately from source/package availability. Remote ChatGPT authorization remains tied to an authorized issuer deployment.
