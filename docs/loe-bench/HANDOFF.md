# LOE-Bench lane handoff

Owner of this file: main planner (Claude Opus). Branch: `research/loe-bench`, with its local worktree at `../_worktrees/ptp-loe-bench`. Plan and board: [PLAN.md](PLAN.md). Memory: [MEMORY.md](MEMORY.md).

## Current state (27 November 2026, Wave 1 closed)

- Wave 1 is merged after review. The full `loe_bench` unittest discovery passes 34 tests.
- **E1:** S0 inputs are frozen with t0 2026-11-27 and tag `loe-S0-input-20261127`.
- **E2:** 19 historical Orange Book editions (2009–2026) and the as-of parser `ob_history.py` are merged. G1 passes, so C′ is feasible subject to the CP1 coverage gate.
- **E3:** Purple Book monthly CSVs are open (77 months), and the Track B table is built. Reference products with several BLAs are grouped by product name.
- **E4:** the LLM harness is built, but the GPU smoke is BLOCKED because dr-train was offline. `rule_baseline` in the prompt is admissible for Track A only. Track C′ must take it from the as-of edition.
- **E5:** no Thai sample could be retrieved. The demo will use four columns of curated links, and owner access items are deferred to the end-of-research pack.
- **CP1:** code defects found by static review must be fixed (FIX1) before any modeling. The new single primary endpoint is paired ΔAURC(M3 − M1) at 24 months on C′.

## Wave 2 status

- FIX1 is merged after main-planner review. The suite passes 51 tests, 17 of them regression tests. The repo pytest shows only the 8 accepted SACR failures. Real-data row counts did not change for the 1995–2014 training grid.
- CP2 (GPT-6.2 Astra high) and T7 (GPT-6 Luna high) are dispatched. T2 waits for the CP2 split decision. The first historical Orange Book edition is from 2009-06, which limits the C′ training window.
- GPU: owner rule. Send a proposal with GPU type, rate, hours per stage, budget cap and stop rules, and get approval before any pod is created. No envelope is approved yet.

## Next action (Wave 1 close)

Owner confirms the GPT executor model mapping in PLAN.md. Then dispatch FIX1. After FIX1, run T7 and T2, then T1, then T4. When dr-train is back online, rerun the E4 smoke.
