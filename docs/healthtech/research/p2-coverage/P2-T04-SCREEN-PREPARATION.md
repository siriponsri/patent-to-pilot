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

## Offline implementation checkpoint

- `p2t04_matched_screen.py` runs the common seed and arm accounting, the pinned P2-T03 relation action and native
  depth, static, generic, extractive and shuffled controls against a caller-supplied index. It records SHA-bound
  source offsets for submitted excerpts.
- `p2t04_requirements.py` proposes literal-span extraction for English conditional clauses. Its provisional
  assessor uses bounded lexical co-occurrence as a coverage signal and requires a source excerpt for an actionable
  unresolved relation. The signal is an engineering heuristic and is not a human judgment.
- `p2t04_bm25_backend.py` implements the archived BM25-full term weights, date/self filters and corpus-order tie
  handling. It cuts a prefix of the native shortlist when an arm asks for fewer candidates. Exact reproduction
  against archived BM25-full P1-DEV rankings remains NOT_RUN. The local Python has no scikit-learn.
- `p2t04_run_screen.py` adds a hash-bound P1-DEV runtime entry point. It requires full archived BM25 reproduction
  on the frozen query list before the matched run, uses the existing four-window G03 fusion for the seed, writes
  original-route and matched-arm rankings for the separate evaluator, and emits trace and runtime receipts.

Bind the baseline routing, input views, sampler, arm limits, assessor settings, evaluator and resources in an executable
manifest before any DEV measurement. The historical reproduction gate uses the archived Arctic-serialised original
queries. If the screen itself uses complete original query text for literal clause spans, keep that input view common
across its arms and disclose the difference from the historical retrieval arms.

The offline implementation passed the combined pypdf/PyThaiNLP gate with 2,729 passing tests, nine skips, one known
xfail and the eight permitted SACR supervisor failures. The added skip is the synthetic test that compares the native
scikit-learn CLI and adapter. The frozen-manifest entry point was exercised with an authored corpus and in-memory fixture.
A read-only check found NumPy 2.2.6, SciPy 1.18.1 and scikit-learn 1.9.1 in the existing dr-train research environment.
Keep that version difference visible and require the exact archived BM25 gate before using it for any screen.

### Local fingerprints, 24 Nov 2026

These hashes identify the candidate inputs checked during preparation. The executable freeze must bind the final
baseline decision and the remainder of the input set.

| Private artifact locator | SHA-256 |
|---|---|
| `p2t02-runpod/p2-coverage/runs/arctic-c1/run-P1-DEV.tsv.gz` | `1529d8c9b11ae19b8401be872fff70492e976a5dcdb8f7bb46ed0996667b858d` |
| `p2t02-runpod/p2-coverage/runs/bm25-full/run-P1-DEV.tsv.gz` | `19f7d75e3e8526ceeec67665ac3ba5741bd24e3c749482328e7d1f4f3f0a5eb4` |
| `p2t02-runpod/p2-coverage/content/manifest.json` | `4627d4f133feaf634fca28b1ef611789351f1150632050a6f59f096ac7f98d6b` |
| `g03-a3r1-runpod-stage/tree/data/ptp-paper2/bridgeret/texts-v1/queries.jsonl` | `46bd76d21d9e580e993d38533394b3d6318b23a8c966c88dbab6789cdd40bf02` |
| `g03-a3r1-runpod-stage/tree/data/ptp-paper2/bridgeret/code/eval_bridgeret_dev.py` | `a6f25e52c7cc1651a777da0351f72f231deac53afab5fd936c82b85e85da8fd6` |
