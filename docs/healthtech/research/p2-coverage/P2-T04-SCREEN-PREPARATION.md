# P2-T04 preparation: one bounded relation search on Challenge-1M

**Status:** preparation, NOT_RUN. This file records reusable inputs and the proposed matched design.
Freeze the executable protocol and its manifest after the D19 decisions and before running the screen.
No new retrieval scores or paid jobs were produced in this preparation.

## Baseline inputs

| Route | Provenance | Use in the screen |
|---|---|---|
| Arctic C1 | P2-T02 receipt; private `p2t02-runpod/p2-coverage/runs/arctic-c1/run-P1-DEV.tsv.gz` | Complete-content dense control |
| BM25-full | P2-T02 receipt; same root, `runs/bm25-full/run-P1-DEV.tsv.gz` | Complete-content lexical control; rebuild the searchable content for fresh queries |
| Qwen3 and PatEmbed | D19 amendment A2 and its final per-model gate and decision | Use C1 on PASS and a qualifying contrast; keep C0 on a completed NO_GAIN decision. A pending or failed D19 arm stays unresolved |
| A3r1 | P1-T05 receipt; `alloc-L0-Q1-P1-H1-K1` | Keep the historical exploratory comparator; if its routes are reused with the new baselines, identify that comparison separately |

The first two P1-DEV run files and the Arctic content manifest are present locally. The full lexical passages and
the dense C1 vectors were not retained. The rerun of the strongest original-query fusion and the deeper-query
descriptives are in the [P2-T02 receipt](../../../tracking/owner-note-22112026/receipts/P2-T02_coverage_control_results.md).
Bind the exact route files and evaluator inputs by SHA-256 in the frozen screen manifest.

## Proposed matched design

- **Population and provenance.** P1-DEV only. Select the fixed query manifest by a stable app-id rule independent of
  relevance judgments and route success. Derive requirements from exact spans of the original query. Read only
  eligible seed documents to assess whether a relation is unresolved. Store the source and version, text hash and
  offsets for every copied span. Keep the assessor's signal separate from human citation judgments.
- **Shared retrieval.** Use a fixed seed ranking from the declared complete-content baselines. Rebuild the P2-T02
  full-text passages and verify the frozen content fingerprints. The additional lexical queries share that index,
  tokenizer and cap. Apply the filing-date and self-unit masks before ranking and preserve the benchmark's unit
  identity. Use one common reranker against the original query text and a common final cutoff.
- **Arms.** Run matched original-query extra depth, one static requirement query, generic lexical feedback,
  extractive feedback from the same capped seed passages, and the unresolved-relation action with
  [P2-T03's pinned policy](../../../tracking/owner-note-22112026/receipts/P2-T03_mechanism_spec.md). Include a
  within-query shuffled binding where there are at least two eligible bindings. Declare ordering, deduplication,
  ties, seed inspections, search depth, reranker input cap and fallback before running. Run the shared budgets on
  the full manifest and separately report where the relation policy actually takes an action.
- **Evaluator.** The engine receives query text, eligible corpus metadata and seed rankings. A separate evaluator
  receives the finished runs and P1-DEV judgments. Report ALL, IN and OUT R@200, art-unit paired intervals, new
  candidates and judged-positive recovery/displacement, net score after reranking and the observed resource costs.
  Record the viability rule before scoring and reserve confirmatory claims for the later frozen comparison.

## Execution prerequisites

Choose the runtime assessor and exercise the adapters on authored fixtures, then freeze its rules, the comparison
manifest and the evaluator before touching score outputs. Reproducing the BM25-full content is a CPU staging job.
On dr-train, run one large CPU stage at a time, give 8–16 workers their own chunks, freeze the parent heap before
forking, estimate full-scale RSS, and use a 30 GiB MemAvailable watchdog restricted to the project job group.
Use the final D19 outcome to finish the baseline manifest. R2 authorizes D19, while this screen requires its own
resource accounting and an approved scope for any paid execution.
