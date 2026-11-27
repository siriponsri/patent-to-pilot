# FREEZE | Criteria v3 development freeze

## Protocol recorded before scoring

Use the merged FIX2c, E7b and K07 development replay, REG PIV semantics and graph v1.
Use the T1v3 guarded source readers, split, native models and train-only calibration.
Reconcile H2 on the same development roster. Replay pre-REG by restoring fresh-list
non-observation for matched undated PIV rows without a dated witness. Swap REG on
TRAIN, then on validation. Compare both queue scorers, matching seeds and draws.
Check native scores and common calibrators against the K22 entrypoints. Historical
policy differences belong to secondary actions. [T1v3](T1v3.md) · [REG](REG.md) · [K22](K22.md)

Freeze the native triage queue and keep the T1v3 asymmetric policy for safety and
illustrative loss. Report grouped native-score AP. For continuity report policy
AURC80 and full-coverage E-AURC on the legacy TRAIN-selected 90% confidence operating
point where defined. Also report the common probability-only ranking diagnostic
using calibrated probabilities, a 0.5 classification threshold, and max(p, 1−p)
confidence. The latter supplies a defined ranking diagnostic independent of
realized policy coverage. Brier and ten-bin ECE use calibrated probabilities.
Use missed-clear cost 10, false-flag cost 1 and referral cost 0.5, with perfect
referral resolution assumed. Use the same 2,000 paired whole-drug draws per horizon
and seed 20261127 for endpoints and contrasts. Keep the original safety interval
conditional on the observed clear roster. The acceptance checks are exact annual
queue capacity and defined endpoints. Report conditional auto-clear safety and
legacy coverage separately. [Criteria v3](../PLAN.md#confirmatory-criteria-v3-owner-approved-27-november-2026-supersedes-v2-endpoints)

The sealed schedule is set using annual Jan 1 cutoffs from 2017 and complete
follow-up by the pinned S0 observation end. Candidate cutoffs require an FDA
Orange Book edition within six calendar months with availability proven by the
cutoff. An independent data custodian supplies the blinded event history
projection to the eligibility gate. The gate only emits PASS or FAIL. The
FREEZE executor runs development only.
