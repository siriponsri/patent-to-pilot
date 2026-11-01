# Queued cancel/resume duplicate execution repair

Cancelling a queued local HTTP job and immediately resuming it leaves two executor callbacks. Previously both callbacks ran the same job, including a second write after the first completed. The worker now atomically claims only `queued` jobs and ignores stale callbacks. The regression holds the worker until both callbacks exist, then checks exactly one runner invocation, one attempt, and one stored history version.

This isolated branch contains the HTTP repair, its self-contained test, and this receipt only on top of base `0cf41e0d37cac75bc9475c8604ab3dabb5c5fd66`. The separate paused Luna worktree retains its pre-existing postprocessor, vector, benchmark, manuscript, and owner edits. No whole-file dirty owner changes were staged into this branch.

Validation on the isolated candidate: **481 passed, 1 optional tokenizer skip**, zero failures. See [verification.json](verification.json) for source hashes, dependency versions and scope. This is engineering evidence; it does not establish a new scientific result or live provider parity.

The current paused worktree already has the same repair applied. When integrating this commit later, check patch equivalence before replaying it; do not apply it twice or reset the paused worktree.
