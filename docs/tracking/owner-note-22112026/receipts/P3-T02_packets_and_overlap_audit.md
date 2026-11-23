# P3-T02 — Overlap audit and grouped Thai source packets (packets-v1)

**Task:** P3-T02 (phase P3, lane offline). **Built:** 23 Nov 2026. **Spend:** USD 0. No download, no paid API, no model
and no LLM judge was used. **Authority:** D18 (local Thai copies), P3-T01 contract, D15 (PyThaiNLP).

**Evidence in Git:**
- builder: `scripts/research/p3t02_build_packets.py` (`p3t02-packets-v1`, sha256 `f2b969b30c27…`);
- tests: `tests/test_p3t02_packets.py` (8 tests, fictional rows only);
- aggregates-only summary: `receipts/P3-T02_packets_summary.json`. The builder refuses to write it if it contains any
  Thai character, so no question text, law name or law code reaches Git.

**Private outputs:** `C:\Users\User\Desktop\myProject\_private_artifacts\thai-data\packets-v1\` (never committed).

Status fields: `method_evidence` NOT_YET_DEMONSTRATED (no retrieval run); `product_readiness` unchanged (never bundled);
`publication_readiness` unchanged.

## 1. What was declared, and one amendment

The builder docstring declares the rules. Inputs are sha256-verified against `thai-data/MANIFEST.json` before reading.

- **DEV source:** WangchanX-Legal-ThaiCCL-RAG train only.
- **Held-out:** NitiBench `ccl` and `tax`, the pinned `data/ccl-*` and `data/tax-*` shards.
- **Gazette:** the Gazette queries enter the audit as question text only. Gazette qrels and the `author_model` /
  `judge_model` fields were not read.
- **Family unit:** the law (`law_code`).
  - Held-out laws are every law named in NitiBench `relevant_laws` or `reference_laws`, mapped by `law_name` through the
    statute corpus.
  - A DEV record is eligible only if none of its positive laws is held out.
- **Variant rule:** a variant is an equal normalised question, or a Jaccard of at least 0.8 on character 5-gram shingles.
  - Normalisation: NFC; zero-width characters removed; Thai digits converted to Arabic; PyThaiNLP 5.4.0
    `util.normalize`; casefold; whitespace, punctuation and control characters removed.
  - A DEV candidate that is a variant of any held-out question is excluded.

**Amendment before the settled run.** The first rule formed families as connected components of laws linked by
multi-law records. A discarded trial in a scratch folder (nothing kept) showed that this puts 1,305 of 1,330 DEV items
in one family, and 2,483 of 3,779 held-out items in one family. Such families are useless for grouping.

The settled rule is now:
- one family (packet) per law;
- an item joins the family of its rank-1 gold law;
- DEV variant questions are merged into one family;
- items whose gold also cites another law record that count (`gold_laws_in_other_packets`).

The component sizes are still reported in `overlap_audit.json`. The split rule did not change: no law, source or variant
crosses DEV and held-out.

A test caught one rule defect before the settled run: the date cue missed `ภายใน 30 วัน` when a space separated the
number and the unit. It was fixed. The trial counts with the bug differed only slightly: DEV date 79 → 81, held-out date
572 → 573.

The data files are deterministic: two runs gave byte-identical files (MANIFEST.json differs only in its timestamp).

## 2. Overlap audit (required before any DEV use)

Set *a* is WangchanX train (8,211 questions). Set *b* is the held-out set. Counts are questions unless stated.

| Check | vs NitiBench-CCL (3,729) | vs NitiBench-Tax (50) | vs Gazette queries (2,000) |
|---|---|---|---|
| Exact raw match (b found in a) | 4 | 0 | 0 |
| Normalised exact match (b in a) | **7** (0.19%) | 0 | 0 |
| Near-duplicate, Jaccard ≥ 0.9 (b with a match) | 13 | 0 | 0 |
| Near-duplicate ≥ 0.8 | **30** (0.80%); 31 train questions | 0 | 0 |
| Near-duplicate ≥ 0.7 | 57 (1.53%) | 0 | 0 |
| Near-duplicate ≥ 0.5 | 192 (5.15%) | 0 | 0 |
| Best Jaccard per b item: median / p90 / p99 / max | 0.219 / 0.417 / 0.764 / 1.0 | 0.072 / 0.119 / 0.274 / 0.326 | 0.108 / 0.168 / 0.241 / 0.396 |
| Laws shared (a has 35) | **21 of 21** | 4 of 4 | n/a (notices, not statute) |
| Gold sections shared | **2,659 of 3,582** (74.2%) | 56 of 59 | n/a |
| b items whose gold section is a train positive | **2,806** (75.2%) | 50 any, 47 all | n/a |
| Train records with a positive among b gold sections | 5,934 (72.3%) | 151 | n/a |
| b items with a near-dup ≥ 0.8 **and** the same gold section | 22 | 0 | n/a |

**Reading.**
- Question text rarely repeats: 7 normalised duplicates and 30 near-duplicates at 0.8 among 3,729 CCL questions.
- The **source overlap is massive.** Every CCL law and three quarters of the CCL gold sections are WangchanX train
  positives.
- So any model trained or tuned on WangchanX train has seen the gold sections of most CCL items. This includes the
  specialists listed in P3-T01 §5. A section-level split would leak on sections and laws, so packets-v1 splits by law.
- The Gazette and Tax questions show no question overlap with WangchanX train.

**Other audit lines.**
- WangchanX train, internally: 8 normalised duplicate groups (17 records) and 24 near-duplicate pairs at 0.8
  (45 records).
- NitiBench CCL configured shard vs the non-config copy `nitibench-ccl.parquet`:
  - 7 rows differ positionally in raw question text;
  - the normalised multisets are equal;
  - the configured shard remains the pin.
- After the split, the highest Jaccard between any DEV question and any held-out question (CCL, Tax, Gazette) is
  **0.4565**. No DEV question equals a held-out question after normalisation.

## 3. Packets

| | DEV | Held-out |
|---|---|---|
| Items | **1,330** (WangchanX train) | **3,779** (NitiBench ccl 3,729 + tax 50) |
| Synthetic vs real | all `synthetic_question_real_source` (Gemini 1.5 Pro questions, real statute text) | all `real` (ccl: expert-written; tax: Revenue Department ruling cases) |
| Families (= laws) / with items | 14 / 12 | 22 / 21 |
| Items per family (descending) | 379, 312, 205, 194, 80, 52, 42, 29, 19, 7, 6, 5, 0, 0 | 1,621, 529, 295, 186, 165, 153, 110, 109, 78, 74, 73, 64, 58, 48, 40, 38, 36, 36, 33, 22, 11, 0 |
| Sources (statute sections) | 734 | 4,393 |
| Gold sections per item | 1: 870, 2: 259, 3: 107, 4: 68, 5: 26 | 1: 3,748, 2: 8, 3: 13, 4: 5, 6: 2, 7: 1, 9: 2 |
| Gold source outside the statute corpus | 0 | 0 |

**Task types.** These are lexical cue rules (`TASK_RULES` in the builder) on the question and on the gold source (text,
id, and the statute `reference` field). The basis of every tag is stored, and one item can carry several types.

| Task type | DEV: any cue | DEV: question cue | Held-out: any cue | Held-out: question cue |
|---|---|---|---|---|
| binding (cross-reference / exception) | 519 | 41 | 1,634 | 124 |
| annex | **0** | 0 | 56 | 5 |
| table | **0** | 0 | 34 | 3 |
| date (question only, by rule) | 81 | 81 | 573 | 573 |
| plain (no cue) | 767 | — | 1,825 | — |

**DEV has no annex or table items.** The annex and table material is the Revenue Code stamp-duty schedule, and that law
is held out. So the owner's priority on annex and table tasks cannot be met from this DEV pool. It needs authored or
licensed packets (§5).

**DEV exclusions** (8,211 → 1,330):
- 6,809 records: a positive law is held out (`heldout_family_quarantine`);
- 72 records have no positive judgment;
- 0 held-out variants remained after the law quarantine;
- 696 hard negatives in held-out laws were dropped from DEV judgments.

The 22 held-out laws include 1 that appears only in `reference_laws`. No law name was left unmapped.

**Judgments and their independence.**
- Every judgment is the dataset's own gold, and its origin is recorded on each record:
  - DEV: WangchanX `positive_contexts`, which are BGE-M3 candidates filtered and reranked by legal experts;
    `hard_negative_contexts` are the expert-removed candidates;
  - held-out: NitiBench `relevant_laws`.
- No PTP policy output, model or judge created or changed a label (`independent_of_tested_policy: true`).
- **Pooling caveat:** the DEV positives were pooled by BGE-M3, so a BGE-M3-based arm has a pooling advantage on DEV.
  This is recorded per judgment. CCL gold is not pooled (the question was written from the section). Tax gold is the
  laws cited by the ruling.

**Provenance.** Each request and source carries:
- dataset, revision, licence and file;
- the positional locator (`train[i]`, `ccl[i]`, `tax[i]`, `statute_ccl/<law>/<section>`);
- a record-id hash: sha256 of `repo@revision:locator`;
- for sources, also the text sha256 and the statute cross-references.

Licences: WangchanX MIT, NitiBench MIT, statute MIT. The Gazette (CC BY 4.0) is not packetised.

**Output files** (`packets-v1/`, sha256 prefixes; full values in its `SHA256SUMS` and in the summary JSON):

| File | Records | sha256 |
|---|---|---|
| `dev/requests.jsonl` (runtime input: question + provenance, no gold) | 1,330 | `86a1f2573ead` |
| `dev/sources.jsonl` | 734 | `d5505a194b2d` |
| `dev/judgments.jsonl` | 1,330 | `877e3b464bbf` |
| `dev/packets.jsonl` | 14 | `7adea502e8d1` |
| `heldout/requests.jsonl` | 3,779 | `d706a44dfdc1` |
| `heldout/sources.jsonl` | 4,393 | `1a6cde42029e` |
| `heldout/judgments.SEALED.jsonl` (evaluator-only) | 3,779 | `06c0760a9f1b` |
| `heldout/packets.jsonl` | 22 | `41f06973af23` |
| `excluded.jsonl` (hash, locator, reason; no text) | 6,881 | `dac9bf1947a7` |
| `overlap_audit.json` | — | `7e5a3f8bebbc` |
| `MANIFEST.json` | — | `cb00f98c5969` |

## 4. Held-out handling

- **NitiBench ccl and tax** were read by the builder only, for three purposes:
  - question text, for the overlap audit;
  - `relevant_laws` and `reference_laws` law names and section numbers, to separate families and write the sealed
    judgments;
  - the gold section text of items, for the task-type cues stored with the sealed judgments.
- No agent printed or inspected held-out rows. Only aggregates were viewed. Nothing was scored, and nothing selects a
  method. `heldout/judgments.SEALED.jsonl` may be opened only to score a frozen method (D18).
- **Gazette:** the builder read the query text column only. Qrels, spans and model fields were not read. The Gazette
  stays its own scoreboard (P3-T01 §3) and remains an exposed public transfer.

## 5. NOT_RUN and limitations

- **NitiBench+** (gated, not accepted) is not covered.
- **Gazette packetisation:** NOT_RUN. It has no DEV part, and packetising would only re-read its sealed qrels. Its
  native qrels remain its judgments.
- **Fresh structural packets / supplied document tasks** (P3-T01 resource `PTP_authorized_thai_packets`): NOT_RUN. This
  is the only route to DEV annex and table tasks.
- **dr-train copy** of `thai-data/` and `packets-v1/`: NOT_RUN. dr-train was unreachable on 23 Nov. Target:
  `/data/ptp-paper2/thai-data/`, verified with `sha256sum -c`.
- **Task-type tags** are lexical cue rules, not expert annotation. Precision was not measured. The date cue is
  question-only by design. Binding mostly comes from the statute `reference` field.
- **DEV representativeness.** DEV covers 14 smaller CCL laws (median 24.5 statute sections per law), all with
  LLM-generated questions. Held-out covers 22 larger laws (median 84.5 sections) with expert or real questions. A DEV-to-held-out gap therefore mixes law domain, question origin and
  pooling. This must be stated in any P3 result.
- **Specialist models** trained on WangchanX train have seen about 75% of the CCL gold sections (§2). They are
  specialist comparators only (P3-T01 §5).
- Answers (`positive_answer`, NitiBench `answer`) are not packaged. These packets are retrieval and evidence judgments
  only. Judge-graded answer scores stay governed by rule 12.
