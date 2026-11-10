# Dev run-plan, attempt and cost reconciliation
research/sacr_run_reconcile.py reconciles an expected digest-bound dev manifest,
six explicit stage slots per query (profile/generic/selective/embedding/acquisition/
selection), terminal attempt receipts, actual cost events and complete query outcomes.
One query-stage slot prevents undeclared retries. Skips require a reason and receipt;
they do not disappear. Every started attempt needs one matching cost event, including
failed/interrupted work. Event IDs, query, stage and status must match the journal.

Nonterminal PLANNED/RESERVED/RUNNING records are rejected for final reconciliation;
this does not classify them as interrupted or authorize restarting. The controller
must inspect the live process/handle. READY requires completed profile and retrieval
stages; missing-input outcomes require all stages skipped. Failure classifications
must agree with recorded attempt stages. Dev-only enforcement rejects a test manifest
even when its digest matches. No parameter here authorizes protected evaluation.

27 tests pass:12 reconciliation,15 outcomes. Coverage includes complete records,
explicit missing-input skips, changed/test manifests, absent attempts/costs, duplicates,
live/nonterminal state, wrong event stage, false READY, missing receipt and retry slots.
Ruff passes for two new files. No runtime/model/data/GPU job.

Limit: this is a record reconciler, NOT a durable controller or proof of truthful
receipts. Receipt SHA fields are syntactically checked, not loaded from artifact files.
Expected manifest hashes must come from trusted pre-execution reservations. Source/
model/encoder/index identity manifests and actual receipt bytes remain external.
The six-slot plan describes the current prospective factorial flow, not a replacement
for earlier immutable model-smoke records. Generation calls/token/time caps still need
controller enforcement; standalone arm costs and actual end-to-end times remain open.
No false claim that full resource or experiment orchestration is now complete.

Next implement/exercise a durable offline controller with injected synthetic backends
that reserves before calls, records failures and receipt bytes once, and feeds this
reconciler. Then review remaining integration against the readiness matrix before
any actual encoding. External curator/isolation/A03/parity and generation/fidelity
gates remain unchanged. Earlier failures are preserved.
