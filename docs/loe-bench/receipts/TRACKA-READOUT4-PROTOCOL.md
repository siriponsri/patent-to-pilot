# TRACKA-READOUT4 protocol

28 November 2026. Executor branch `loe/TRACKA-READOUT4`, based on `d998c9335e559442d9e0897b2e289d833c853776` from `origin/research/loe-bench`. First maturity is 27 November 2027. All outcome and publication fixtures in this card are fictional. [Round 3 findings](../reviews/EXTERNAL-REVIEW-R3.md) · [Planner rule](../reviews/EXTREV-RESPONSES.md#round-3-review-answered-28-nov-2026-2319-bangkok).

## Publication and replay

- The first verified publication at each horizon controls the entire family in the registered GitHub repository, Zenodo version DOI and OSF update 4 freeze digest. H3 can acquire a formal decision only in the first 24-month publication. Keep the frozen hypothesis order, estimates, intervals and maturity rules.
- Mark standalone results `PROVISIONAL` through the family label and in the displayed decisions. Preserve the underlying fixed-sequence calculations for inspection and comparison. The registered default-branch workflow is the only supported publisher. Its scoring step captures live FDA data and its publication step verifies scope, an eligible provisional run, and the absence of a release, tag or surviving scored issue at the current horizon. The publication bundle bears the formal decisions in the verified release. The workflow retains provisional and replay artifacts separately from the release.
- Check the current horizon for a prior publication in the registered scope. Preserve and verify its original bytes. Mark subsequent computations `REPLAY`, compare the H1–H3 fields against the published aggregate, and preserve any differences in JSON and the report. If FDA coverage or capture prevents the comparison, record that disposition and keep the verified archive available. A standalone command without registered-scope discovery labels its computation `PROVISIONAL`.
- Retain the READOUT3 H3 rules for finding the 12-month input. An eligible 24-month publication requires a verified first 12-month result or the predeclared revised vintage supported by the discovery record.

## Publication witnesses

- Inspect all trusted scored issues before deciding absence. Record every issue locator and its available publication pins. Compare pins for the same asset across witnesses. A malformed pin, missing required result pin or disagreement yields `DISPUTED` before fallback. Consistent issue-only evidence with the release and exact tag absent permits the documented 12-month fallback. A surviving issue at the horizon being published requires recovery of that horizon's first release.
- Preserve release-notes-only recovery, validation of the result and FDA manifest pins and asset integrity checks. Conflicting or malformed issue evidence leaves H3 descriptive and prevents a new formal 24-month publication.

## Acceptance checks

1. With a fixed verified first 12-month publication and no 24-month publication, score two covered caller-supplied FDA snapshots that change the registered sequence outcome. Assert that both complete families are provisional. Repeat with documented absence of the first 12-month release, checking that their H3 estimates differ while both families remain provisional.
2. Exercise the live-fetch publication path against synthetic GitHub and FDA evidence. Verify the first published bundle and a second canonical attempt marked `REPLAY`. Check a changed replay, an identical replay, and retention of the old archive when FDA inputs are unavailable. Assert that no replay can prepare a replacement formal bundle. Preserve exact 24-month recovery and release-only verification.
3. With an absent release and exact tag, test agreeing, conflicting and malformed trusted issue-only witnesses. Assert complete locators and available pins in the discovery record and `DISPUTED` plus descriptive H3 for both failure cases. Retain the release-present witness and asset integrity checks.
4. Run the LOE-Bench unittest suite, Worker npm suite and root pytest gate. Check workflow shell syntax and synthetic/production separation. If the branch can be dispatched with `synthetic=true`, verify the synthetic job and both production jobs' skipped state. Record exact commands, runtimes, test counts, exit codes and verification limits in the receipt.

The frozen forecasts, freeze manifest, freeze tag, OSF records and the four primary scorer modules are outside this card's writable paths. Mature scoring, production publication, protected data, paid APIs and GPU jobs are outside the test plan.
