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
| K04 | As-of challenge leaf (FDA PIV list + Rai court filings + EDGAR) | E6, E6-alt | M1, M3 (as features); M3 (as the leaf) | Dated witnesses only | ADOPTED | E7 had partial coverage. With E7b patent-number relinking (1,065 cases, 259 drugs by 2016), development at 24 months gave M1−B1 −0.0096 (CI −0.0188 to −0.0018) and M3−B1 −0.0087 (CI −0.0194 to +0.0017). At 12 months both CIs fall below 0, and M3−M1 is about 0 |
| K05 | L2 grid {1, 10, 100}; selected value at the grid edge | T2b | M1, M3 | None | TRIED-DEV | Extend the grid (T1) |
| K06 | Confidence discount when a decision-relevant leaf is UNKNOWN (M3), with the matching missing-input discount for M1; configurations 0 or 0.05 | CP3 scan (rank 1) | M3 policy; M1 counterpart | None | REJECTED | DEVX: failed the pre-declared adoption rule (see receipts/DEVX.md) |
| K07 | Count distinct strengths and form/route pairs at the cutoff | CP3 (rank 2) | M1, M3 | Low (as-of products only) | ADOPTED | DEVX: M3−B1 at 24 months improved by −0.0032 (CI −0.0083 to −0.0003) against E7b. The robustness fold held at 24 months but reversed slightly at 12. M3 Brier and ECE at 24 months worsened |
| K08 | Error selector for the emitted action (confidence plus disagreement with the age clock) | CP3 (rank 3); Calibrated Selective Classification, arXiv 2208.12084 | M1, M3 | Out-of-fold fitting only | REJECTED | DEVX: failed the pre-declared adoption rule (see receipts/DEVX.md) |
| K09 | Discrete-time hazard in two annual intervals | CP3 (rank 4) | M1, M3 | None | REJECTED | DEVX: failed the pre-declared adoption rule (see receipts/DEVX.md) |
| K10 | Beta calibration instead of the sigmoid | CP3 (rank 5) | M1, M3 | None | REJECTED | DEVX: failed the pre-declared adoption rule (see receipts/DEVX.md) |
| K11 | CMS Medicare/Medicaid spending as a demand proxy | CP3; NBER w6190 | M1, M3 | High (release-date witness required) | IDEA, needs owner decision on a new source | Coverage before 2015 is poor |
| K12 | Competing risks | CP3; DeepHit | M1, M3 | Needs a label taxonomy | IDEA, needs owner decision | — |
| K13 | Isotonic and inductive Venn–Abers calibration | CP3; arXiv 1511.00213 | M1, M3 | None | IDEA | — |
| K14 | Conformal risk control for the operating point | CP3; arXiv 2208.02814 | M1, M3 | Exchangeability under drift is unverified | IDEA (secondary only) | — |
| K15 | Selective and verdict-specific calibration | CP3; arXiv 2208.12084 | M3 policy (M1 same budget) | None | IDEA | Only 10 OPEN validation rows |
| K16 | Learning to defer | CP3; arXiv 2006.01862 | both | Needs analyst decisions | IDEA, needs owner decision for reviewer data | — |
| K17 | Cost-aware evidence acquisition (VoI per review minute) | CP3 | M3 workflow | Needs review logs | IDEA (outside H1/H2) | — |
| K18 | AUGRC as a secondary selective metric next to AURC80, with an MSP/SRmax confidence baseline | SciSpace report (owner, 27 Nov), section 2 | reporting only | None | IDEA (secondary metric; decide in T5) | — |
| K19 | As-of FDA product-specific guidance (PSG) availability and date as a feature | SciSpace Table 1; Hopefl et al. 2025, doi:10.1111/cts.70365 (used PSG availability lagged 1 year) | M1, M3 | Survivorship of revised or withdrawn PSGs (verify with Wayback) | QUEUED (E9) | — |
| K20 | NBER Orange Book Dataset 1985–2016 (annual editions) to extend as-of features before 2009 and fill 2011 | SciSpace D3; Durvasula, Hemphill, Sampat et al., Res Policy 2023, doi:10.1016/j.respol.2023.104791 | all (larger training window) | Edition-year availability rule needed | DATA INGESTED (E8); model trial pending | 31 annual editions. Content is about 12 months old at Jan-1 cutoffs, versus 6 months or less for the Wayback ZIPs. NBER terms restrict redistribution and commercial use, so keep raw files private and publish only code and instructions |
| K21 | Open demand proxy from Medicaid SDUD, vintage by posting date | SciSpace idea 3 | M1, M3 | Suppression and later revisions | IDEA, needs owner decision (overlaps K11) | — |
