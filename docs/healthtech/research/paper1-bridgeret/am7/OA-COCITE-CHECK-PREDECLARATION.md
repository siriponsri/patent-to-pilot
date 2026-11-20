# OA co-citation check for Idea A: criteria declared before running (20 Nov 2026)

Status: DECLARED. This file was committed before the check script ran. No missing-reference recall for any system is computed here.
Owner request: owner-note-20112026, decision 1 (CPU only, USD 0).

## Question

Do our OA labels carry enough "co-cited in the same 103 rejection" structure to build Idea A?
Idea A: given the application and one co-cited IN reference, retrieve the OUT reference that was combined with it.

## Data (developer-visible only)

- Labels: `/data/ptp-paper2/challenge1m/out-v1/pairs-dev.tsv`, produced by the sealed Challenge-1M builder. It holds blocks TRAIN, VAL, P1-DEV and P2-DEV only, with no TEST block. This check reads TRAIN, VAL and P1-DEV.
- Corpus: `challenge1m/out-v1/corpus-units.tsv`.
- Filing dates: `splits/private/tasks.tsv`, read only for apps in those three blocks.
- OA Research Dataset 2017 (`oa2017/`):
  - `office_actions.csv`: the chosen action and its `cite103_max`.
  - `rejections.csv`: number of 103 rows in the chosen action, and `claim_numbers`.
  - `citations.csv`: all 103 references in the chosen action, including foreign and unparsed ones, for the clean test below.
  - All three are filtered to the apps in those blocks before any field is used.
- The chosen action is the same as the task definition in `oa_temporal_splits.py`: the earliest CTNF by (mail_dt, ifw_number), mailed 2008-01-01 to 2017-12-31.

## Definitions

- **C103(q)** = units u of q in `pairs-dev.tsv` that pass all of these:
  - basis is 103 or both;
  - unit present, with a known first_pub;
  - first_pub < filing_date(q);
  - u is not q's own unit;
  - u is in the Challenge-1M corpus.

  This is the evaluator's conditional positive set restricted to 103.
- **A-eligible** task: C103(q) holds ≥1 IN3 unit (the anchor) and ≥1 OUT3 unit (the missing target).
- **Clean (single combination)**: n103_all(chosen action) == cite103_max(chosen action) ≥ 2.
  - n103_all = distinct 103-cited references in that action from `citations.csv` with citation_in_oa = 1, counting US and foreign/unparsed.
  - When this holds, one 103 rejection cites every 103 reference in the action, so the whole set is one combination.
  - Secondary definition, reported only: the action has exactly one `rejections.csv` row with action_type 103.

## Gate (fixed now)

- G1: P1-DEV A-eligible ≥ 2,000 tasks. At n = 2,000, a paired SD of about 0.3 gives an MDE of about 0.02.
- G2: TRAIN A-eligible ≥ 10,000 tasks. Enough to train a conditional reranker.
- G3: P1-DEV clean A-eligible ≥ 500 tasks. Enough for a same-rejection sensitivity analysis.

Outcomes:

- G1, G2 and G3 all pass: SUFFICIENT. Write AM-7 and freeze it before any missing-reference number exists.
- G1 and G2 pass but G3 fails: PARTIAL. The label can only be "co-cited under 103 in the same office action". Report to the owner before writing AM-7.
- G1 or G2 fails: INSUFFICIENT. Idea A is not used in this form, and the owner's fallback is D + B.

## Reported (aggregates only)

Per block:

- tasks;
- tasks with |C103| ≥ 2;
- A-eligible tasks;
- clean tasks;
- clean A-eligible tasks;
- distributions of |C103|, OUT targets per eligible task, and IN anchors per eligible task;
- 103-row count per action;
- share of actions with claim_numbers present;
- cite103_max;
- runtime.

P1-TEST count is estimated as the P1-DEV A-eligible rate × 10,000 and is labelled as an estimate. No TEST label is read.
