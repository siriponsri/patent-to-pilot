# R1 history recheck — 2026-11-03

Status: `LEGACY_HISTORY_REVIEWED_NOT_CANONICAL`

This is a bounded read-only recheck of the R1 evidence already present in the
repository. It does not rescan `Documents` or `Desktop`, copy private journals,
create a registry, create a zero ledger, or call OpenRouter.

## Findings

- The two recovered files are `live.sqlite3` and
  `paired-revalidation-1.sqlite3`, both classified by the prior recovery
  receipt as legacy provider-pilot journals.
- Their recorded schemas are legacy `attempts/meta` (with `reconciliations`
  in one file), not the current R1 canonical ledger schema.
- The prior recovery receipt explicitly marks both as `r1_compatible=false`
  and the registration probe as `REJECTED_FAIL_CLOSED`.
- Four known legacy settled debits sum to `USD0.0001464`, matching the
  read-only key-usage observation. This is historical debit correspondence,
  not proof of complete R1 history, current account credit, or remaining
  admission.
- Unknown-pending attempts in the reviewed legacy receipts: `0`.

## Decision

The legacy receipts must remain historical evidence only. They cannot satisfy
the current paid gate and must not be rebound or imported into the canonical
R1 ledger without an owner-supplied migration contract or current sanitized
all-attempt export. Paid dispatch remains `BLOCKED_BEFORE_RESERVATION`.

## Evidence

- `docs/healthtech/audits/pepo-r1-metadata-recovery-20261031/legacy-journal-check.json`
- `docs/healthtech/audits/pepo-r1-metadata-recovery-20261031/reconciliation.json`
- `docs/healthtech/audits/pepo-o3-unblock-20261031/journal-recovery-20261031.json`
- `docs/healthtech/audits/pepo-o3-unblock-20261031/journal-search-20261031.json`

The next required owner evidence remains limited to the existing canonical R1
journal/export location and a current scoped credit snapshot, both non-secret.
