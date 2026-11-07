# Amendment 1 to the frozen Solution Scout protocol: E6 "time machine" (DRAFT, 7 Nov 2026)

- **Status: DRAFT, NOT IN FORCE.** This text changes nothing until the owner approves it and a commit marks it `IN FORCE`, before any DAPFAM test read.
  - The frozen protocol [SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md](SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md) (freeze `4c5a882`) stays as it is until then.
- **Why:** the owner chose the time-machine framing on 7 Nov 2026. The pre-declared dev probe ([audit](../audits/ptp-time-machine-dev-probe-20261107/README.md), plan `013cbb9`) returned `GO_SHOCK` on 25 A61 dev queries: hit@20 0.08 (U) vs 0.28 (X).
  - The amendment adds one secondary analysis, E6. It changes no existing E1–E5 rule, run or decision.
- **What the test can show:** the dev probe used dev rankings and labels already seen in earlier dev work. E6 is the one-time confirmation on the unread test split.
- **Open before it comes into force** (marked ⚠ below):
  - any dev-only method changes the owner may approve first;
  - the frozen analysis script.

## E6. Time machine: older cross-industry evidence for medtech problems (DAPFAM test, secondary, descriptive)

**Population:**
- test queries whose IPC3 list contains `A61`;
- with at least one positive relation with `domain_rel = OUT`;
- where that target's earliest claim year is at least **5 years** before the query's earliest claim year.

Those targets are G_q.
- Expected size: about 40 queries, by the dev proportion (25 of 474).
- If fewer than 20 queries qualify, E6 reports counts and rates only, with no contrast.

**Time filter:**
- In every ranking, drop each candidate whose earliest claim year is later than the query's earliest claim year, then truncate.
- Candidates with an unknown year are kept and counted.

**Arms:** all come from the test rankings that E1/E2 already produce (step 4 of the run order), so no extra run is needed.

| Arm | Ranking |
|---|---|
| **U** | brief P, full candidate set |
| **X** | brief P, other-fields set |
| **M** | U[:10] then X, deduplicated, to 20 |
| R2-U, R2-X | Full-patent view; leakage references only |

⚠ If the owner approves a dev-only method change first (for example a different lane construction), it is defined here before this amendment comes into force. Every variant tried on dev is listed in the amendment.

**Measures:**
- **Primary for E6:** hit@20 (at least one member of G_q in the first 20).
- **Also reported:**
  - recall@20 and hit@100;
  - the median year gap of X's hits;
  - the IPC sections of the hits;
  - the counts.

**Statistics:**
- Paired query bootstrap, 5,000 resamples, seed `20261106` (the frozen protocol's seed). Contrasts: X − U and M − U on hit@20.
- E6 is outside the Holm family of E1; there is no multiplicity adjustment.

**Secondary populations** (descriptive): A61 with gap ≥ 1 y and ≥ 10 y; all IPC sections with gap ≥ 5 y.

**Wording rule (pre-declared):** the paper may state the headline form only if X − U on hit@20 has a 95% lower bound > 0 on test. The headline form is: "for medtech problems, a plain search showed an older cross-industry document in the first 20 for a% of queries; a cross-industry lane raised it to b%, and the documents were a median of c years older".
- Otherwise the test numbers are reported as they are, beside the dev numbers, with no headline.
- In all cases the paper states that the lane uses the same rule as the OUT definition, so part of the contrast holds by construction.

**Reporting:**
- Dev (probe) and test numbers are reported separately and never pooled.
- Brief P is LLM-written from the query patent, a possible leakage, and this is stated.
- Relevance is citation-based: unjudged is not negative.

## Code (⚠ to be written and frozen with this amendment)

- `scripts/healthtech/analyze_time_machine_test.py`: the dev probe's logic, unchanged, but reading the test rankings and test labels.
  - It refuses to overwrite its output and runs once after E1/E2.
  - Its output goes to `docs/healthtech/audits/ptp-scout-frozen-eval-*/e6-time-machine.json` (aggregates only).
- Unit tests for the time filter, the mixed pool and the population rule.

## Order of runs (unchanged except for E6)

Step 5 of the frozen run order (the E1/E2 analysis) is followed by **5a: E6, one run.** Nothing in E1–E5 changes.
