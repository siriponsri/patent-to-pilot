# TRACKA-CORE | Prospective CPU preparation

## Protocol recorded before execution

The governing [registration](https://doi.org/10.17605/OSF.IO/P2SMD) includes approved updates [1](../OSF-UPDATE-SHEET.md), [2](../OSF-UPDATE-2-SHEET.md) and [3](../OSF-UPDATE-3-SHEET.md). The [audited preregistration](https://github.com/siriponsri/patent-to-pilot/blob/bef62d64/docs/loe-bench/PREREGISTRATION.md#track-a-prospective-protocol) places Track A retraining after the [GATE](GATE.md) PASS and the [SCORE](SCORE.md) disposition. The third update concerns exploratory C9 training timing. Track A is a prospective replication.

Consider January 1 cutoffs from 1995, the start in the original Track A runner, through the S0 year. Admit every window whose entire 12- or 24-month label period has closed by t0 and whose FDA ZIP meets the retained six-calendar-month freshness and exact-availability rule. This applies K20's rejection of the NBER expansion and includes newly eligible years omitted from the original development and C′ split. Establish training labels independently from the pinned S0 source and the FIX2c identity, following the registered first final original ANDA endpoint. Keep the protected C′ projections, labels, score exports and seal authorization outside this execution.

At t0, select every dated original NDA history with dated TYPE 1 eligibility and no first final original ANDA by t0. Keep unlisted and missing-evidence histories in both horizons. Use the registered graph v1, K07 presentations, B1 and logistic models, five-fold drug-group calibration on the latest eligible TRAIN cutoff, and the frozen diagnostic policy. Apply B3 to the original S0 snapshot's recorded expiry dates. Its registered output is binary with no fitted calibration or diagnostic policy. Form queues on native scores with `floor(N/5)` expected slots and uniform inclusion probabilities at a boundary tie.

Use the frozen archive selectors for Orange Book and Paragraph IV coverage. Use the pinned L1 and L1e renderers on the identical ordered t0 roster. C9 receives the same 24-month L1e messages and a separate provenance envelope. Keep source locators and per-drug outputs private.

## Result

**PASS.** The [core manifest](../../../loe-bench/data/TRACKA_CORE_MANIFEST.json) records code revision `6bd0ac682b01fe0c82166a1e0d1af4d1efeb6d6c`, cutoffs, input digests, availability proof, training and model summaries, queue boundaries, score distributions and all data artifact hashes. Its canonical LF SHA-256 is `6497ab59ba41b0429a6169d5118c6afd14680233076a6a6693c03599d0176628`.

Of 2,290 histories with a dated original NDA by t0, 1,469 had dated TYPE 1 eligibility. Removing 818 histories with a first final original ANDA by t0 left **651** forecasts at each horizon. The common roster includes 29 low-confidence identities and 29 histories without a linked presentation in the selected FDA edition. These counts measure different properties.

| Horizon | Eligible TRAIN cutoffs | TRAIN rows / events / drugs | Latest inner cutoff and rows / events | t0 roster | Expected slots per arm |
| --- | --- | --- | --- | ---: | ---: |
| 12 months | 2010 and 2012–2025 | 8,513 / 332 / 954 | 2025-01-01, 620 / 19 | 651 | 130 |
| 24 months | 2010 and 2012–2024 | 7,893 / 618 / 922 | 2024-01-01, 615 / 46 | 651 | 130 |

All windows start on January 1. The pinned inventory supplies no eligible FDA ZIP for 1995–2009. The 2011 edition is stale. Later candidates beyond the table have unclosed label windows. The runner retains both classes and all eligible rows in each admitted TRAIN window. For B1, M1 and M3, it fits whole-drug out-of-fold calibrators at the latest TRAIN cutoff, refits the native models on all admitted TRAIN rows, and writes calibrated risks and diagnostic actions. The B3 snapshot covers 412 roster histories. B3 has a binary native score, and its calibration and policy fields are null under the registered recipe.

| Horizon | B1 boundary slots / tied histories | B3 boundary slots / tied histories | M1 boundary slots / histories | M3 boundary slots / histories |
| --- | ---: | ---: | ---: | ---: |
| 12 months | 6 / 25 | 130 / 310 | 1 / 1 | 1 / 1 |
| 24 months | 18 / 32 | 130 / 320 | 1 / 1 | 1 / 1 |

The queue files encode the expected inclusion of each row. The verification reconstructed all eight allocations independently and reproduced every calibrated value using the saved coefficients.

## Evidence boundary

The card used the eight local S0 files whose SHA-256 digests match the manifest at the existing `loe-S0-input-20261127` tag, the digest-matched GSRS identity export, and the pinned Orange Book, PIV and court evidence. The S0 fetch time was 2026-11-27 10:23:14 UTC. The runner denied Python socket operations, validated the selected historical edition bytes and left the retrospective scoring authorization unset. It derived mature TRAIN labels from S0 bytes. It accessed zero protected C′ projections or per-row C′ score exports and fetched zero post-t0 outcome sources.

At t0 the frozen selector chose the 2026-07-10 FDA Orange Book ZIP, captured 2026-07-26. The 2026-11-13 local ZIP has no exact availability proof in the frozen selector. The frozen PIV archive has no fresh t0 edition. The current October PIV files were inventory-only under E6. Among the 651 histories, 23 had admitted court-based challenge evidence and 628 retained UNKNOWN. [Orange Book edition manifest](../../../loe-bench/data/OB_EDITIONS.json) · [E6](E6.md) · [E7b](E7b.md)

## Runtime and tests

Run from `loe-bench/` with Python 3.12.10 and NumPy 2.5.4.

```powershell
rtk proxy python -B scripts/tracka_core.py
```

- **PASS.** `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` ran 243 tests, 238 passed and 5 skipped, exit 0. The new fixtures cover window maturity, roster eligibility, queue ties and exact calibration and policy parity on a development fixture. The existing Purple Book tests emitted resource warnings.
- **Known failures only.** `python -m pytest` from the repository root reported 2,760 passed, 50 skipped, 1 xfailed and 8 standing SACR r2/r3 supervisor budget failures, exit 1.

## Handoff

The private package is `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/trackA/`. `SHA256SUMS` covers 12 files, including the byte-identical core manifest. All listed digests were independently rechecked. Git carries the summary manifest and receipt.

- Core predictions are in `core_predictions_12m.jsonl` and `core_predictions_24m.jsonl`, joined by `(key, t0, horizon_months)` to `roster.jsonl`. The reconstructable B1, M1, M3 and calibration parameters are in `fitted_models.json`.
- L1 and L1e each have 1,302 rows. Use `manifest.json`, `L1DEV_inputs.jsonl` and `L1E_inputs.jsonl` with the pinned [L1/L1e consumer](../../../loe-bench/scripts/scorellm_gpu.py). The `*_messages.jsonl` files capture the exact rendered pairs. The local consumer verified both input and rendered-message hashes and common order.
- C9 uses `C9_track_a.json` and its projection digest in the core manifest with the [paired predictor](../../../loe-bench/c9/predict.py). The envelope carries per-row dated provenance. Ordered keys and rendered messages exactly match the 651-row 24-month L1e subset. CPU verification with the pinned Qwen revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` and Transformers 4.55.2 measured 598–872 tokens per prompt against the 2,048-token limit. The ordered token-ID JSONL digest is `9b54256a64e390dbce5450a893e867cb1a5fb74b142861d82814cd547347d1a8`.

The later freeze card adds quality-gated L1/L1e and eligible paired C9 predictions, then applies the registered freeze and timestamp procedure before 2027-01-31 at 23:59 UTC. At card close, exploratory inference and the external prediction freeze are **NOT_RUN**. The main planner owns review and lane handoff and memory integration.
