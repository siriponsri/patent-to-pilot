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
- `p2t04_evaluate_screen.py` uses a separate pinned P1-DEV evaluator manifest. It verifies cohort and ranking
  integrity, keeps empty rankings in the cohort and reports paired recall, judgment-conditioned recovery and displacement.

Bind the baseline routing, input views, sampler, arm limits, assessor settings, evaluator and resources in an executable
manifest before any DEV measurement. The historical reproduction gate uses the archived Arctic-serialised original
queries. If the screen itself uses complete original query text for literal clause spans, keep that input view common
across its arms and disclose the difference from the historical retrieval arms.

The offline implementation passed the combined pypdf/PyThaiNLP gate with 2,741 passing tests, nine skips, one known
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
| `p2t04-preflight-20261124/queries-arctic-P1-DEV.jsonl` | `7ff4645911c7079048c531d6db139cdaa19128e57f495a337c29ee6f95099956` |
| `p2t04-preflight-20261124/a3r1-f3star-P1-DEV.tsv.gz` | `e6757311c7361a26cff4764047d7b2895477f6db3405067c7c5fc8d2839a695e` |
| `p2t02-d19-runpod/complete-lexical-passages.jsonl.gz` | `79b53f8dc994c6124ebe1f0498563077f5e9ab0c22a580135545773c1154b94d` |
| `p2t04-preflight-20261124/clusters-P1-DEV.tsv` | `161fbbdecfc4d21e49849e48e5a5229cb1f69760a573ed46ed2188a0eb45cc21` |
| `p2t04-preflight-20261124/dr-runtime-stage.json` | `c66e0d650788cbae6480c4e75390997945e9696693de515823f3faba23f549f6` |

The Arctic query view streams the 25,626 P1-DEV rows from the existing dr-train non-TEST serialization at
`/data/ptp-paper2/bridgeret/ser-arctic-v1/queries.jsonl`. A single process ran with a 30 GiB MemAvailable
watchdog. No output was staged on dr-train. The A3r1 comparator was extracted from the verified results archive,
member `data/ptp-paper2/g03-dev/runs-a3r1-full/P1-DEV/alloc-L0-Q1-P1-H1-K1.tsv`. Its legacy C0 routes remain
identified in the planned matched-sample evaluation. These two transfers produced no new retrieval scores.
The recovered full-text passages match the P2-T02 manifest on decompressed bytes, allowing P2-T04 to reuse the
content without rebuilding the claims on dr-train. See the [D19 receipt](../../../tracking/owner-note-22112026/receipts/P2-T02_D19_followup_results.md).
The stage receipt pins the ten files transferred to `/data/ptp-paper2/p2t04-run-prep-20261124`. Relevance pairs
and the derived art-unit TSV are evaluator inputs and do not enter the runtime stage.

## Proposed freeze values for the P1-DEV screen

These are prospective execution parameters. Complete the comparator and evaluator input pins after D19 and
publish the manifests before running the score path.

| Item | Proposed value |
|---|---|
| Screen cohort | 2,000 apps with archived P1-DEV query text, smallest SHA-256 of UTF-8 `ptp-p2t04-screen-v1/<app_id>`, ties by app ID |
| Candidate eligibility | P2-T02 filing date strictly after first publication, self unit excluded, archived missing-date convention |
| Seed | Four G03 windows, Q2/P2, RRF k=60 and the existing tie order, first 200 pooled units |
| Complete-content route rows | Arctic C1, BM25-full, and per-model D19 qualifying C1 or explicitly retained C0 |
| Close controls | Deeper original query, static first requirement, generic term-frequency feedback, extractive source feedback, within-query shuffled binding |
| Common limits | Eight seed reads, 1,500 characters per source, four copied feedback terms, one lexical step up to depth 400 with at most 20 returned candidates, final depth 200 |
| Deeper original query | Use positions 201–220 of the matched original-text lexical search |
| Assessor | First 2,500 claim characters, up to four condition spans and four anchor terms, local windows of twelve tokens, up to 28 inspected sources with the same 1,500-character cap |
| Outcome measure | Paired ALL R@200 with examiner art-unit bootstrap. Report IN and OUT on identical metric support and count new and displaced judged positives |
| Screen reference | The strongest mean among the close controls, seed-only rerank, complete-content fusion and individual complete-content routes, using the fixed cohort. Report all contrasts, including A3r1 F3* as a historical C0-route reference |
| Progression criterion | Against the screen reference, ALL improvement at least +0.010 with paired lower bound above zero, and IN/OUT paired lower bounds above −0.005. Smaller gains stay exploratory |

Use exact archived Arctic query serialization only for the lexical reproduction gate. All matched arms use the
same original query string formed from title, abstract and claim with newline joins, retaining the exact claim
offset. The 20 returned candidates and optional post-search coverage checks are recorded. No-action cases stay in
the declared cohort. The prospective practical margin comes from the owner score contract.

One CPU stage should run at a time on dr-train. Budget up to eight numeric-library threads and a 30 GiB
MemAvailable watchdog that targets only the project process group. The old BM25-full RSS was 12.6 GiB.
Budget 36 GiB peak for the index, route rows and transient buffers before checking live headroom. The
proposed route data cohort and streaming passes avoid loading the full probe ranking sets into memory.
