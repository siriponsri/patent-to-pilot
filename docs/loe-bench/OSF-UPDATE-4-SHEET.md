# OSF registration update sheet (update 4, Track A prediction freeze)

**AUDITED: YES** (main planner, 28 Nov 2026). Checks:
- The manifest LF SHA-256 recomputes to 8a78b318…c38d, and the manifest is present in tagged commit 6712f32c.
- The ten file digests and the archive digest match the TRACKA-FREEZE receipt.
- The target field exists in the registration (response key 72-61, "Secondary measures of forecasting performance").
- The Qwen2.5-7B revision matches SCORELLM.
- The repository is public, so the manifest link resolves.
- One transparency sentence was added: C9-GRPO abstained on all rows.

## Rules for the agent

1. Use only the owner's signed-in session. Never enter credentials.
2. Open https://osf.io/p2smd and choose **Update**. Preserve the existing registration and prior responses.
3. Paste the exact text below. Append the second block to the field with the specified anchor.
4. **Stop before submitting.** Show the owner the justification, appended text and attachment state. Submit after the owner types `submit`.

## 1. Justification

> This update records the prospective Track A prediction freeze and its file digests. It adds the exploratory arm specifications and external-reference metric plan. The registered H1–H3 testing sequence and one-sided alpha 0.025 are unchanged. Predictions were frozen before any post-snapshot outcome-source fetch for Track A.

## 2. Field containing “Secondary measures of forecasting performance”

Append this block at the end of the existing field.

> Track A prediction freeze for the 27 November 2026 source snapshot.
> Freeze UTC 2026-11-28T11:18:44Z. Git tag loe-track-a-freeze-20261127. Commit 6712f32cdfb1252d66e192d770deaa867808a375. Freeze manifest SHA-256 8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d. Manifest https://github.com/siriponsri/patent-to-pilot/blob/6712f32cdfb1252d66e192d770deaa867808a375/loe-bench/data/TRACKA_FREEZE_MANIFEST.json
> Prediction archive trackA-predictions.zip, SHA-256 85e9521e8cf8d6a909d1a0f7333b3f66851c95dcfaded9116ebdceb744882da2. Below are exact byte SHA-256 digests.
>
> B1 | B1_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | 03512b32026d929e8cdcce2a352bfbdafef0d90473330e7177b6e6ca36346c13
> M1 | M1_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | a89086db767ba27e8c15927138c6c2eff2d0b52217679f0bee89c18b9997edd0
> M3 | M3_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | cee7d7a4f77dd57424b7420ccb5c7b5c48dda68a067242bebe52fee45598d410
> B3 | B3_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | 06d02ec233363b16fed5673babe7ef72e4d18a5406b2ef5725a6c038a5971ace
> P1-RSF-OPEN | P1-RSF-OPEN_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | 40a44ecc1c6b9f477d16e8d638a098fc73f4801624daf4e5476ce9d614470f1f
> P2-COX-OPEN | P2-COX-OPEN_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | 2b0eff2b76a5da5968c434965c44d649469d533f4ea31485d8fb8d34d0dda29f
> L1 | L1_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | 79c3b990ec4b6c38df4861ab51a193968cd4b532290da702d8dc1d6e612e9b41
> L1e | L1e_predictions.jsonl | 1,302 rows, 651 at 12 months and 651 at 24 months | bf910f5635a3bb3c1808387924806d344c9f61ba2e1fba9294c9fcf065e4f51d
> C9-SFT | C9-SFT_predictions.jsonl | 651 rows at 24 months | cce35d54f27062e0f2eee1e6c13d1a0742a7181bfdaeed03150a8b5218936488
> C9-GRPO | C9-GRPO_predictions.jsonl | 651 rows at 24 months | 75ab8e09e5210fa841818b503eda1b2cc6b42576fa542130c83fff9c263d9de7
>
> Exploratory Track A arms are P1-RSF-OPEN, P2-COX-OPEN, L1, L1e and the C9-SFT and C9-GRPO pair. All met their technical admission rules. B3 remains the registered descriptive expiry-only comparator.
>
> P1-RSF-OPEN adapts the Hu and Hopefl random survival forest to open inputs. Fit per horizon on age, oral and injectable indicators, NCE remaining years, years to last patent expiry and both frozen expiry-missingness bits. Use 500 trees with log-rank splits, square-root feature sampling, minimum split 10, minimum leaf 5, unlimited depth, bootstrap, one thread and seed 20261127.
>
> P2-COX-OPEN adapts the Kerr and Glos Cox model to open inputs. Use age, dated orphan status, oral and injectable indicators, challenge presence and missingness, and linear first-NDA year. Standardize age and year on TRAIN only. Oral and injectable had zero TRAIN variance and were dropped under the locked rule. Use CoxPHSurvivalAnalysis with alpha 1.0, Breslow ties and baseline, up to 100 iterations and tolerance 1e-9.
>
> Both survival arms fit mature TRAIN windows separately per horizon. Divide elapsed event days by the length of the row's horizon. Censor event-free rows at 1. Native risk is 1 minus predicted survival at 1. The outcome is first final original FDA ANDA approval within the registered horizon. Compare P1 and P2 descriptively with M3 for recall at the 20% review capacity. Use 2,000 paired whole-drug bootstrap draws per horizon with seed 20261127 and rebuild the queues on each draw.
>
> L1 uses the active-moiety identity, cutoff and horizon. L1e adds dated evidence. Both use Qwen2.5-7B-Instruct revision a09a35458c702b33eeacc393d103063234e8bc28 with the registered fp16 greedy decoder, batches of eight, up to 160 new tokens and independent 180-of-200 validity and full-roster gates. Malformed outputs are referrals ranked below valid probabilities.
>
> The C9-SFT and C9-GRPO pair uses Qwen2.5-1.5B-Instruct revision 989aa7980e4cf806f80c7fef2b1adb7bc71aa306 with the matched 651-row 24-month roster, shared prompt bytes, the frozen adapters and greedy decoding. Retain valid abstention probabilities. Malformed outputs use Brier probability 0.5 and rank below every valid probability. Report raw Brier and recall at the registered review capacity under the C9 specification. At the freeze, C9-GRPO returned the valid abstention action on all 651 rows, and C9-SFT on none.
>
> External-reference metrics at maturity for B1, M1, M3, B3, P1 and P2 are ROC AUC on native scores, accuracy at the inclusive 0.5 threshold, Brier and horizon-restricted C-index at each horizon. ROC AUC gives half credit to ties and is undefined on a single-class roster. Accuracy and Brier use calibrated probabilities for B1, M1 and M3 and native survival probabilities for P1 and P2. B3 uses the binary expiry call and hard-rule Brier. Report prevalence, confusion counts and always-negative accuracy. The restricted C-index compares an observed event to strictly later times at the same cutoff, including administrative censoring. Tied native scores receive half credit. Report the comparable-pair denominator and NOT_ESTIMABLE if there are no pairs. Published values are external references for their own endpoints, cohorts and validation designs.
>
> The C′ metric supplement is NOT_RUN. The H1–H3 fixed-sequence family and one-sided alpha 0.025 are unchanged. The 12-month window matures on 27 November 2027. The 24-month window matures on 27 November 2028. Score once outcome coverage through maturity is verified.

## 3. Optional file attachment

If the update accepts files, show the owner the archive `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/tracka-freeze-20261128/r6fi2d2uyhjzfz/freeze/trackA-predictions.zip` before attaching it. Its SHA-256 is `85e9521e8cf8d6a909d1a0f7333b3f66851c95dcfaded9116ebdceb744882da2`. If attachments are unavailable, use the hash in the pasted text.

## Hand-back

Record the OSF version and UTC submission time for the main planner to verify against the registered deadline.
