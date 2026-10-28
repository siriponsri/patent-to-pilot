# HT-G1 / HT-G2 Closeout Receipt

**Run date:** 2026-10-28
**Starting HEAD and origin/main:** `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3`
**Release candidate before this receipt:** `679ff5a`
**Scope:** local public acquisition, local model execution, evaluator correctness, clean offline verification, and guarded HT API boundary. No paid provider, deployment, credential read, or outreach.

## Status

| Root item | Status | Evidence |
|---|---|---|
| HT-G1 data/source registry and usable development cohort | `PARTIAL` / Bridge `BLOCKED_LOCAL` | `docs/healthtech/research/BRIDGE_RIGHTS_COHORT.md`; tracked manifest `data/manifests/healthtech/ht-public-cohort-20261028.json`; local source registry, runtime/evaluator files, groups, split and data card under `results/healthtech/ht-public-cohort-20261028-r1/` |
| HT-G2 evaluator correctness | `PASS` for accepted development contract | 40 focused HealthTech tests; SciFact differential `results/healthtech/g1-g2-scifact-differential-r2/receipt.json`; HT-T1 real-data validation in `ht-real-baselines-20261028-r4/evaluator_validation.json` |
| HT-G2 real development baselines | `PARTIAL` / no final generalization claim | `results/healthtech/ht-real-baselines-20261028-r4/` with raw rankings, attempts, per-device/group metrics, costs, and headroom |
| Clean engineering verification | `PASS` | Clean tracked worktree at `679ff5a`: 275 tests, 0 failures/errors/skips, 0 network attempts, 0 credential-file reads |
| HT API boundary | `DRY_RUN_NOT_EXECUTED` | Guarded dry-run returned no response and zero network/provider calls |

## G1 evidence

The permitted independent development cohort contains 3 named Abbott cardiovascular devices, 41 unique canonical U.S. patent documents, and 61 product-level disclosed pairs. The runtime/evaluator separation is explicit: `runtime.json` contains device inputs and patent text; `evaluator/references.json` contains the disclosure relations and was opened only after rankings and runtime predictions were written.

Tracked cohort hashes:

- runtime: `6414ae59d79972fbffbf5557d378156a2c5b6daae7ff061ce3121515e58a5cad`
- evaluator references: `a0f15c9accbe374ce9e918c09398869d8937096cd6f6809f94ece4f7e3fcd7c2`
- patent universe: `642a3f5873f2a4b2e8f5321c705f3dd442440cfd8382f088f96b2a1b9986152b`
- eligible device cohort: `b92b50716599ad6ea3cdeb5b6a692990a52ae8dd113bfc0bb5cad2cdd2148715`
- acquisition manifest: `6e793d3b40da983c8829ee88ed96e42df0d5b65109d4e6c8144901d2f6d42787`
- acquisition accounting: 63,333,809 transferred bytes; 64,388,112 stored bytes

Groups and split evidence is explicit: MitraClip/TriClip form one exact-patent connected component; Tendyne is separate; all three devices share the Abbott company group; no family mapping is assumed; all queries are development-only with no final holdout.

The Bridge-MedDevKG branch remains `BLOCKED_LOCAL`. At pinned commit `f3990a207949f25012d1070a08ac303e140387e6`, the README snapshot SHA-256 is `f8518e94eceadb9dd6640128399072243beaf2b039981b498d2635f2862e4b36`; no verified repository/data license, per-link disclosure provenance, or recoverable final split was established. The Abbott cohort is not relabeled as Bridge gold.

SciFact is retained as a separate evidence-verification component. Its pinned archive is 3,115,079 bytes with SHA-256 `11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be`; the release contains 5,183 corpus documents, 809 train claims, 300 dev claims, and 300 unlabeled test claims. It is not device--patent gold.

## G2 results

All five methods ran on the same 3-device / 41-patent universe, with candidate and rerank depth 41, primary K=20, and secondary K=10/50. No query failed. Exact macro known-link Recall@K is in `development_headroom.json`.

| Method | R@10 | R@20 | R@50 | Query calls | Rerank pairs |
|---|---:|---:|---:|---:|---:|
| HT-B0a company control | 0.208744 | 0.442739 | 1.000000 | 3 | 0 |
| HT-B0b BM25 lexical | 0.346933 | 0.662242 | 1.000000 | 3 | 0 |
| HT-B1 dense + fixed fusion + local reranker | 0.298908 | 0.493687 | 1.000000 | 3 | 123 |
| HT-B2 fixed multi-query | 0.287703 | 0.584785 | 1.000000 | 9 | 369 |
| HT-B3 observable heuristic | 0.284415 | 0.498802 | 1.000000 | 6 | 246 |

The result is a valid development null/negative finding: BM25 exceeds the fixed dense/reranker hybrid at K=20 on this cohort, while the simple heuristic is only 0.005115 macro recall above B1 and costs twice the B1 query/rerank work. No superiority claim is made; the simplest useful product method remains a live option.

Resources are recorded as offline units, not dollars. B1 used 384 dense query tokens and 31,488 reranker tokens; B2 used 1,152 and 94,464; B3 used 768 and 62,976. The model snapshots total 47,442,652 bytes and are pinned in `data/manifests/healthtech/ht-models-20261028.json`; both model cards declare Apache-2.0. Model pretraining contamination and medical-domain adequacy are unresolved.

## Correctness and commands

Focused adversarial tests:

```text
rtk proxy python -B -m pytest -p no:cacheprovider tests/test_healthtech.py tests/test_healthtech_prelive.py
40 passed
```

Official SciFact differential:

```text
rtk proxy python -B scripts/healthtech/run_scifact_differential.py --official-root <pinned-temp-root> --output results/healthtech/g1-g2-scifact-differential-r2/receipt.json
PASS; 3 valid cases parity-matched
```

Real public acquisition and scoring:

```text
python -B scripts/healthtech/acquire_model_artifacts.py
python -B scripts/healthtech/fetch_public_device_cohort.py --output results/healthtech/ht-public-cohort-20261028-r1
rtk proxy python -B scripts/healthtech/run_real_baselines.py --runtime results/healthtech/ht-public-cohort-20261028-r1/runtime.json --references results/healthtech/ht-public-cohort-20261028-r1/evaluator/references.json --groups results/healthtech/ht-public-cohort-20261028-r1/groups.json --model-root data/raw/healthtech/models --output results/healthtech/ht-real-baselines-20261028-r4 --code-commit 7b15ed8 --protocol-hash 7dab96b735c70bcf60b99f191477c5add04d95c337d437c2d17b546e8b226cf2 --cohort-manifest-hash 6e793d3b40da983c8829ee88ed96e42df0d5b65109d4e6c8144901d2f6d42787
REAL_PUBLIC_DEVELOPMENT_RUN; provider_calls=0; paid_cost_usd=0
```

Clean tracked-checkout verification:

```text
rtk proxy python -B scripts/healthtech/verify_offline.py <fresh-output> --suite all
PASS; 275 tests; 0 failures; 0 errors; 0 skipped; 0 network attempts; 0 credential-file reads
```

Synthetic smoke:

```text
rtk proxy python -B scripts/healthtech/run_dossier.py examples/healthtech/synthetic-device/input.json <fresh-output>
ENGINEERING_DRAFT; 2 candidates; provider_calls=0; paid_cost_usd=0
```

Guarded API boundary:

```text
rtk proxy python -B scripts/healthtech/run_api_dry_run.py configs/healthtech/api_dry_run.json
DRY_RUN_NOT_EXECUTED; network_attempts=0; provider_calls=0; paid_cost_usd=0
```

## Remaining work

G1 is not globally complete because Bridge rights/cohort/split evidence remains unresolved. G2 is not a final scientific study because the permitted branch is development-only, has three devices from one applicant/disclosure source, and has no final holdout. HT-B4 live provider comparison, G4 adaptive evaluation, clinical/FTO analysis, deployment, UI/service work, customer validation, and publication readiness remain out of scope and `NOT_RUN`.

## Post-release revalidation

The current release pointer was revalidated on 2026-10-28 at `HEAD` and `origin/main` `3937d9debe2a27908d923a760926f52bbc43c949`.

- Focused HealthTech regressions: 40 passed.
- Clean tracked worktree, `verify_offline.py <fresh-output> --suite all`: 275 tests, 0 failures, 0 errors, 0 skipped, 0 network attempts, 0 credential-file reads, source unchanged.
- Data/model audit: cohort hashes, runtime/evaluator separation, 15 raw method-query rows, 41-document universe, 61 disclosed pairs, 12 pinned model files, and 4 SciFact release files all verified against their manifests.
- Guarded API boundary: `DRY_RUN_NOT_EXECUTED`, 0 network attempts, 0 provider calls, `paid_cost_usd=0`.
- Status is unchanged: HT-G1 and HT-G2 remain `PARTIAL`; the Bridge main branch remains `BLOCKED_LOCAL` pending rights, per-link provenance, and recoverable cohort/split evidence.
