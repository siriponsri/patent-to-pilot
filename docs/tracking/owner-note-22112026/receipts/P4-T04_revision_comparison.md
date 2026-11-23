# P4-T04 receipt: selective revision against full recomputation

**Task:** P4-T04, "Verify selective revision against full recomputation". Acceptance (owner note): change source text,
scope edges and corpus membership; compare the affected evidence with a full rerun; measure work and cost before
claiming savings.
**Date:** 23 Nov 2026; updated 24 Nov 2026 for owner decision D25 (policy `ptp-structural-acquisition/2.1.0`, which fixes
D2). **Cost:** USD 0. No network, model, paid call or download. Every fixture is authored and its first line says
`SYNTHETIC FIXTURE - NOT A REAL DOCUMENT`.
**Status fields:**
- `product_readiness`: under policy 2.1.0, selective revision equals a full recomputation from scratch in **11 of 11**
  runnable scenarios, and a full rerun in place also equals scratch in 11 of 11. Defect D2 is fixed (D25). Corpus removal
  is still not supported (D3). The 23 Nov results under policy 2.0.0 (10 of 11, D2 open) are kept below as history.
- `method_evidence`: none. This is an engineering check of the revision path; it measures no retrieval effectiveness.
- `publication_readiness`: not affected.

## What was built

| Piece | Where |
|---|---|
| Deterministic harness (scenarios, three paths, version-independent evidence signatures, exact diff, work meter) | `scripts/verify_selective_revision.py` |
| Tests (7 scenario tests, one of them a strict xfail for D2, plus 5 rule tests) | `tests/test_p4_t04_selective_revision.py` |
| Engine fix (D1) and work fix (skipped discarded verification search) | `src/patent_to_pilot/workbench/core.py` (`_process_revision`, new `_decision_depends_on_scope`) |
| Full JSON report of the 23 Nov run (policy 2.0.0; history) | `docs/tracking/owner-note-22112026/receipts/P4-T04_selective_revision_report.json` |
| D25 fix: policy 2.1.0 (pinned), sibling-seed anchor, per-run seed cache | `src/patent_to_pilot/workbench/relation_search.py` (`POLICY_V2_1`), `acquisition.py` (`_sibling_seeds`, `_sibling_seed_anchor`, option `policy`), `core.py` (seed hits kept per run) |
| D25 tests (order independence; 2.0.0 reproduction) | `tests/test_p4_t04_selective_revision.py`, `tests/test_structural_acquisition.py` |
| Full JSON report of the 24 Nov run (policy 2.1.0, harness 1.1.0) | `docs/tracking/owner-note-22112026/receipts/P4-T04_selective_revision_report_v2_1.json` |

Run it with `python scripts/verify_selective_revision.py --out report.json --markdown tables.md`. Add
`--without-scope-fix` to reproduce the selective path without the D1 fix, `--policy ptp-structural-acquisition/2.0.0`
to reproduce the 23 Nov results under the old policy (D2), and `--scenario ID` to pick scenarios.

### Method

For each scenario the harness imports one authored base corpus into an owner project (two candidates, three
requirements: a yes/no field, a free-text item and a temperature range), runs the full comparison once (state S0), and
then applies the change in three ways:

1. **selective:** the product path. `ingest_document` imports the change and `_process_revision` settles it by
   dependency (re-acquire, re-validate by search, or leave untouched). This runs on a copy of S0.
2. **full in place:** the same import on another copy of S0. The settle step only closes the event, and then
   `run_comparison` re-assesses every obligation in that store.
3. **full scratch:** a new store with the final corpus imported, then one `run_comparison`.

Every cell (candidate × requirement) is reduced to a signature. Version ids are replaced by the SHA-256 of the version
text, so `annex-b@v2` in one store equals `annex-b@v1` in another when the texts are identical. The signature is compared
exactly. It holds the following fields:
- outcome;
- reading;
- explanation;
- cited span: source, content hash, passage, code-point offsets and quote;
- stored search receipt: ordered unit ids, including the acquired units;
- linked structural-acquisition decision: gaps, reference states, action, anchors with offsets, new and final units;
- obligation state.

The receipt's `eligible_scope` is reported separately as provenance. A re-validated cell keeps the receipt written by its
original run, so its recorded scope is the old one. That is expected and is not an evidence difference.

The *changed cells* are the cells whose scratch signature differs from S0. A *missed* cell changed but the selective
path did not re-acquire it. An *over-invalidated* cell was re-acquired although it did not change: it costs work, but the
result stays correct.

**Work** is measured by wrapping the engine objects of each store; no engine code changes for this. The meter counts:
- seed searches;
- structural action searches;
- acquisition steps;
- passages written to `passages` and to the Thai derivative index;
- structure nodes;
- passage reads (from the run counters);
- provider-client requests, which are replaced by a function that raises;
- `provider_usage` rows;
- wall time.

## Results under policy 2.1.0 (24 Nov 2026, owner decision D25)

Environment:
- Windows 11, Python 3.12.10, SQLite 3.49.1;
- analyzer `ptp-thai-lexical/1.0.0;newmm-safe;pythainlp=5.4.0;dict=37875115d95d;fold-v1`;
- `core_code_sha256` `c6b3a05a…2e91`; harness `ptp-p4-t04-selective-revision/1.1.0`;
- policy `ptp-structural-acquisition/2.1.0`, SHA-256 `b632a2ca67e5037850312789e6ca1c6d6e5abb858b4ab00390269640d7686df4`.

| Scenario | Kind | Selective vs scratch | Full in place vs scratch | Changed cells (scratch truth) | Re-acquired | Re-validated by search | Untouched | Missed | Over-invalidated |
|---|---|---|---|---|---|---|---|---|---|
| a1-text-cited-annex | source_text | MATCH | MATCH | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| a2-text-seed-clause | source_text | MATCH | MATCH | C1/P1, C1/S1, C1/T1 | C1/P1, C1/S1, C1/T1 | none | 3 | none | none |
| a3-text-uncited-member | source_text | MATCH | MATCH | none | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1, C1/T1 |
| b1-edge-target-relabelled | scope_edge | MATCH | MATCH | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| b2-edge-retargeted | scope_edge | MATCH | MATCH | C1/P1, C1/S1, C1/T1 | C1/P1, C1/S1, C1/T1 | none | 3 | none | none |
| b3-edge-made-ambiguous | scope_edge | MATCH | MATCH | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| b4-edge-resolved-by-unrelated-member | scope_edge | MATCH | MATCH | C1/S1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/T1 |
| c1-member-added-resolves-edge | corpus_membership | MATCH | MATCH | C1/S1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/T1 |
| c2-member-added-retrieved | corpus_membership | MATCH | MATCH | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| c3-member-added-other-candidate | corpus_membership | MATCH | MATCH | C2/S1 | C2/S1, C2/T1 | C2/P1 | 3 | none | C2/T1 |
| c4-member-removed | corpus_membership | NOT_SUPPORTED | - | - | - | - | - | - | - |
| d1-sibling-anchor-order | source_text | MATCH | MATCH | none | C1/A1 | C1/E1 | 2 | none | C1/A1 |

What changed against the 23 Nov run (history below):
- **d1** is now MATCH on both checks. From scratch, in place and selectively, A1 (no hit) anchors
  `search_within_source` on `profile`, the source of E1's first current seed unit, and cites `profile#p0004[147:201]`.
  Under 2.0.0 the run from scratch searched the whole scope and cited `pricing#p0003` instead.
- **a1 to c2:** a full rerun in place now equals scratch. The only difference was the anchor list of `C2/S1`; under
  2.1.0 it is built from the current seed hits of P1 and T1, not from whichever results were already stored.
- The selective plans (re-acquired, re-validated, untouched, over-invalidated) are unchanged in every scenario.
- `python scripts/verify_selective_revision.py --policy ptp-structural-acquisition/2.0.0` reproduces the 23 Nov
  verdicts exactly (d1 MISMATCH_HISTORY; a1 to c2 in-place MISMATCH_HISTORY), so the fix is attributable to the
  policy change alone.

Work totals over the 11 runnable scenarios (per-scenario rows are in the JSON report):

| Path | Obligations re-assessed | Seed searches (measured) | Seed searches in run counters | Sibling seed searches (S1a) | Structural action searches | Passage reads | Passages indexed | Thai index rows written | Structure nodes written | Wall s | Provider requests | Paid model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| selective | 23 | 32 | 32 | 0 | 13 | 29 | 41 | 41 | 26 | 2.93 | 0 | 0 |
| full in place | 64 | 74 | 64 | 10 | 32 | 60 | 41 | 41 | 26 | 6.31 | 0 | 0 |
| full scratch | 64 | 74 | 64 | 10 | 32 | 60 | 221 | 221 | 181 | 7.30 | 0 | 0 |

- Policy 2.1.0 adds **sibling seed searches**: when a requirement with no eligible seed hit needs an anchor, the seed
  searches of the candidate's other active requirements that this run has not run yet are run now. Seeds already run
  in the same run (the obligation's own seed, or a verification search of the selective path) are reused.
- They are counted in the run counter `sibling_seed_searches`, and measured seed searches equal the obligation seed
  searches plus these in every path and scenario (10 in each full path: one per full run of a1 to c2 for `C2/S1`, and
  one for `A1` in d1). The selective path needed none here, because the sibling seeds were already searched.
- Every other count is the same as on 23 Nov. Wall times are single runs on one PC and are not a benchmark.

## History: results of 23 Nov 2026 under policy 2.0.0 (with the D1 fix; Thai analyzer active)

Environment:
- Windows 11, Python 3.12.10, SQLite 3.49.1;
- analyzer `ptp-thai-lexical/1.0.0;newmm-safe;pythainlp=5.4.0`;
- `core_code_sha256` `69f04707…6f80`.

The same verdicts were obtained without PyThaiNLP (legacy `unicode61` route, system Python).

| Scenario | Kind | Selective vs scratch | Full in place vs scratch | Changed cells (scratch truth) | Re-acquired | Re-validated by search | Untouched | Missed | Over-invalidated |
|---|---|---|---|---|---|---|---|---|---|
| a1-text-cited-annex | source_text | MATCH | MISMATCH_HISTORY | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| a2-text-seed-clause | source_text | MATCH | MISMATCH_HISTORY | C1/P1, C1/S1, C1/T1 | C1/P1, C1/S1, C1/T1 | none | 3 | none | none |
| a3-text-uncited-member | source_text | MATCH | MISMATCH_HISTORY | none | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1, C1/T1 |
| b1-edge-target-relabelled | scope_edge | MATCH | MISMATCH_HISTORY | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| b2-edge-retargeted | scope_edge | MATCH | MISMATCH_HISTORY | C1/P1, C1/S1, C1/T1 | C1/P1, C1/S1, C1/T1 | none | 3 | none | none |
| b3-edge-made-ambiguous | scope_edge | MATCH | MISMATCH_HISTORY | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| b4-edge-resolved-by-unrelated-member | scope_edge | MATCH | MISMATCH_HISTORY | C1/S1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/T1 |
| c1-member-added-resolves-edge | corpus_membership | MATCH | MISMATCH_HISTORY | C1/S1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/T1 |
| c2-member-added-retrieved | corpus_membership | MATCH | MISMATCH_HISTORY | C1/T1 | C1/S1, C1/T1 | C1/P1 | 3 | none | C1/S1 |
| c3-member-added-other-candidate | corpus_membership | MATCH | MATCH | C2/S1 | C2/S1, C2/T1 | C2/P1 | 3 | none | C2/T1 |
| c4-member-removed | corpus_membership | NOT_SUPPORTED | - | - | - | - | - | - | - |
| d1-sibling-anchor-order | source_text | MISMATCH_HISTORY | MISMATCH_HISTORY | none | C1/A1 | C1/E1 | 2 | none | C1/A1 |

How to read the "full in place vs scratch" column:
- In a1 to c2 it is MISMATCH_HISTORY because of one field only: the anchor list of `C2/S1`, a requirement with no hit
  whose action anchors on sibling citations (D2).
- The full rerun in place re-assesses C2 while older C2 results already exist, so it records two sibling anchors.
- A run from scratch records one.
- The action, the units and the evidence are identical.
- The selective path leaves C2 untouched, so it matches scratch.

### Work and cost (measured; per scenario rows are in the JSON report)

Totals over the 11 runnable scenarios (c4 does no work):

| Path | Obligations re-assessed | Seed searches (measured) | Searches in run counters | Structural action searches | Passage reads | Passages indexed | Thai index rows written | Structure nodes written | Wall s | Provider requests | Paid model calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| selective | 23 | 32 | 32 | 13 | 29 | 41 | 41 | 26 | 5.36 | 0 | 0 |
| full in place | 64 | 64 | 64 | 32 | 60 | 41 | 41 | 26 | 9.16 | 0 | 0 |
| full scratch | 64 | 64 | 64 | 32 | 60 | 221 | 221 | 181 | 12.90 | 0 | 0 |

Example, a1 (one cited annex edited):

| Path | Obligations | Seed searches | Action searches | Reads | Passages indexed | Wall s |
|---|---|---|---|---|---|---|
| selective | 2 | 3 | 1 | 3 | 3 | 0.37 |
| full in place | 6 | 6 | 3 | 6 | 3 | 0.76 |
| full scratch | 6 | 6 | 3 | 6 | 20 | 1.11 |

What the numbers support:
- On these fixtures the selective path re-assessed **23 of 64** obligations (36%). It ran 32 of 64 seed searches, 13 of
  32 structural action searches and 29 of 60 passage reads.
- Indexing work is the same for the selective path and a full rerun in place. Both index only the changed version
  incrementally, with no full derivative rebuild. A rebuild from scratch indexes the whole corpus (221 passages against 41).
- Wall time was 5.4 s for selective, 9.2 s in place and 12.9 s from scratch. This is one run on one PC; the timings
  include store copies and Python overhead and are not a benchmark.
- Model and provider work was **zero on every path**. Any provider-client request would have raised; it raised none.
  The run counters report no paid or remote call, and no `provider_usage` row was written.

The savings are measured for these fixtures only: 2 candidates, at most 6 obligations, documents of 1 to 4 passages.
They are not a claim about real corpora. The ratio depends on how many obligations share the changed candidate, and the
invalidation stays candidate-wide (see the limitations).

## Defects found

**D1: re-validation ignored scope-dependent structural decisions. Fixed.**
- `_process_revision` reused a result when its seed search returned the same passages and the result rested on no
  structural action (no `acquisition_scope` dependency).
- But the P4-T03 decision itself reads the candidate's scope. A reference that had no target, was ambiguous or was in
  the pool, or a gap that took no action, can change when another member changes.
- Reproduced by **b4** (an unrelated member now holds the `Annex D.` unit that Clause 4 cites) and **c1** (a new member
  holds it). In both, the full rerun resolves the edge and records one `resolve_reference` action with the annex unit as
  context. The selective path reused the old "no target" decision.
- Outcome and citation were equal; the explanation, the search receipt and the acquisition decision differed. The
  original run (`--without-scope-fix`) shows `MISMATCH_SELECTIVE` for b4 and c1, with `missed = C1/S1`; this is also
  pinned in `test_harness_detects_the_original_reuse_defect_when_the_fix_is_disabled`.
- **Fix** (`core.py`): a result is re-acquired, not re-validated, unless its recorded decision had no gap and no
  reference or binding candidate. A result with no receipt is also re-acquired.
- Why this is sufficient: gap detection reads only the seed pool, except reference resolution and search anchors and
  targets, which read the scope. With an identical pool, a decision with no candidates and no gaps cannot change.
- Cost: S1 (which has an unresolved reference) is now re-acquired whenever its candidate changes. This is the extra
  over-invalidation in a1, a3, b1, b3 and c2.

**Work accounting: a discarded verification search was hidden. Fixed.**
- `_process_revision` ran the verification search before deciding to re-acquire, then threw it away. That search was
  not in the run counters: in the original run of a1, the meter measured 4 seed searches against 3 counted.
- The search now runs only for a reuse candidate, and measured and counted searches are equal in every scenario. The
  change affects no evidence.
- One discarded search remains: a reuse candidate whose hits changed is searched once and then re-acquired. That search
  is still not counted. No scenario here triggers it. It is a remaining accounting gap.

**D2: a sibling-anchored action depends on history. Fixed on 24 Nov 2026 by policy 2.1.0 (owner decision D25).**

*Fix (D25).* The owner chose remedy 1 together with 2: policy `ptp-structural-acquisition/2.1.0` (pinned
`b632a2ca…6df4`) changes only the anchor rule (S1, new S1a). Every other rule is the 2.0.0 text verbatim.
- When an obligation's own eligible seed pool is empty, the seed searches of the candidate's other active requirements
  are run on the current corpus in the same run. A seed already searched in the run is reused.
- Each other requirement, in requirement-id order, votes once for the source version of its first eligible seed unit.
  The anchor is the source version with the most votes, ties by source id and then version id.
- Stored assessments, citations and earlier runs are never read. The recorded anchors are the voting seed units
  (`kind: sibling_seed_unit`, with their requirement id), at most 3.
- Requirements that have seed hits are unchanged: they still anchor on their first seed unit, and every other gap,
  reference and action rule is the same.
- 2.0.0 stays pinned and selectable (`acquisition: {"policy": "ptp-structural-acquisition/2.0.0"}`), for reproduction
  only. Runs, receipts, the run setup record, the capability record and Compare report the policy actually used.
- Tests: the strict xfail now passes as a normal test. New tests cover the following:
  - permuting requirement ids (the no-hit requirement sorting before or after its sibling) gives identical evidence
    signatures;
  - a second full run with no change reproduces the first;
  - the anchor step never reads stored citations (they are deleted before a rerun, and the receipt is unchanged);
  - the permutation and rerun tests also run under 2.0.0 and still show the dependence described below, and the
    harness reproduces d1 as MISMATCH_HISTORY under 2.0.0.
- Limits of the fix:
  - A sibling seed search that falls back from hybrid to lexical runs on a copy of the run's retrieval context, so a
    dense-channel failure inside it does not switch the rest of the run to lexical. No scenario here uses hybrid
    retrieval.
  - The run cap `max_structural_actions` is still applied in obligation order (a budget rule, not an anchor rule).
  - A revision settles with the default policy (2.1.0), even if the last full run explicitly asked for 2.0.0.

*Original finding (23 Nov, policy 2.0.0):*
- Under P4-T03 policy `ptp-structural-acquisition/2.0.0`, a requirement with no hit anchors `search_within_source` on the
  source most cited by the candidate's *current* assessments of other requirements.
- Those assessments come from the store's history and from the order of requirement ids within a run. So the result
  depends on what was committed before, not only on the corpus.
- **d1** shows an evidence-level difference. A1 ("annual application fee") sorts before E1:
  - from scratch, A1 runs before any E1 result exists and searches the whole candidate scope, citing `pricing#p0003`;
  - after any change in the candidate, both the selective path and a full rerun in place re-run A1 while E1's result
    exists, take `search_within_source` on `profile`, and cite `profile#p0004`.
- The same mechanism makes a second full rerun differ from the first, even with no change.
- Tracked by a strict-xfail test (until 24 Nov).
- Possible remedies, which needed a decision because they change the pinned policy:
  1. anchor only on an order-independent signal, such as sibling *seed hits* recomputed on the current corpus;
  2. run all seed searches before any action (a two-pass run);
  3. keep the rule and document the order dependence.

**D3: no corpus removal. Product gap.**
- The engine has no operation that removes a source from the corpus. `ingest_document` only adds a source or a new
  version, and no `remove_*`, `delete_*`, `retire_*` or `archive_*` source method exists.
- Removal therefore cannot be revised selectively or checked; c4 is reported as NOT_SUPPORTED.
- If removal is added, it needs the same invalidation as an addition (every result of that candidate rechecked), plus
  `needs_review` for results that cite the removed source.

## Not covered

- **Real corpora:** owner documents, patents, Thai PDFs and scanned or rotated pages were not used. The fixtures are small
  English Markdown files.
- **Thai text:** the Thai analyzer was active, but no Thai-language scenario was run. P4-T03's Thai `ข้อ ๔(๒)` revision
  is covered by `test_structural_acquisition.py`.
- **Hybrid (dense) retrieval and index-generation switches:** not exercised. No embedding profile was configured.
- **Baseline-mode projects:** not covered. A revision always settles with the default structural mode, even when the last
  run was a baseline run.
- **Budget limits:** no scenario reaches the per-run caps (`max_acquisition_actions` 12, `max_source_reads` 24). A full
  run that hits a cap while a selective run does not would differ.
- **Over-invalidation is by design:**
  - any change in a candidate rechecks every result of that candidate (`search_scope` covers all its current sources);
  - results that rest on a structural action are always re-acquired.
  This is correct but not minimal (a3: nothing changed, two obligations re-acquired).
- **Requirement edits, archive and restore** (P4-T01b) were not part of the change set here.
- **Wall times** come from single runs and are not a benchmark.

## Gate (24 Nov 2026, policy 2.1.0)

- `tests/test_p4_t04_selective_revision.py` and `tests/test_structural_acquisition.py`: all pass. The D2 strict xfail is
  now a normal passing test.
- Full suite with pypdf and PyThaiNLP: 2696 passed, 8 skipped and 1 xfailed (the pre-existing one). There were 8
  failures, exactly the 8 known SACR r2/r3 supervisor budget tests.
  - A first run during a network outage also failed `test_requirement_lifecycle.py::test_http_archive_restore_routes_and_guards`
    with a loopback `ConnectionAbortedError` (WinError 10053).
  - That file passed when run alone, and the clean rerun above passed it.
- `python scripts/ptp_run.py --smoke`: 15/15 PASS. Sample projects keep acquisition mode `off`.

## Gate (23 Nov 2026)

- New tests: `tests/test_p4_t04_selective_revision.py`: 11 passed, 1 xfailed (D2).
- Full suite with pypdf and PyThaiNLP (`python -c "...sys.path.append(<repo>/.venv/Lib/site-packages)...pytest.main(['-q',
  '-p','no:cacheprovider'])"`): 2664 passed, 8 skipped and 2 xfailed (the pre-existing one and D2). There were 8 failures,
  which are exactly the 8 known SACR r2/r3 supervisor budget tests
  (`test_budget_cannot_use_nonfinite_inflated_or_erased_cost[nan|inflated|erased|insufficient]` in r2 and r3).
- `python scripts/ptp_run.py --smoke`: 15/15 PASS. The G01 sample path is unchanged: sample projects keep acquisition
  mode `off`, so the new rule does not apply to them.
