# P2-OA step R1: eligible tasks, temporal splits and corpus size

Status: DONE (2026-11-16). The rule was committed (edfb00e) before the first run; results follow it. Step R1b (`oa_splits_v2_addons.py`) aligns with merged plan v2 (open-population corpus, RPD/OAER, claim check). R1b was declared in 71fa5a1 and amended once in f3128bc (see section R1b).

No retrieval, no model, no text, no new download. CPU only.
- Scripts: [`oa_temporal_splits.py`](oa_temporal_splits.py) (R1) and [`oa_splits_v2_addons.py`](oa_splits_v2_addons.py) (R1b).
- Aggregates: [`oa-splits.json`](oa-splits.json) and [`oa-splits-v2.json`](oa-splits-v2.json). [`oa-splits-v2-run1-asdeclared.json`](oa-splits-v2-run1-asdeclared.json) is kept as the superseded first R1b output.
- CPU receipts: [`remote-cpu.jsonl`](remote-cpu.jsonl).
- Raw per-application tables (`tasks.tsv`, `pairs.tsv`) stay on the remote only, in `/data/ptp-paper2/splits/private/` (mode 700).

## Task definition (merged plan 3.1, made exact)

- One task = one US application. Its office action is the **earliest non-final rejection** (`document_cd = CTNF`) in the OA Research Dataset 2017, ordered by (mail date, ifw number).
  - The dataset only holds application series 12-15, so this is the first non-final rejection the application received, provided it was mailed before the dataset ends (mid-2017).
- It must be mailed 2008-01-01 to 2017-12-31.
- K(q) = the distinct US documents cited **in that action** with `citation_in_oa = 1` and `action_type` 102 or 103.
  - Foreign or unparsed cited art is counted but cannot enter K.
- Eligible if all four hold:
  - |K| ≥ 3;
  - the application has an IPC;
  - at least one K document is OUT under IPC3 (no shared IPC3 with the application; the cited side needs an IPC);
  - a filing date is known.
- If the first non-final rejection does not qualify, the application is not a task. A later action is never searched for, so the task set is not selected on its labels.

## Cut-point rule (declared before the first run; no retrieval number exists)

Facts seen before this rule was written:
- the dataset holds application series 12-15 only;
- office actions per mail year: 2008: 6,837; 2009: 66,926; ... 2016: 748,472; 2017: 178,408 (half year).

The eligible-task histograms below had not been computed when the rule was written.

| # | Rule |
|---|---|
| R1 | Temporal key = application filing date from PatentsView (pre-grant record first, else grant record). |
| R2 | Observation completeness per filing year Y: c(Y) = share of series 12-15 applications filed in Y (known to PatentsView) that have at least one CTNF in the dataset. Y is **complete** if its denominator is ≥ 10,000 and c(Y) ≥ 0.9 × max c. Incomplete years are excluded from every split and reported. They are right-censored by the mid-2017 end of the data, or only partly covered by series 12-15. |
| R2a | Only the contiguous run of complete years ending at the newest complete year is used. |
| R3 | **P3-TEST** = the newest complete year. It is extended backward by whole years until it holds ≥ 1,000 eligible tasks. |
| R4 | **P2-TEST** = the next older block of whole years, built the same way (≥ 1,000). |
| R5 | **DEV** = all remaining older years of that run. |
| R6 | A test window is a pool. The evaluated test sample is the first n tasks of the window, ordered by sha256(`p2-oa-split-v1|` + app_id). n is fixed later by the MDE rule of the pre-declaration. Corpus size is therefore reported per window **and** for n = 1,000 / 2,000 / 5,000. |

Why completeness and not only size:
- A window of ≥ 1,000 tasks is easy to reach; each filing year has tens of thousands.
- The binding problem is right-censoring. Applications filed in 2015-2016 appear only if they got their first action before mid-2017.
- That keeps fast art units and drops slow ones, so a test window made of censored years would not be a fair sample.

## Encoding-cost scale

Measured on DAPFAM (stage 0, 2026-11-05), PatEmbed-large fp32 on the V100:
- 188,944 passages from 45,336 families took **5,182 s (1.44 h)**, i.e. 36.5 passages/s and 4.17 passages per family.
- The merged plan's "well under 1 h" was wrong; the estimates below use the measured rate.
- fp16 has not been measured.

## Results R1 (rule applied as declared)

### Eligibility funnel

| Step | Applications |
|---|---|
| with at least one CTNF in the dataset | 2,169,879 |
| first CTNF mailed 2008-2017 | 2,169,870 |
| first CTNF cites ≥ 1 US document under 102/103 (`citation_in_oa = 1`) | 1,795,745 |
| ... ≥ 3 such documents | 740,853 |
| ... and the application has an IPC | 739,082 |
| ... and ≥ 1 cited document is OUT under IPC3 = **eligible tasks** | **378,109** |

All eligible tasks have a filing date. A probe of the first 3M 102/103 citation rows found that 100% join an office action by (app_id, ifw_number).

### Completeness by filing year, and the cut points

c(Y) = share of the year's series 12-15 applications (known to PatentsView) that have a CTNF in the dataset. Years with a denominator under 10,000 are not shown.

| Filing year | Denominator | c(Y) | Eligible tasks | Complete (c ≥ 0.9 × 0.830 = 0.747) |
|---|---|---|---|---|
| 2006 | 23,533 | 0.811 | 3,055 | yes |
| 2007 | 61,790 | 0.817 | 8,119 | yes |
| 2008 | 326,454 | 0.805 | 46,608 | yes |
| 2009 | 309,103 | 0.772 | 42,594 | yes |
| 2010 | 322,279 | **0.668** | 38,701 | **no** |
| 2011 | 347,917 | 0.830 | 52,806 | yes |
| 2012 | 373,296 | 0.823 | 54,074 | yes |
| 2013 | 394,048 | 0.800 | 55,307 | yes |
| 2014 | 400,654 | 0.651 | 45,110 | no (censored) |
| 2015 | 401,695 | 0.389 | 24,898 | no (censored) |
| 2016 | 386,671 | 0.131 | 6,595 | no (censored) |

- Right-censoring starts in 2014, as expected from the mid-2017 end of the data.
- **Filing year 2010 has an unexplained dip** (0.668, against about 0.80 on both sides). Under R2a it cuts the contiguous run, so 2006-2009 are excluded although they are complete.
  - The rule was applied as declared and was not changed after seeing this.
  - The cause is not known and not investigated here. Candidates: missing office-action documents in the 2017 release, or a series 12/13 numbering transition.
  - If the owner wants a larger DEV pool, a separate, explicitly post-hoc decision could add 2006-2009 as a second DEV block, labelled as such. DEV is development-only, so no test window is affected.

**Cut points (R3-R5): DEV = filing year 2011, P2-TEST = 2012, P3-TEST = 2013.**
- Excluded: 215,922 eligible tasks in incomplete or non-contiguous years.
- Eligible tasks by first-action mail year: 2008: 807; 2009: 7,905; 2010: 22,506; 2011: 47,099; 2012: 57,097; 2013: 56,238; 2014: 54,771; 2015: 61,189; 2016: 59,007; 2017: 11,490.

### Per-split table

Shares are over (task, cited document) pairs.

| | DEV (2011) | P2-TEST (2012) | P3-TEST (2013) |
|---|---|---|---|
| tasks | 52,806 | 54,074 | 55,307 |
| (task, cited) pairs | 230,703 | 236,008 | 240,940 |
| distinct cited documents | 211,156 | 217,217 | 220,368 |
| ... with a PatentsView record | 200,776 | 207,503 | 211,463 |
| 102 only / 103 only / both | 5.2% / 84.2% / 10.6% | 5.2% / 84.6% / 10.2% | 5.6% / 84.8% / 9.6% |
| OUT3 / IN3 / cited side without IPC | 43.3% / 48.1% / 8.6% | 42.6% / 49.5% / 7.9% | 43.7% / 49.0% / 7.3% |
| OUT4 / section mismatch | 51.2% / 25.9% | 50.9% / 25.7% | 52.2% / 27.1% |
| K per task: mean / median / p90 | 4.37 / 4 / 7 | 4.36 / 4 / 7 | 4.36 / 4 / 6 |
| OUT3 per task: mean / median; tasks with ≥ 3 OUT3 | 1.89 / 2; 12,325 | 1.86 / 1; 12,049 | 1.90 / 2; 13,152 |
| other (unjudged) US citations per task: mean / median | 25.6 / 9 | 23.9 / 8 | 23.8 / 7 |
| art units; largest art-unit share; art units with ≥ 20 tasks | 577; 1.4%; 498 | 578; 1.4%; 500 | 569; 1.1%; 496 |
| technology centres | 18 | 20 | 18 |
| primary IPC4 subclasses; largest share | 563; 11.6% | 569; 11.5% | 557; 9.7% |
| AIA tasks (proxy: filed ≥ 2013-03-16) | 0 | 0 | 39,795 (72%) |
| first-action 102/103 rejection covers claim 1 | 46,747 (88.5%) | 48,034 (88.8%) | 49,326 (89.2%) |

Known bug in `oa-splits.json`:
- The field `share_noipc_cited`, and `NOIPC` in `pair_counts`, count each no-IPC pair three times (once per domain rule). The table shows the corrected value, one third of the stored share; OUT3 + IN3 + no-IPC then sums to 100%.
- No other field is affected. The JSON is left as produced.

Why OUT3 is so high:
- The eligibility rule (≥ 1 OUT3 reference) selects OUT-rich tasks. OUT3 is about 43% of pairs here, against 24.7% in the full 102/103 census.
- Pairs whose cited side has no IPC count as neither IN nor OUT, so OUT3 is a lower bound.

Notes:
- **AIA heterogeneity.** P2-TEST is entirely pre-AIA, while P3-TEST is 72% AIA. The OAER rule differs between them, and the report must state it.
- **Clusters.** There are about 570 art units per split, none above 1.5% of tasks. The art unit works as the cluster unit for the bootstrap and for power (merged plan v2, section 5.5).

### Family / continuation chains across splits

The exact chain is **not detectable** with the downloaded files: the PatentsView related-document / continuity tables are not downloaded, and that needs owner approval. Proxies:

| Proxy | DEV | P2-TEST | P3-TEST |
|---|---|---|---|
| K pairs whose cited document is the application of a task in a **later** split (filed later yet cited, so almost certainly an earlier-priority chain) | 162 (to P2: 135, to P3: 27) | 113 (to P3) | 0 |
| K pairs whose cited document is a task application in an earlier split | 0 | 2,673 (DEV) | 4,138 (DEV) + 2,714 (P2) |
| tasks sharing an exact normalised title + primary IPC4 with a task in another split (upper bound; generic titles inflate it) | 5,047 (9.6%) | 5,383 (10.0%) | 5,526 (10.0%) |
| cited documents shared with another split | DEV∩P2 21,354; DEV∩P3 20,265 | P2∩P3 22,474 | |

- The first row is the clearest evidence that chains cross splits, but it is small (≤ 0.07% of pairs).
- Earlier-split citations are expected temporally: the test target is then a DEV query's own document. That is not leakage for a method without training, but it is disclosed.
- Before the freeze, either the continuity tables are downloaded (owner approval) and chains are removed, or the paper states this limit with these numbers.

### Closed-world corpus size (cited documents + distractors)

| Split | Whole window, 1:1 / 1:3 docs | n = 1,000 sample, 1:3 | n = 2,000, 1:3 | n = 5,000, 1:3 |
|---|---|---|---|---|
| DEV | 422k / 845k | 17.5k docs | 34.5k | 86.8k |
| P2-TEST | 434k / 869k | 17.4k | 35.1k | 86.8k |
| P3-TEST | 441k / 881k | 17.6k | 35.2k | 87.0k |

At 31.8 V100-h per million documents (below), a 1:3 closed-world corpus costs about 0.6 h per 1,000-task sample, and about 28 h for a whole window.

## Results R1b (merged plan v2)

### Amendment 1 (before any retrieval)

- R1b run 1 admitted only pre-grant publications typed `utility`.
- PatentsView types every 2001-2004 pre-grant publication `new`: about 751,000 documents, 117,561 of them cited in K. Run 1 therefore dropped them silently.
- Amendment 1 (f3128bc) admits types `utility`, `new` and `new-utility`. Membership still depends on type and date only.
- Run 1 output is kept in [`oa-splits-v2-run1-asdeclared.json`](oa-splits-v2-run1-asdeclared.json). In it, OUT3 RPD coverage for start 1976 was 0.82-0.84 instead of 0.93-0.94.

Cited documents with no PatentsView record: 65,748.
- 65,329 have numbers ≤ 3,930,270, i.e. grants before 1976, which PatentsView does not hold.
- 241 pre-grant publication numbers, 125 later patent numbers and 53 other prefixes are unresolved.

### Temporal settings: cited references excluded per split (share of K pairs)

| | DEV | P2-TEST | P3-TEST |
|---|---|---|---|
| RPD excludes (published on/after the task's filing date) | 6.9% (OUT3 6.5%) | 6.3% (OUT3 6.0%) | 6.3% (OUT3 5.7%) |
| OAER excludes (published later **and** US-filed on/after the task's filing date) | 0.69% | 0.62% | 0.64% |
| date unknown (no PatentsView record; mostly pre-1976) | 4.6% | 4.2% | 3.8% |

- About 6% of examiner-cited references are later-published, earlier-filed US documents (102(e) / 102(a)(2) art). RPD removes them and OAER keeps them.
- OAER uses US filing dates as a proxy. Foreign priority and AIA transition cases cannot be resolved here.

### Open-population corpus: size and gold coverage

Definitions:
- **Population** = US utility and reissue grants plus utility pre-grant publications (types `utility`/`new`/`new-utility`), published from the start year until the split's upper date.
  - RPD upper date: 2011-12-31 / 2012-12-31 / 2013-12-31.
  - OAER upper date: the latest first-action mail date, 2017-06/07.
- **Unit:** a pre-grant publication and its grant count once (application-level unit). The unit's date is its first publication.
- **Coverage** = share of K pairs whose cited document is in the population and visible in the setting.

| Split | Start | RPD units | OUT3 RPD coverage | ALL RPD coverage | OUT3 OAER coverage (OAER units) | V100 fp32 hours to encode RPD units* |
|---|---|---|---|---|---|---|
| DEV | 1976 | 5.75M | 0.935 | 0.884 | 0.993 (7.86M) | 182 |
| DEV | 1990 | 4.78M | 0.853 | 0.819 | | 152 |
| DEV | 2001 | 3.52M | 0.683 | 0.676 | 0.741 | 112 |
| DEV | 2005 | 2.32M | 0.462 | 0.488 | | 74 |
| P2-TEST | 1976 | 6.10M | 0.940 | 0.894 | 0.994 (7.88M) | 194 |
| P2-TEST | 1990 | 5.13M | 0.866 | 0.836 | | 163 |
| P2-TEST | 2001 | 3.87M | 0.713 | 0.708 | 0.768 | 123 |
| P3-TEST | 1976 | 6.46M | 0.943 | 0.899 | 0.994 (7.88M) | 205 |
| P3-TEST | 1990 | 5.50M | 0.879 | 0.847 | | 175 |
| P3-TEST | 2001 | 4.23M | 0.747 | 0.735 | 0.798 | 134 |

\* Assumes DAPFAM passage density (4.17 passages per document) at the measured fp32 rate (36.5 passages/s), i.e. **31.8 V100-hours per million units**.
- Patent text (title + abstract + claims) may have a different density; re-measure on a 10k sample (merged plan section 8).
- fp16 is not measured.

What this means:
- **G2.0 (OUT coverage ≥ 80%) is met only with start year 1976 or 1990.** Starting in 2001 gives 68-75%.
- The RPD populations are nested by date. One encoding of the P3-TEST population serves all three splits in RPD:
  - start 1990: 5.5M units, about 175 V100-h fp32;
  - start 1976: 6.5M units, about 205 h.
- OAER needs publications up to 2017-07: 7.9M units, about 250 h.
- This is **about 10× the merged plan's 5-20 GPU-h estimate**. That estimate assumed 0.3-1.0M documents and "well under 1 h" for DAPFAM, which actually took 1.44 h.
- **Hash-sampling the population destroys coverage.**
  - A 25% sample of units gives OUT3 RPD coverage of 0.17-0.19 (start 2001); 50% gives 0.34-0.37.
  - The realistic choices are the full population (≈ 175-250 V100-h, or RunPod) or a narrower label-independent population, for example restricted by publication window.
  - Restricting by IPC section conflicts with the cross-domain question, because OUT references sit outside the query's classes by definition.
- Tasks with zero covered OUT3 references in RPD:
  - start 1976: 3.7% / 3.4% / 3.0%;
  - start 2001: 20.6% / 18.4% / 15.7%.
- Coverage by basis (P2-TEST, RPD, start 1976): 102 only 0.861, 103 only 0.897, both 0.886. 102 references have more missing records (7.0% date unknown).

### Claim-version check

- The first CTNF is by construction the first action, so no response amendment can precede it.
- Preliminary amendments (filed before the first action) are not recorded in `office_actions`/`rejections`. The share "first action precedes any amendment" therefore **cannot be measured** with these files; it needs file-wrapper transaction data (e.g. ODP/PEDS transactions, which need download approval).
- Measurable proxy: in 88.5% / 88.8% / 89.2% of tasks, the first action's 102/103 rejection covers claim 1. Every task joined its rejection rows.
- The published claims (the query text) can still differ from the examined claims through a preliminary amendment after publication. This remains a limitation until transaction data are available.

## Cost of this step

- CPU only, run with `nice -n 15` on dr-train.
- Total measured CPU 1,495 s (user + sys) over six remote runs:
  - a join probe;
  - one failed R1 launch (0.2 s; the input link was missing and no data was processed);
  - the R1 run;
  - R1b run 1 (superseded);
  - a type diagnostic;
  - the amended R1b run.
- Peak RSS 9.0 GB. No model calls, no GPU, no download, USD 0.
