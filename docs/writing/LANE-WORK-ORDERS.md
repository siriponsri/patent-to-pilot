# Parallel lanes P2 / P3 / Product — first work orders (19 Nov 2026)

These lanes start after the P1 grid / B53 jobs and do not block them. Each item names its input, output and acceptance. No
protected TEST is used.

## P2 CEDS (Acquire)
1. **Real backend adapter.** Connect `src/patent_to_pilot/research/acquisition_harness.py` to the Challenge-1M BM25 run
   files and dense indices on dr-train (read-only). Output: Search/Visit/Select over real units.
   Acceptance: the existing `tests/test_acquisition_harness.py` and `tests/test_patex_arms.py` still pass, plus one
   integration test on 20 P2-DEV tasks.
2. **P2-DEV pilot (descriptive).** 200 P2-DEV tasks (family-disjoint from P1-DEV by manifest-v2), matched-budget arms
   E0/E1/E2/E3, cost ledger on.
   Acceptance: funnel table Search-R/Visit-R/Select-R with cost per recovered OUT citation; no claim beyond descriptive.
3. **Pre-declaration P2.** Update `plans/P2-OA-PREDECLARATION-DRAFT.md` with the pilot's measured costs before any
   confirmatory run.

## P3 EG-SHE (Repair)
1. **Typed patch contract.** A schema for stage patches (Search/Visit/Select): typed fields, preconditions, rollback.
   Acceptance: unit tests that reject untyped or unsafe patches.
2. **Replay runner** over recorded P2-DEV traces (from P2 step 2) and synthetic traces.
   Acceptance: deterministic replay hash equality before/after a no-op patch.
3. **Controls:** E4 uniform evolution, E5 headroom-gated, E7b random eligible stage, all under equal compute.
   Acceptance: synthetic headroom fixture where E5 > E7b and a fixture with no headroom where Stop-A triggers.

## Product (Solution Scout)
1. Demo path verified 19 Nov (`is2/DEMO-STORYBOARD.md`). Next: record a fallback screen capture.
2. Close the recorded P0 gap (`docs/healthtech/product/P0-P2-GAP-AUDIT.md`, 41/42).
3. Licence split: a commercial build profile with a commercially licensed encoder; keep the patembed demo profile
   research-only.
