# Time-machine feasibility probe (DAPFAM dev): GO_SHOCK, small n

- **Status:** PASS. The probe ran once, as pre-declared in [TIME_MACHINE_DEV_PROBE_PLAN_20261107_EN.md](../../research/TIME_MACHINE_DEV_PROBE_PLAN_20261107_EN.md) at commit `013cbb9`.
  - Dev split only; the test split was not read.
  - No GPU, no LLM call, USD 0.
- **Decision under the plan: `GO_SHOCK`.** It is the narrowest possible pass: n = 25 (bar 20), and X hit@20 = 0.28 (bar 0.25).
  - This is a go for the framing, not a scientific result. Confirmation needs the test split, under a dated amendment to the frozen protocol made before the test read.
- Results: [probe.json](probe.json) (aggregates only). The 5 demo-case IDs are private, in `../_private_artifacts/healthtech/ptp-org-adaptive-20261105/scout/time-machine-dev-cases.jsonl`.

## Primary result

**Population:**
- 25 dev queries in A61 (medical), with 30 older cross-industry targets;
- each target is a positive relation with `domain_rel = OUT` and an earliest claim year at least 5 years before the query's;
- rankings are time-filtered to the query year.

Older cross-industry target in the first 20 results:

| Arm | hit@20 | recall@20 | hit@100 |
|---|---|---|---|
| **U**: problem brief, all patents | **0.08** | 0.06 | 0.20 |
| **X**: problem brief, other-fields lane | **0.28** | 0.24 | 0.32 |
| M: U[:10] then X | 0.28 | 0.24 | 0.28 |
| R2: full query patent, all patents (leakage reference) | 0.24 | 0.20 | 0.24 |
| R2x: full query patent, other-fields lane (leakage reference) | 0.32 | 0.26 | 0.48 |

**Contrasts on hit@20** (paired query bootstrap, 5,000 resamples, seed `20261107`):
- **X − U: +0.20 (95% CI +0.04 to +0.36)**, bootstrap p 0.008;
- M − U: +0.20 (CI +0.04 to +0.36).

**The targets X found:**
- They were a **median of 16 years** older than the query (range 5–28).
- Their IPC sections were B (3), F (3), A (1), E (1), G (1) and H (1).

## Secondary (descriptive)

| Population | n | U hit@20 | X hit@20 | X − U (95% CI) | Median gap of X hits |
|---|---|---|---|---|---|
| A61, gap ≥ 1 y | 27 | 0.11 | 0.33 | +0.22 (+0.07 to +0.37) | 8 y |
| A61, gap ≥ 10 y | 18 | 0.11 | 0.22 | +0.11 (0.00 to +0.28) | 19 y |
| All sections, gap ≥ 5 y | 133 | 0.20 | 0.32 | +0.12 (+0.07 to +0.17) | 12 y |

## How to read this

- **By construction.** X drops every family sharing an IPC3 code with the query, which is the strict-OUT definition. A positive X − U was expected in part for that reason. The plan therefore put the bar on X's absolute level.
- **Possible headline numbers** (dev, small n, CIs wide):
  - for medtech problems, a plain search showed an older cross-industry document in the first 20 for 8% of queries;
  - a cross-industry lane raised that to 28%;
  - the documents found were a median of 16 years older.
- **The mixed view keeps the gain.** M, which shows 10 general results and then the lane, scores the same as X at 20, so a product does not have to hide the general results.
- **The short brief.** Under the lane, the problem brief scored above the full patent searched over all patents (0.28 vs 0.24). It scored below the full patent under the same lane (0.32).
- **Most targets are still missed.** Even X misses 72% of these queries at 20.
- **Medtech looks harder for plain search** than the all-section population (U 0.08 vs 0.20), but n = 25 is too small to claim it.

## Limitations

- **Sample size.** n = 25 just meets the bar, and the gap ≥ 10 y subgroup has a CI that touches 0.
- **Possible leakage in brief P.** Qwen3-8B wrote brief P from the query patent itself, with the `PROBLEM` field only. It may still leak mechanism words. In a real rewind, the user writes the problem.
- **Gold is incomplete.** Relevance is citation-based: unjudged is not negative, and known-link hits are not exhaustive recall.
- **The time filter is approximate.** It uses earliest claim year. 195 candidate slots with an unknown year were kept, across all arms and queries.
- **Dev only.** These rankings and labels were already used in earlier dev work.

## Command and hashes

- Command (exit 0, 07:55:34Z–07:55:36Z on 7 Nov 2026): `python scripts/healthtech/probe_time_machine_dev.py --split $P/split.json --rankings-dir $P/scout/rankings --r2 $P/dense-single/rankings-dense-single-top200.jsonl --output docs/healthtech/audits/ptp-time-machine-dev-probe-20261107/probe.json --cases-output $P/scout/time-machine-dev-cases.jsonl`, where P = `../_private_artifacts/healthtech/ptp-org-adaptive-20261105`.
- `probe.json` sha256 `721de03483fbb662abcbc0936243888d2f4271b02d188dad56627235d4a88e8c`.
- Private cases file sha256 `de304bce86774b92442f73d54df17259714ddeb97e33b575ca37cc45912b460a`.
- Input hashes are in `probe.json` (`inputs_sha256`).
- Base commit `013cbb9` (the plan and code). Unit tests: `tests/test_time_machine_probe.py` (3 passed).

## Next

These need the owner:
1. A **dated amendment** to the frozen protocol, made before the P3 test read. It would add this A61 time-machine analysis as a pre-declared secondary of E1/E2: same arms, time filter, gap ≥ 5 y, hit@20, X − U. The test population would be about 40 A61 queries by dev proportion.
2. A **demo prototype** built from the 5 private dev cases, plus authored HUPD examples for anything shown publicly.
