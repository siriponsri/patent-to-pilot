# PRD1 executor receipt

PRD1 implements the development data pipeline, shared dossier contract and first-pass bilingual export. It started on the fetched research/loe-bench base `7f3593b8`. The inputs are the two frozen native score exports and the guarded development evidence reconstruction. The user guide holds the [build commands and evidence policy](../../product/PRD1.md). The [machine-readable selection](../../product/DEMO_MOLECULES.json) is the handoff to the demo and evidence cards.

## Handoff to the Planner

- For PRD2, consume the six per-cutoff queue files and dossier JSONs under `product/demo/data/`. Link demo records by exact active-moiety key and the `(as_of, horizon_months)` cell. Preserve the distinction between the product's lexical queue tie rule and fractional ties in benchmark reports.
- For EVP, emit the dossier-shaped Thai/ASEAN claims and sources at the path documented in the user guide. Rebuild and re-audit after evidence integration. Review dated context and claim meaning independently of C8 citation coverage.
- The 28 November owner decision in `a87f8407` keeps PRD1 on GPT for data, builder and audit. Claude owns the next renderer redesign and product integration.

## Execution notes

- An initial probe hit the older freeze runner's pre-registration guard because the base already included the OSF lock. The build uses only the guarded C3 input projection with fixed development cells, validates rosters against the score exports and rejects execution when a preregistration authorization variable is present. The registered-test runner and protected outcomes were outside the run.
- The first input probe unpacked five values from the six-value C3 adapter and stopped before creating output. The adapter now consumes the documented return shape.
- Direct Chrome CLI attempts produced valid samples but hit inherited-handle, cache-cleanup and process-timeout failures in batch. The PDF exporter reuses one isolated headless Chrome session through the installed Playwright 1.64.1 with Chrome 158.0.8127.37. The HTML path stays standard-library only. The Thai sample embeds TH Sarabun New.
- Execution was local CPU only. Paid APIs, GPU work, Track A freeze, comparative product claims and semantic FTO review were outside this receipt.

## Verification

| Check | Result |
|---|---|
| `py -3.12 -m product.mwd.build` | PASS, 32 dossiers and six queues for 3,244 eligible cutoff-horizon rows |
| `py -3.12 -m product.mwd.audit` | PASS, 1,720/1,720 traceable claims, 1,688 hash-backed, zero future-dated as-of claims |
| Cross-file queue reconciliation | PASS, all 32 dossiers match their queue row's scores, rank, membership and development event |
| `py -3.12 -m product.mwd.render --pdf` | PASS, 64 HTML and 64 Chrome PDFs in Thai and English |
| Export inspection | PASS, all seven HTML sections, internal citation targets and language links present. All 64 PDFs opened with nonempty pages (649 pages total). Thai first pages embed TH Sarabun New. |
| `py -3.12 -m pytest product/mwd/tests -ra` | PASS, 8 passed |
| `py -3.12 -m pytest -ra` | Exit 1, 2,760 passed, 50 skipped, one xfailed, and the eight allowed pre-existing SACR r2/r3 budget failures |

The eight full-suite failures are the four parameterizations of `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` in each of the r2 and r3 supervisor files. Their unchanged resource ledger fails the shared budget arithmetic guard. The scope-specific suite validates the schema on every generated dossier.
