# Luna patent-linked dossier slice audit

Run id: `luna-patent-dossiers-20261028-atomic`

Checked on October 28, 2026. Base and end `HEAD` remain `1ce0443f7e972b19942336cadcd46294bde82c41`; the worktree is intentionally dirty because unrelated owner artifacts and the tracked `AGENTS.md` edit are preserved.

This run covers the bounded backend slice requested in `docs/healthtech/LUNA_PATENT_LINKED_DOSSIERS_GOAL.md`:

- Package A: atomic committed-version publication and recovery tests.
- Package B: three Abbott public-source patent-linked dossiers.
- Package C: development-only universe, unjudged distractors, exact-overlap groups, and split freeze.

## Acceptance matrix

| Package | Result | Evidence |
|---|---|---|
| A: no partial published version | PASS | `history-after.json`; paused reader saw only version `[1]`, no visible version-2 path, final chain `[1,2]`. |
| A: same-base concurrency | PASS | `tests/test_healthtech_repairs.py`; one committed update and one stale-parent conflict remain green. |
| A: interruption/recovery | PASS | Focused tests cover before publish, after payload fsync/before publish, after publish, and age-gated staging recovery. |
| A: edit/export regression | PASS | Focused suite plus three generated histories contain version 2, user edit, JSON, English, and Thai exports. |
| B: three real patent-linked cases | PASS for local development backend | Three Abbott devices use real PMA snapshots, 41 patent documents, independently parsed Abbott disclosure evidence, BM25 hits, and disclosed-link annotations. |
| B: source viewer/history/export | PASS | Generated case artifacts and CLI source-view/export smoke. |
| C: bounded expansion and frontier | PASS for development-only freeze | 3 eligible devices, 41-document universe, 61 disclosed pairs, 62 unjudged distractor pairs, exact-overlap/company groups, no final holdout, and a fresh query-matched fixed-prefix quality/resource frontier. |
| Scientific pilot/public release | NOT_RUN | Explicitly out of scope: no paid/free remote inference, no final holdout claim, no deployment, no public redistribution, no FTO/clinical/validity/investment claim. |

## Canonical artifacts

- `history-after.json`: rerun of the prior portable publication race under the fixed implementation.
- `verification.json`: machine-readable commands, hashes, counts, boundaries, and outcomes.
- `rights-matrix.json`: source clauses, URLs, checked dates, hashes, and intended-use decisions.
- `frontier_summary.json`: sanitized r7 quality/resource frontier, group diagnostics, hashes, and uncertainty limits.
- `receipt.md`: human-readable handoff.
- `NEXT_ACTIONS.md`: continuation work; the overall HealthTech goal is not complete.

Large/raw and derived local artifacts remain outside this audit folder:

- Cohort: `results/healthtech/ht-public-cohort-20261028-r1/`
- Development freeze: `results/healthtech/ht-abbott-development-20261028-r1/`
- Baseline frontier: `results/healthtech/ht-real-baselines-20261028-r7/`
- Three cases: `results/healthtech/ht-abbott-dossiers-20261028-atomic-r3/`

Those paths are referenced by hashes and manifests here; raw third-party HTML and extracted patent text are not copied into the audit folder or staged for redistribution.

## Exact verification commands

```text
rtk python -B -m pytest -p no:cacheprovider tests/test_healthtech_repairs.py tests/test_healthtech.py tests/test_healthtech_prelive.py
PASS: 52 passed in 7.25s

rtk python -B -m compileall -q src/patent_to_pilot/healthtech scripts/healthtech
PASS: exit 0

rtk python -B docs/healthtech/audits/pepo-followup-20261028-1ce0443/reproduce_history_publication.py --output docs/healthtech/audits/luna-patent-dossiers-20261028-atomic/history-after.json
PASS: READER_SAW_COMMITTED_CHAIN

rtk python -B scripts/healthtech/freeze_abbott_development.py --cohort results/healthtech/ht-public-cohort-20261028-r1 --output results/healthtech/ht-abbott-development-20261028-r1
PASS: 3 devices, 41 patents, 61 disclosed pairs, 62 unjudged distractor pairs

rtk proxy python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-public-cohort-20261028-r1/runtime.json --references results/healthtech/ht-public-cohort-20261028-r1/evaluator/references.json --groups results/healthtech/ht-public-cohort-20261028-r1/groups.json --model-root data/raw/healthtech/models --output results/healthtech/ht-real-baselines-20261028-r7 --code-commit 1ce0443f7e972b19942336cadcd46294bde82c41 --protocol-hash f9b1fdf43d2bfd1fc94bee58e4c91738195456202dcd0f8e228af41887f938b8 --cohort-manifest-hash 6e793d3b40da983c8829ee88ed96e42df0d5b65109d4e6c8144901d2f6d42787
PASS: 5 methods, 3 devices, 41 patents, 61 disclosed pairs, 0 provider calls, frontier_diagnostics.json written

rtk python -B scripts/healthtech/build_abbott_dossiers.py --cohort results/healthtech/ht-public-cohort-20261028-r1 --protocol results/healthtech/ht-abbott-development-20261028-r1/protocol.json --output results/healthtech/ht-abbott-dossiers-20261028-atomic-r3 --code-commit working-tree
PASS: MitraClip 35/21, Tendyne 20/17, TriClip 28/23 (candidate/disclosed-link counts)

rtk python -B scripts/healthtech/view_dossier_source.py results/healthtech/ht-abbott-dossiers-20261028-atomic-r3/HT-DEV-MITRACLIP/dossier.json openfda-pma-p100009-base --field trade_name
PASS: returned the PMA trade_name source view

rtk python -B scripts/healthtech/manage_dossier_history.py export results/healthtech/ht-abbott-dossiers-20261028-atomic-r3/HT-DEV-MITRACLIP/history results/healthtech/ht-abbott-dossiers-20261028-atomic-r3/HT-DEV-MITRACLIP/cli-export-v2 --version 2
PASS: EXPORTED version 2
```

## Frontier result

The fresh r7 run reports realized local quality and resources at each observed prefix. At K=20, BM25 is the strongest one-query control (`0.662242` macro known-link recall); the fixed hybrid starts at `0.498802` and the fixed three-query schedule reaches `0.568912`. The heuristic matches the hybrid at prefix 1 and realizes only two of three queries at prefix 2, so its all-device score is `0.224293` while its reached-device descriptive score is `0.336439`.

The first query hash matches across HT-B1, HT-B2, and HT-B3 for every device. Confidence intervals and inferential group claims are `NOT_ESTIMABLE`: the slice has three queries, two exact-patent groups, one company group, unknown family mapping, and no final holdout. See `frontier_summary.json` and the full local `frontier_diagnostics.json` for the per-prefix and per-group rows.

