# FIX1 | CP1 code corrections

**Result** DONE on `loe/FIX1` from `3bb3cc68`, subject to Orchestrator review.

## Defects and verification

Base locators are at `3bb3cc68`. Regression names are in [test_fix1.py](../../../loe-bench/loe_bench/tests/test_fix1.py).

| Defect and base locator | Fix | Regression |
| --- | --- | --- |
| 1. Whole-snapshot feature flags and NME cohort membership. `dataset.py:44–70,81–95,112–113`. | Record the earliest dated approval evidence for each flag. Apply NME eligibility at each cutoff. Dated products added after the original approval cannot change the original ingredient key. Routes require an explicit product approval date. | `test_future_invariance_of_features_cohort_and_labels`, `test_undated_products_and_orig_submissions_do_not_supply_flags` |
| 2. Incomplete follow-up favored positives and could admit post-availability events. `dataset.py:101–120`. | Require `t + h <= data_end` before considering either class. An eligible positive is the first observed final original ANDA approval in `(t, t + h]`. The existing `ORIG`/`AP` distinction excludes `TA`. | `test_complete_follow_up_for_both_classes_and_first_final_only` |
| 3. Same-day label leakage and overlapping split boundaries. `dataset.py:124–131`. | Require strictly ordered split boundaries and purge windows ending on or after the next split's first cutoff. With both validation boundaries supplied, return train, validation, test and the combined purge count. The two-way return shape is retained. | `test_exact_embargo_boundary_and_overlapping_bounds`, `test_three_way_embargo_boundaries_and_invalid_dates` |
| 4a. AURC was tied to the 0.5 probability rule. `metrics.py:43–57`. | Accept explicit scores and graph actions. Count coverage against all eligible rows while ranking only answered rows. Integrate the right-step curve up to achieved coverage. An all-abstain policy has undefined AURC. | `test_explicit_ranking_and_policy_coverage` |
| 4b. AURC ties inherited input order. `metrics.py:47–51`. | For a tied group with `m` rows and `e` errors, the expected added errors at prefix `j` are `j * e / m`. Use those expectations at every prefix. | `test_expected_aurc_invariant_to_tie_permutations` |
| 4c. Bootstrap handled one arm. `metrics.py:84–102`. | Compute A minus B on the same whole-cluster draw for both arms with a fixed seed. Return percentile interval bounds and the number of non-finite draws. | `test_paired_cluster_draws_and_invalid_counts` |
| 4d. ECE accepted invalid observations and discarded bin counts. `metrics.py:10–20`. | Require aligned non-empty probabilities and binary labels, probabilities in `[0, 1]`, and a positive bin count. Return the estimate and per-bin counts, with the final bin closed on the right. | `test_ece_validates_inputs_and_returns_bin_counts` |
| 5. Empty date lists implied OPEN and every BLOCKED verdict forced a negative call. `evidence_graph.py:25–32,40–59`. | An absent or empty date list supplies UNKNOWN evidence. BLOCKED with `p_model >= hi` sets `conflict` and refers to the evaluator by default. An explicit policy can override that action. BLOCKED below `hi` predicts no entry. | `test_missing_evidence_is_unknown`, `test_blocked_conflict_refers_by_default_at_high_boundary` |
| 6. Evidence-action rates and the prior were passed as abbreviated, positional arguments with a hardcoded prior at the decision call site. `voi.py:29–45,63–104,118–129`, `evidence_graph.py:57–59`. | Name the reveal probabilities and prior truth probability separately through the decision and VoI functions. The default reveal rate for challenge evidence is 0.3 and the default prior truth probability is 0.5. Report the VoI of the requested leaf. The old math already distinguished reveal and truth internally. | `test_voi_reveal_rate_and_truth_prior_have_separate_roles` |
| 7. Freeze trusted unchecked files, trained through the latest observed event, ignored the snapshot cutoff and rounded an implicit ensemble. `trackA_freeze.py:19–45`, `dataset.py:134–155`. | Verify the manifest and its file hashes before loading prediction inputs. Reject source or fetch dates after `t0` and use the earlier verified date to cap training follow-up. Determine snapshot eligibility at `t0` and keep expiries published with S0. Write one full-precision column per explicitly supplied arm. | `test_snapshot_filters_by_cutoff_and_keeps_future_expiration`, `test_freeze_refuses_newer_manifest_fetch_or_hash_mismatch`, `test_freeze_requires_all_used_files_to_be_manifested`, `test_freeze_only_closed_windows_and_full_precision_per_arm`, `test_cli_freezes_only_explicit_baseline_arms` |

## Evidence

- From `loe-bench/`, run `python -m unittest discover -s loe_bench/tests -t .`. Base suite on Python 3.12.10 returned `Ran 34 tests ... OK`. The corrected suite returned `Ran 51 tests ... OK`, exit 0.
- Failing-before check loaded the base `dataset`, `metrics`, `voi`, `evidence_graph` and `trackA_freeze` modules into a Python process from `git show 3bb3cc68:loe-bench/loe_bench/<module>.py`. It then ran `unittest.defaultTestLoader.loadTestsFromName("loe_bench.tests.test_fix1")` against those modules. All 17 tests were red, with 8 assertion failures and 11 errors including subtests for APIs absent at base. On the first post-change run, one bootstrap fixture had the valid and invalid seeded draw counts reversed and compared floating-point differences exactly. The fixture now records the enumerated draws and compares interval endpoints with tolerance.
- All 34 original cases remain. Updated expectations encode strict embargo, the ECE result object, dated snapshot input, and explicit exclusivity evidence where a graph leaf is intended to be known. The legacy BLOCKED test now exercises the no-conflict branch. The legacy baseline entrypoint reads the numeric `ece` field of the new result.
- The repository-level `python -m pytest --tb=short --basetemp <fresh-short-path>` returned `8 failed, 2760 passed, 50 skipped, 1 xfailed, 2 warnings` in 291.16 seconds, exit 1. All failures match the eight allowed SACR r2/r3 supervisor budget cases. [Repository test policy](../../../AGENTS.md) · [Prior S4 verification](../../evidence-scope/receipts/S4-integrated-verification.md)

## Count protocol

Compare base `3bb3cc68` and FIX1 on the same locally pinned Drugs@FDA files from E1. Use annual January 1 cutoffs from 1995 through 2014, the training grid from the baseline entrypoint, and the S0 snapshot date of 2026-11-27 as the common label-availability date. Count NME-only candidate rows and retained training rows at 12, 24 and 36 months using a 2017-01-01 embargo boundary. Count distinct enrolled keys per horizon and the NME keys approved by the last training cutoff and by S0 before the no-prior-ANDA criterion. Read the base dataset implementation from Git for comparison. Emit only aggregate counts. Performance scoring and real-data baseline or freeze execution are outside this task. [E1 input freeze](E1.md) · [S0 manifest](../../../loe-bench/data/S0_INPUT_MANIFEST.json)

The SHA-256 values of `df_nda.jsonl` and `df_anda.jsonl` matched S0. The entity table had 2,520 keys before and after. The approved NME cohort had 1,092 keys at 2014-01-01 and 1,495 keys at S0 in both versions.

| Horizon | Candidate rows before → after | Retained train rows before → after | Distinct retained keys before → after | Embargoed rows before → after |
| --- | ---: | ---: | ---: | ---: |
| 12 months | 10,861 → 10,861 | 10,861 → 10,861 | 903 → 903 | 0 → 0 |
| 24 months | 10,861 → 10,861 | 10,861 → 10,861 | 903 → 903 | 0 → 0 |
| 36 months | 10,861 → 10,861 | 10,861 → 10,299 | 903 → 880 | 0 → 562 |

From `loe-bench/`, pipe the following Python to `python -`. It reads two source files and prints only aggregate counts.

```python
import hashlib
import json
import subprocess
import sys
import types
from datetime import date
from pathlib import Path

from loe_bench import dataset as after

raw = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/raw-20261127")
manifest = json.loads(Path("data/S0_INPUT_MANIFEST.json").read_text())
data_end = date.fromisoformat(manifest["t0"])
for entry in manifest["files"]:
    path = raw / entry["raw_file"]
    if path.name in {"df_nda.jsonl", "df_anda.jsonl"}:
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], path.name

name = "loe_bench._base_dataset"
before = sys.modules[name] = types.ModuleType(name)
before.__package__ = "loe_bench"
source = subprocess.check_output(
    ["git", "show", "3bb3cc68:loe-bench/loe_bench/dataset.py"], text=True)
exec(compile(source, "3bb3cc68:dataset.py", "exec"), before.__dict__)
last, embargo = date(2014, 1, 1), date(2017, 1, 1)
cutoffs = [date(year, 1, 1) for year in range(1995, 2015)]
for title, module in (("before", before), ("after", after)):
    entities = module.build_entities(raw)
    cohorts = [
        sum(e.nda_first is not None and e.nda_first <= cutoff
            and (e.flag_at("nme", cutoff) if module is after else e.nme)
            for e in entities.values())
        for cutoff in (last, data_end)
    ]
    print(title, "entity_table", len(entities), "NME_cohorts", *cohorts)
    for h in (12, 24, 36):
        rows = module.build_samples(entities, cutoffs, h, data_end)
        train, _, dropped = module.time_split(rows, last, embargo)
        print(h, "candidates", len(rows), "train", len(train),
              "keys", len({r["key"] for r in train}), "embargoed", dropped)
```

## Failures and limitations

- Drugs@FDA retains the current status and effective date for each submission. `AP` marks full approval and `TA` marks tentative approval. The event is the earliest retained dated `ORIG/AP` among linked ANDAs. This source cannot recover superseded status history or prove that an approval led to a commercial launch. [openFDA field reference](https://open.fda.gov/fields/drugsfda_reference.pdf) · [FDA AP/TA definitions](https://www.fda.gov/media/168926/download?attachment=)
- The pinned Drugs@FDA product records have no product-level approval date. Route indicators therefore remain zero on those files, meaning the dated evidence is unavailable. The ingredient linkage still uses the application's undated product list as a proxy where explicit product dates are absent. Historical changes within that list cannot be reconstructed from S0. Dated future feature records and outcomes beyond the label window leave prior rows unchanged. A first final ANDA inside an earlier row's observation window supplies that row's outcome by design.
- The AURC convention uses the integral up to each policy's achieved coverage. Its magnitude depends on that coverage. The confirmatory protocol still needs to declare how arms with different maximum coverage will be compared.
- The Track A CLI exposes implemented `B0` through `B3` and requires a repeated `--arm` argument in column order. `freeze_predictions` accepts a mapping of locked arm identifiers to predictors for later arms. G2 preregistration, real arm runs, external timestamping and an actual G3b freeze remain pending. No arm was inferred from the historical example CSV. The fixture CLI test used `--arm B3 --arm B0`.
- The pre-existing Purple Book test and reader emitted `ResourceWarning` for unclosed fixture files in both unittest runs. No production baseline or freeze was run on real data. The real-data check emitted only counts for the declared training grid.

## Next action

The Orchestrator reviews this branch and receipt before integration. T7 should audit the current ingredient linkage against FDA first-generic records on its approved development cases. Subsequent modeling and preregistration cards can use the corrected split and metric interfaces once released.
