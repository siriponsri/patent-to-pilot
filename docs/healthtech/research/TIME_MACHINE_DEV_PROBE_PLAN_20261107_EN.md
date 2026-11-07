# Time-machine feasibility probe (DAPFAM dev only): pre-declared plan, 7 Nov 2026

- **Status:** PRE-DECLARED. This file and `scripts/healthtech/probe_time_machine_dev.py` are committed before the probe is run. The probe runs once; the script refuses to overwrite its output.
- **Owner decision (7 Nov 2026):** run a dev-only feasibility check for the "time machine" framing. The direction review is in §7 of [DEEP_DIVE_DIRECTION_REVIEW_20261107_EN.md](DEEP_DIVE_DIRECTION_REVIEW_20261107_EN.md).
- **Data boundary:** DAPFAM **dev** split only (Stage 0 `split.json`). The test split is not read. No GPU, no LLM call, USD 0. The probe uses existing dev rankings from the scout feasibility check.
- **What this is:** a go/no-go for a framing. It is not a scientific claim and is not part of the frozen E1–E5 protocol. Any test-split use needs a dated amendment to the frozen protocol before the test read.

## Question

A medtech problem is written as a short problem brief, and only patents that existed at the time are searchable. How often does a search show, in the first 20 results, an older cross-industry document that the examiner or applicant later cited as relevant? How does an ordinary search over all patents compare with a dedicated cross-industry lane?

## Population

**Primary population:**
- dev queries whose IPC3 list contains `A61` (medical);
- with at least one positive relation with `domain_rel = OUT`;
- where that target's earliest claim year is at least **5 years** before the query's earliest claim year.

Those targets are the query's **older cross-industry targets** G_q.

**Secondary populations** (descriptive):
- A61 with a gap of at least 1 year;
- A61 with a gap of at least 10 years;
- all IPC sections with a gap of at least 5 years, as context.

## Time filter ("the corpus as of the query year")

- From every ranking, drop each candidate whose earliest claim year is later than the query's earliest claim year, then truncate.
- Candidates with an unknown year are kept, and their count is reported.

## Arms

All arms use existing dev rankings at depth 200 (PatEmbed-large dense, MaxP).

| Arm | Ranking | Notes |
|---|---|---|
| **U** | `rankings-d-P-dev.jsonl` | Brief P over all patents |
| **X** | `rankings-x-P-dev.jsonl` | Brief P, other-fields lane: families sharing no IPC3 code with the query |
| **M** | U[:10] followed by X, deduplicated, to 20 | Secondary: a mixed view |
| R2 | `dense-single/rankings-dense-single-top200.jsonl` | Reference only. The full query patent contains the solution, so this is a leakage reference, not a rewind |
| R2x | `rankings-x-R2-dev.jsonl` | Reference only. Same leakage caveat |

**Brief P** is the frozen `ptp-solution-scout-v1` `PROBLEM` text that Qwen3-8B wrote from the query patent. It may leak mechanism words even though only the problem was requested; this is a stated limitation.

## Measures

- **Primary:** hit@20, meaning at least one member of G_q in the first 20 time-filtered candidates.
- **Secondary:** recall@20 and hit@100 over G_q.
- **Also reported:**
  - the median year gap of the hits;
  - the IPC sections of the hit targets;
  - the counts of queries and pairs.
- **Statistics:** paired query bootstrap, 5,000 resamples, seed `20261107`. The primary contrast is X − U on hit@20.

## Decision (pre-declared)

| Status | Condition |
|---|---|
| `GO_SHOCK` | n ≥ 20 queries **and** X hit@20 ≥ 0.25 **and** X hit@20 ≥ 2 × U hit@20 **and** the 95% CI lower bound of X − U > 0 |
| `GO_DESCRIPTIVE` | The lower bound of X − U > 0, but some other `GO_SHOCK` condition fails |
| `NO_GO` | Otherwise |

**Known in advance:** X excludes every family that shares an IPC3 code with the query. Strict-OUT targets are defined by the same rule, so a positive X − U is expected partly **by construction**. On dev over all sections, X roughly doubled OUT R@200, as the scout feasibility audit shows.
- The informative quantities are therefore the absolute hit rates and the time gap, not the existence of a difference.
- The `GO_SHOCK` bar is set on X's absolute level for that reason.

## Outputs

- **Aggregates only:** `docs/healthtech/audits/ptp-time-machine-dev-probe-20261107/probe.json`.
- **Demo candidates** (private, IDs only): `../_private_artifacts/healthtech/ptp-org-adaptive-20261105/scout/time-machine-dev-cases.jsonl`. These are queries where X found an older target in the top 20.
- No DAPFAM text enters Git.
