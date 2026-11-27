# LOE-Bench technique ledger

This is the single record of score-improvement ideas, so that no one repeats them. Check it before proposing or trying any technique, and add a row for every idea, including rejected ones.

## Integrity rules for score improvement

- Tune and select on **development data only** (training and validation). The test seal stays closed until preregistration.
- **Fairness for H2.** Any shared modeling improvement (features, base model, calibration) must go to both M1 and M3 under the same tuning budget. Only graph and policy improvements may be specific to M3.
- **No outcome proxies.** Never use a feature that encodes the outcome or post-cutoff knowledge, such as the FDA First Generic list or a backdated submission date.
- Record the number of configurations tried per arm. The preregistration reports it.

## Status values

IDEA · QUEUED · TRIED-DEV (result on validation) · ADOPTED · REJECTED (reason)

## Ledger

| ID | Technique | Source (paper, repo or competitor) | Arms affected | Leakage risk | Status | Evidence |
|---|---|---|---|---|---|---|
| K01 | As-of Orange Book patent and exclusivity features | FIX1, E2, E2b | M1, M3 | Controlled by the freshness and availability rule | ADOPTED | T2b, FIX2c |
| K02 | Shared age-hazard base (B1 logit) in M1 and M3 | T2b | M1, M3 | None | ADOPTED | T2b: M1 beat B1 only once the shared base was added |
| K03 | Active-moiety key (GSRS UNII + alias union) | FIX2, FIX2b | all | Identity only (2026 GSRS release, disclosed) | ADOPTED | Fresh audit: 57/60 correct |
| K04 | As-of challenge leaf (FDA PIV list + Rai court filings + EDGAR) | E6, E6-alt | M1, M3 (as features); M3 (as the leaf) | Dated witnesses only | QUEUED | E7 |
| K05 | L2 grid {1, 10, 100}; selected value at the grid edge | T2b | M1, M3 | None | TRIED-DEV | Extend the grid (T1) |
