# Next actions

Request one combined allocation confirmation containing:

1. Authorized destination and job root.
2. GPU UUID or CPU quota.
3. Execution window and hard deadline.
4. VRAM, RAM, and disk limits.
5. Podi/shared-service restrictions.
6. Authorization for controlled transfer/use of the runtime bundle and pinned model artifacts.

Then run the 32-100 document remote canary, record numeric integrity and resource facts, and only then start the full resumable encoding job. Keep the full remote branch `BLOCKED_LOCAL` until those facts are present.
