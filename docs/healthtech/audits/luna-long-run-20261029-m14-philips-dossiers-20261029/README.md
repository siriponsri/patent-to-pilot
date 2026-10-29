# HT-M14 Philips local dossier pipeline

- Run ID: `luna-long-run-20261029-m14-philips-dossiers-20261029`
- Date: `2026-10-29`
- Base commit: `7dae0a8ac9ff790714d640e94889459529512073`
- Tested code commit: `c6494370fad1c263eed169a7bd6a8c5718ed3427`
- Status: `PASS_OFFLINE_ENGINEERING_DOSSIERS`

## Outcome

This package adds a committed Philips-specific local dossier adapter and runner for the frozen `ht-philips-cardiovascular-20261029-r2` cohort. The adapter reads only the frozen runtime/source-registry/raw inputs and the reviewed M13 rights matrix, rejects runtime/source-registry/raw-file mutation and evaluator leakage, and reconstructs product-level disclosure evidence without converting unlisted pairs into negatives.

The committed-code run completed three inspectable dossiers:

| Case | Disclosed links | Patent rows | History | Output |
|---|---:|---:|---|---|
| AngioSculpt Scoring Balloon | 1 | 1 | versions 1 and 2 | `results/healthtech/ht-philips-dossiers-20261029-r3/HT-DEV-PHILIPS-ANGIOSCULPT-SCORING-BALLOON/` |
| Thromcat Thrombectomy System | 2 | 2 | versions 1 and 2 | `results/healthtech/ht-philips-dossiers-20261029-r3/HT-DEV-PHILIPS-THROMCAT-THROMBECTOMY-SYSTEM/` |
| Turbo-Elite Laser Catheter | 4 | 4 | versions 1 and 2 | `results/healthtech/ht-philips-dossiers-20261029-r3/HT-DEV-PHILIPS-TURBO-ELITE-LASER-CATHETER/` |

The run recorded three actual search calls, zero returned lexical candidates, zero provider calls, and USD `0.00` paid cost. Each case generated local JSON, English and Thai exports, source views, case manifests, resource receipts, and two history versions. The run manifest SHA-256 is `e0acaa3d9852ddee96bce73d9b7527c77998a613925c81feca60f1aeb0837f60`; the receipt SHA-256 is `1bdfd218f90e681892723544fbe38cdcde81fd2c8e09c10de9654e019c2321af`.

## Reproduction

```text
rtk proxy python -B scripts/healthtech/run_philips_dossiers.py --cohort results/healthtech/ht-philips-cardiovascular-20261029-r2 --output results/healthtech/ht-philips-dossiers-20261029-r3 --rights-matrix docs/healthtech/audits/luna-long-run-20261029-m13-philips-expansion-20261029/rights-matrix.json --code-commit c649437
```

The valid run uses the producer's patent normalization contract, `content_hash({"title", "abstract", "claims"})`. Earlier `r1` failed because the adapter used an incorrect hash assumption. Corrected working-tree `r2` passed, and `r3` repeated the same validation with the committed code.

## Verification

- Synthetic Philips dossier and cohort regressions: `10/10` passed.
- Compile checks for the adapter, runner, and test: passed.
- Broader focused HealthTech suite covering repairs, pre-live controls, Cook, Philips dossiers, and Philips cohort: exit `0`; only the existing `fitz` deprecation warning appeared.
- M1 current-head revalidation remains linked at `docs/healthtech/audits/luna-long-run-20261029-m1-revalidation-20261029/verification.json`, with output SHA-256 `5e301ad332f2c5fb6ef3935149a5962f4d500ff2e00dfeee23fbfe1e67314703` and zero network/provider/neural calls.

The authored source hashes at the tested code commit are:

- `src/patent_to_pilot/healthtech/philips.py`: `e72dd6770e4b700a1571cb307483913e6864a4d0173619e0de59a77f0d764370`
- `scripts/healthtech/run_philips_dossiers.py`: `9ac9d8939e647ee0f9ea6a94d56ab37457e497522cf37760c81dfd32875303c5`
- `tests/test_healthtech_philips_dossiers.py`: `8a03848ecfc5cac128e47eeee506ebcf48117db01b872cb89f32a30e051796f9`

## Rights and limits

The dossier artifacts are local research outputs. Philips marking material and Google-derived patent text remain local-only; the reviewed rights matrix documents policy decisions but does not grant redistribution rights. The dossier links are product-level disclosed associations, not claim-level semantic relevance judgments. Unlisted device-patent pairs remain unjudged. This package does not support exhaustive recall, stable generalization, clinical suitability, FTO, patent validity, investment merit, user validation, or publication readiness.

## Boundaries and next step

Implemented: frozen-input validation, typed source-policy enforcement, product-level disclosure reconstruction, local dossier exports, source views, history, receipts, and offline regression coverage. Mocked or not run: live provider inference, paid inference, rights-cleared semantic adjudication, statistical significance, clinical/FTO review, user/commercial validation, and public raw-data release.

The next discriminating step remains a rights-cleared semantic device-patent judgment source with explicit labels, source revision/hash, rights policy, adjudicator role, exact locators, multiple independent company/family groups, and a predeclared untouched final holdout. Preserve the current denominator and unjudged pairs while keeping paid HT-B4, Bridge, deployment, outreach, and Claude UX/UI paused.

See [`verification.json`](verification.json), [`experiment-ledger.json`](experiment-ledger.json), and [`NEXT_ACTIONS.md`](NEXT_ACTIONS.md) for the machine-readable record and continuation handoff.
