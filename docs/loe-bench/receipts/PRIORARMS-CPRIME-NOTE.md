# PRIORARMS | C′ supplement analysis note

**Recorded 28 November 2026, before any supplement calculation.** The [locked specification](../PRIOR-ARMS-SPEC.md) permits a descriptive, aggregate-only analysis of the previously exported C1 scores. The existing [SCORE receipt](SCORE.md#private-outputs-and-verification) supplies the export digests and schemas.

| Output | Arms and horizons | Fields and rule |
| --- | --- | --- |
| Pooled row ROC AUC | B1, M1 and M3, each at 12 and 24 months | Use native `B1`, `M1` or `M3` with binary `y` in the corresponding authenticated `C1_scores_12m.json` or `C1_scores_24m.json` export. Validate unique `(key, cutoff)` and the registered horizon. Tied scores receive half credit. A single-class panel is `NOT_ESTIMABLE`. |
| Accuracy and confusion counts | Same arms and horizons | Apply the original frozen development sigmoid to each native arm score using SCORE's original calibrator inputs. Classify positive at calibrated `p >= 0.5`. Report TP, FP, TN, FN and the always-negative accuracy. Use the full authenticated export at each horizon. |
| Brier | Same arms and horizons | Transcribe the existing SCORE values. At 12 months these are 0.0373, 0.0354 and 0.0352 in B1, M1, M3 order. At 24 months these are 0.0713, 0.0654 and 0.0647. |
| Horizon-restricted, within-cutoff C-index and comparable pairs | Same arms and horizons | Use the native arm score and exact event time in `(cutoff, cutoff + horizon]`, with administrative censoring at the horizon. Compare only a strictly earlier observed event with a later observed time from the same cutoff. Give tied native risk half credit. The documented export fields omit event times. Record `NOT_ESTIMABLE` and do not join another source to recover dates. |

The only planned outputs are aggregate rows, unique drugs, event counts, prevalence and the measures above in [PRIORARMS.md](PRIORARMS.md). The analysis does not use B3, P1 or P2 on C′. It requires an export-only execution path under the authorized SCORE runner. That runner's public entry point either replays the development preflight or opens protected source inputs for a new scoring pass. It has no export-only mode. The PRIORARMS executor will record the calculation `NOT_RUN` under the locked restriction. The existing Brier values can be transcribed from SCORE.
