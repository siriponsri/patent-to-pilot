# C3b | Historical applicant identity and native development scores

## Protocol before scoring

The main planner amended C3 after exact-day documentation resolved four of the 221 linked ANDAs in the 2013 window. Use the earliest historical Orange Book edition that lists the ANDA from its approval day through 12 calendar months later, inclusive. Keep documented approval-day holders and transfer intervals as overrides. Report the current Drugs@FDA sponsor as a sensitivity analysis. Apply the existing date-scoped aliases and preserve the published FDA applicant designation in the evidence trace. [C3 receipt](C3.md) · [C3 specification](../../../loe-bench/data/C3_SPEC.json)

Replay 12- and 24-month development scores with the pinned FREEZE implementation. Check exact numerical equality against the published report before releasing the per-row native scores. Use the full original predicted roster for each cutoff. Score 36-month C3 labels only at the 2013-01-01 cutoff using the original 24-month predictions. Keep the threshold, queue capacity, ties, missingness rules and bootstrap from C3. The replay uses local CPU, the closed seal and guarded development evidence. [FREEZE receipt](FREEZE.md)
