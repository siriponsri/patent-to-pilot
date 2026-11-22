# P2-T01 — Audit of eligible content and available structural evidence

**Status:** COMPLETE (22 Nov 2026). **Evidence class:** read-only data audit. These are counts, not retrieval results.
**Spend:** USD 0. CPU only on dr-train (`CUDA_VISIBLE_DEVICES` empty, `nice -n 15`). No GPU, no training, no download,
no paid call. **TEST isolation:** no TEST block, `sealed/`, `splits/private/pairs.tsv` or per-query TEST output was
opened. See §6 for how the OA citation table was filtered.
**Scope:** the P1/G03 BridgeRet setting. That means the Challenge-1M corpus (1,000,000 units), P1-DEV (26,575 tasks)
and VAL (2,000 tasks) queries, and the four G03 routes L (BM25), Q (Qwen3), P (PatEmbed) and A (Arctic). DAPFAM (G04)
is **not** audited here.

## 0. Answer in one paragraph

The current representation omits eligible content **by construction**, not only through truncation.
- Every route, BM25 included, indexes only **title + abstract + the first independent claim**, capped at 512 tokens.
- The other claims of each document are already on disk (PatentsView claims, downloaded 18 Nov) but are never indexed.
  In the corpus, the median document has 19 live claims and 3 independent claims. The current 512-token text holds a
  median of only **~12% of a document's claim tokens** and **~23% of its title + abstract + all-claims tokens**.
  This holds for all three tokenizers.
- Truncation on top of that is moderate. Arctic cuts the first-claim tail of 16.6% of corpus units and 9.5% of
  P1-DEV/VAL queries; Qwen3 cuts 8.0% and 4.7%; PatEmbed cuts 7.0% and 3.2%. **BM25 reads the Arctic-truncated
  text**, so it inherits Arctic's truncation.
- The description is **absent from disk**. Adding it would need a per-item download approval.

**Conclusion:** the owner rule ("skip rebuild if no coverage gap") does **not** apply. A claims-complete rebuild is a
valid P2-T02 candidate, as an engineering control with an equal-content flat comparison. Several structural relations
are available on disk without downloads: claim dependency, IPC, US continuity, dates and OA-2017 examiner citations.
CPC, front-page citations, descriptions and international (DOCDB) families are absent.

## 1. Source fields and what each route actually encodes

**Raw text table** `bridgeret/texts-v1/corpus.jsonl` (built by `code/build_bridgeret_texts.py`):

- **Record keys** (identical for all 1,000,000 rows): `unit, doc, title, abstract, claim, claim_variant`.
  - `claim` is **one** claim. It is the lowest-numbered claim whose PatentsView `dependent` field is empty and whose text
    has no dependency reference, and which is not cancelled.
- **Not in the record:** other claims, description, CPC/IPC, citations, family id and dates.
  - Dates exist separately: `first_pub` is in `challenge1m/out-v1/corpus-units.tsv` and is used only for the
    date mask.

| Field (corpus, n = 1,000,000) | Non-empty | Chars p50 / p90 / p99 / max |
|---|---|---|
| title | 1,000,000 | 52 / 97 / 154 / 600 |
| abstract | 999,485 (515 missing) | 721 / 1,127 / 1,626 / 57,192 |
| first independent claim | 999,997 (`first_independent` 999,916; `claim_fallback_claim1` 81; `no_claims` 3) | 742 / 1,526 / 2,818 / 304,483 |
| **all live claims** (PatentsView, not indexed) | 999,997 docs have claim rows | **5,544 / 12,596 / 28,345 / 1,883,330** |
| description / brief summary | **absent from disk** (no `g_detail_desc_text*`, `g_brf_sum_text*`, `pg_*` equivalents) | — |

**Queries** (`texts-v1/queries.jsonl`, P1-DEV + VAL only):
- Each query is the earliest pre-grant publication of the task application, with the same three fields.
- 25,626 of 26,575 P1-DEV and 1,919 of 2,000 VAL tasks have a pre-grant publication. The remaining **949 + 81 tasks
  have no query text**, so they are absent from every run and score 0.
- Query first-claim chars: p50 654, p90 1,295. All live claims of a query: p50 5,087, p90 9,731.

**What each route encodes:**

| Route | Serialised input (exact command in §7) | Text | Cap | Model's own limit |
|---|---|---|---|---|
| A Arctic-embed-m-v2.0 (CLS) | `ser-arctic-v1` (`serialise_bridgeret_texts.py`, query prompt `query: `) | title\nabstract\nfirst indep. claim | 512 Arctic tokens (claim tail cut first, then abstract; title never) | 8,192 positions (**cap is a configuration choice**) |
| Q Qwen3-Embedding-0.6B (last token) | `ser-qwen3-v1` (instruct prompt counted on the query side) | same | 512 Qwen3 tokens | 32,768 positions (**configuration choice**) |
| P PatEmbed-large (mean) | `ser-patembed-v1` (`_v2`; query and document prompts both counted) | same | 512 BERT tokens | 512 (**hard limit**) |
| L BM25 (k1 1.5, b 0.75) | **`ser-arctic-v1`** (`bm25.time`: `bm25_bridgeret.py ser-arctic-v1 …`) | same | **inherits the Arctic 512-token cut** | none intrinsic |

All dense encoders also call the tokenizer with `truncation=True, max_length=512`. The serialised lengths are already
at most 512 (max `ntok` = 512 in every file), so the encoder applies no further cut.

## 2. Truncation (full population, actual tokenizers, from the stored serialisations)

The serialised files record how many tokens were removed. They were joined row by row with `texts-v1`, and every unit
and app_id was checked equal (audit 1).

| Route tokenizer | Corpus units truncated | first-claim tokens removed when cut (p50 / mean) | first-claim chars kept when cut (p50) | abstract also cut (= first claim fully removed) | P1-DEV+VAL queries truncated |
|---|---|---|---|---|---|
| Arctic (also BM25) | **16.61%** (166,143) | 95 / 151.1 | 72.0% | 0.13% | **9.49%** (2,615 / 27,545) |
| Qwen3 | 8.04% | 83 / 153.3 | 76.5% | 0.06% | 4.69% |
| PatEmbed | 7.05% | 86 / 153.7 | 75.6% | 0.04% | 3.24% |

- **What is cut:** always the tail of the first independent claim. The title is never cut.
- The Arctic figures reproduce the 18 Nov report `bridgeret/truncation-arctic-full-v1.json` (corpus 0.1661; P1-DEV
  0.0939; VAL 0.1084).

**What the cap and the field choice exclude together** (tokenized with the real tokenizers on CPU):
- **Sample:** 20,000 corpus units, 2,000 P1-DEV queries and all 1,919 VAL queries. Units were drawn by ascending
  `sha256('p2t01-v1|'+id)`.
- **Prompts:** as configured. The document prompt is used for PatEmbed and the query prompts for queries.

| Tokenizer, side | title+abstract+**all** claims > 512 | full-content tokens p50 / p90 / p99 | 512-windows needed p50 / mean / p99 | share of claim tokens inside the current 512 text, p50 (mean) | share of title+abstract+all-claims tokens inside it, p50 (mean) |
|---|---|---|---|---|---|
| Arctic, corpus | **96.1%** | 1,461 / 3,050 / 6,521 | 3 / 3.98 / 13 | 12.0% (16.8%) | 22.9% (27.4%) |
| Arctic, P1-DEV | 98.0% | 1,329 / 2,435 / 5,024 | 3 / 3.48 / 10 | 12.4% (15.0%) | 23.4% (26.1%) |
| Arctic, VAL | 97.3% | 1,360 / 2,424 / 4,935 | 3 / 3.51 / 10 | 12.0% (14.9%) | 23.4% (26.3%) |
| Qwen3, corpus | 93.4% | 1,246 / 2,617 / 5,670 | 3 / 3.49 / 12 | 12.2% (17.3%) | 22.9% (27.6%) |
| Qwen3, P1-DEV | 96.3% | 1,153 / 2,052 / 4,371 | 3 / 3.08 / 9 | 12.3% (15.0%) | 24.1% (26.9%) |
| PatEmbed, corpus | 92.5% | 1,192 / 2,493 / 5,369 | 3 / 3.34 / 11 | 12.6% (17.8%) | 23.6% (28.4%) |
| PatEmbed, P1-DEV | 94.6% | 1,086 / 1,961 / 4,107 | 3 / 2.92 / 9 | 12.7% (15.5%) | 23.8% (26.6%) |

The same picture holds as a character proxy over the **full** populations (audit 2). The first independent claim is a
median of 13.0% of a document's live-claim characters (mean 18.6%) in the corpus, 12.7% in P1-DEV and 12.5% in VAL.

**Description length:** cannot be measured, because the text is not on disk.

## 3. Unit and family aggregation

**What a unit is:** one US application. A grant and its pre-grant publication count once.
- 999,951 `A:` units, plus 49 `D:` units (cited documents that could not be mapped).
- `rep_doc` is the earliest publication: a pre-grant publication for 643,111 units and a grant for 356,889.
- For the 461,294 units that have both, the indexed text is the **as-published application** (PG claims); the granted
  claims are not used.
- Units are **not** families. There is no family id in the corpus, and the evaluator (`eval_bridgeret_dev.py`) scores
  units.

**US continuity among corpus units** (rule copied from `build_continuity_related.py`):
- **Primary rule** (continuation, CIP, division, substitution, reissue): **100,976 units (10.1%)** sit in **38,587**
  components that hold at least 2 corpus units. Size histogram: 2 → 29,311; 3 → 5,195; 4 → 1,798; ≥10 → 440;
  maximum 269.
- **With shared provisionals:** 115,936 units (11.6%) in 42,488 components; maximum 302.

**Exact duplicates** (lower-cased text, over 1M units):
- 7,161 units in 3,495 groups have an identical title+abstract+first claim (maximum group 8).
- 10,501 units share an identical first claim.
- 55,958 units share an identical abstract (typical of continuation chains).

**Query–TRAIN near-duplicates** (earlier audit `audits/lc-v1`): 0.53% of P1-DEV and 0.21% of VAL.

**Implication:** sibling applications occupy separate slots in a top-200 list. The owner method note asks for family
deduplication before final scoring. That needs a declared family rule and a protocol amendment; the current G03
evaluator has neither.

## 4. Structural evidence available without new downloads (corpus = 1M units; queries = P1-DEV/VAL only)

| Evidence | Source on disk | Coverage |
|---|---|---|
| **All claims + dependency structure** | `patentsview/claims/{g_claims_1976–2013, pg_claims_2001–2016}` (54 files), `dependent` = e.g. "claim 1" | **Corpus:** 999,997 docs have claim rows. Live claims p50 19 / p90 38; independent claims p50 3 (mean 3.28); 79.2% have more than one independent claim; 97.8% have at least one `dependent` field; 99.9% of dependent references resolve to a claim of the same document; 138,969 dependent claims carry no field and are detected only by regex; 88,170 cancelled rows. **P1-DEV:** 99.3% have dependent fields, 78.6% have more than one independent claim, 99.98% resolve. **VAL:** 98.9%, 79.1% and 99.98%. |
| **IPC** (not CPC) | `g_ipc_at_issue`, `pg_ipc_at_issue` | 982,907 units (98.3%) have an IPC on some document of the unit; on the rep_doc itself, 939,744 (94.0%). Distinct subclasses per unit: p50 1, mean 1.47. Distinct main groups: p50 1, mean 1.85. |
| **CPC** | — | **Absent** (no `*_cpc_*` table). `panorama/panorama.parquet` lists `cpcClassificationBag`, but only for examined applications. It was not opened (pyarrow is missing on dr-train) and is not corpus-wide. |
| **Dates** | `corpus-units.tsv`, `g_application`, `pg_published_application` | `first_pub` 100% (1976–2012). Filing date for all 999,951 `A:` units. 816,432 units have a grant, 644,813 have a pre-grant publication, and 461,294 have both. |
| **Families** | `g_us_rel_doc`, `pg_us_rel_doc` | US continuity only (§3). Edges from corpus units: continuation 260,165; CIP 341,197; division 126,756; provisional 389,770. **No international or DOCDB family table.** |
| **Cited references (front page)** | — | **Absent** (no `g_us_patent_citation` / `g_us_application_citation`). |
| **Examiner/applicant citations made by corpus units** (OA Research Dataset 2017) | `oa2017/citations.csv.zip` | Present for **175,830 units (17.6%)**. Distinct refs per citing unit: p50 12, p90 55. 5,033,070 refs, of which 2,194,364 resolve to a corpus-unit document; 165,395 citing units have at least one in-corpus ref. **Of the citing units, 41,156 are themselves tasks** (tasks.tsv split DEV 6,580 and EXCLUDED 34,576; VAL is in EXCLUDED). Their outgoing citations are those tasks' labels. |

## 5. Conclusion for P2-T02 and P2-T03

**P2-T02: rebuild candidate, do not skip.**

- **Eligible, on-disk, unindexed content:** all non-first claims. They are about 77% of a document's
  title+abstract+claims tokens and about 88% of its claim tokens (medians, all three tokenizers).
- **Smallest honest rebuild:** claim-complete passages per unit, under the same tokenizer, date mask, own-unit mask,
  unit aggregation and final cutoff.
  - Structural arm: title+abstract plus each independent claim with its dependent claims, parent-linked.
  - **Equal-content flat control:** the same text split into fixed 512-token windows.
  - **Full-text BM25** over title+abstract+all claims, which needs no cap.
  - Cap or normalise passage multiplicity before taking the unit maximum (owner note).
- **Deeper retrieval with the original query** remains the matched resource control. The G03 runs already go to depth
  1,000.
- **Not possible without approval:** the description, CPC and international families. Each needs a per-item owner
  download approval.

**Indexing cost (rough estimate only, linear in windows, not measured):**
- The 1M-passage encodes took 4,212 s (Arctic), 13,539 s (Qwen3) and 5,759 s (PatEmbed) on the V100 (`z*.log`).
- At about 3.3–4.0 windows per unit, a claims-complete index would need roughly **4.5 h Arctic, 12–13 h Qwen3 and 5–6 h
  PatEmbed** of V100 time, and about 3.5–4M vectors per model.
- The BM25 index build took 30 min at about 355 tokens per unit; full text is about 4–5 times that.
- An Arctic- or BM25-only pilot is the cheapest first step.

**P2-T03 candidate relations for a bounded relation search** (on disk, each with its caveat):
1. **Claim dependency tree.** Both the query side (about 79% of queries have more than one independent claim; dependent
   claims add limiting elements) and the corpus side are covered by explicit, resolvable `dependent` fields. This is the
   most natural source of "unresolved requirement → next search" with source spans, and it carries no label leakage.
2. **US continuity components.** About 10% of units. Use them for sibling deduplication or expansion. Siblings are often
   near-duplicates, so they mainly affect slot use, not discovery.
3. **IPC subclass / main group** of acquired candidates. Coverage is 98%, but there are few codes per unit (mean 1.5
   subclasses). IPC is also the IN/OUT definition (`dom_ipc3`), so any IPC-steered search must report IN and OUT jointly
   (the AM-7 N4 lesson).
4. **OA-2017 citation edges of acquired candidates** (17.6% of units). Three caveats apply:
   - exclude edges whose citing unit is an evaluation task;
   - OA citations were made during examination in 2008–2017 and may postdate a query's filing date, so a temporal mask
     by OA mail date is needed;
   - co-citation already gave only about +0.01 in AM-7 N5.
5. **Dates.** Masks only.

## 6. TEST isolation and limitations

**TEST isolation:**
- `texts-v1` and `ser-*` contain no TEST rows. Every audit script asserts that no `*-TEST` block appears and counts only
  P1-DEV and VAL queries.
- `tasks.tsv` was read for `app_id` and `split` only. Every OA-2017 citation row whose `app_id` is in a TEST split was
  dropped before any other field was read (3,718,870 rows dropped).
  - A separate check confirmed that all 108,894 apps of the frozen manifest's P1-TEST, P2-TEST and P3-TEST blocks lie
    inside that excluded set (0 missing).
  - 1,622 corpus units are TEST-task applications. Only their count is reported.
- Nothing per task or per query was written.

**Limitations:**
- Token figures for all-claims content come from a salted-hash **sample** (20,000 corpus units; 2,000 P1-DEV; all
  1,919 VAL). The truncation shares in §2 and the claim and structure counts in §3–4 cover the full populations.
- "Claim tokens inside the current text" assumes the serialiser's rule (claim tail cut first) and counts the first
  independent claim's surviving tokens against all live claims.
- Joining claims with `\n` adds a token or two per claim. Claim-number ordering puts the first independent claim first
  in most documents.
- Regex dependency detection is the serialiser's own rule; 138,969 corpus claims are dependent by regex only.
- Exact-duplicate counts are hash-based on lower-cased text and do not detect near-duplicates.
- The claims files cover grants from 1976 to 2013 and pre-grant publications from 2001 to 2016. This matches the corpus
  window (first publication 1976–2012) and the query publications (3 corpus docs have no claim rows).
- Panorama CPC coverage, and DAPFAM's representation (G04), were not audited.
- The cost figures in §5 are linear extrapolations, not measurements.

## 7. Methods and exact commands

**Scripts** (written for this task, read-only, aggregates only), in dr-train `/data/ptp-paper2/g03-dev/code/`:

| Script | SHA-256 |
|---|---|
| `p2t01_text_audit.py` | `4adc7085…91fc` |
| `p2t01_claims_audit.py` | `6c049718…08de` |
| `p2t01_struct_audit.py` | `d1f5c074…dab9` |

**Outputs**, in `/data/ptp-paper2/g03-dev/p2t01/`:

| Output | SHA-256 |
|---|---|
| `text-audit.json` | `7230953c…1b29` |
| `claims-audit.json` | `c853f7db…cc35` |
| `struct-audit.json` | `88e7c0fd…685c` |

Each output has `.log` and `.time` companions.

```bash
# dr-train, as chaw; from Git Bash prefix ssh/scp with MSYS_NO_PATHCONV=1
cd /data/ptp-paper2/g03-dev/p2t01
# 1. raw fields + truncation of ser-{arctic,qwen3,patembed}-v1 (stdlib; 54 s wall, 0.6 GB RSS)
CUDA_VISIBLE_DEVICES= /usr/bin/time -v nice -n 15 python3 -I ../code/p2t01_text_audit.py /data/ptp-paper2/bridgeret text-audit.json
# 2. all-claims scan (54 PatentsView claim zips, 12 CPU workers) + CPU tokenisation of the sample (16 min wall, 14.4 GB RSS)
export CUDA_VISIBLE_DEVICES= TOKENIZERS_PARALLELISM=false PYTHONPATH=/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages
/usr/bin/time -v nice -n 15 python3 ../code/p2t01_claims_audit.py /data/ptp-paper2/bridgeret /data/ptp-paper2/patentsview/claims claims-audit.json 12
# 3. IPC / dates / US continuity / OA-2017 citations (stdlib; 10 min wall, 5.3 GB RSS)
CUDA_VISIBLE_DEVICES= /usr/bin/time -v -o struct-audit.time nice -n 15 python3 -I ../code/p2t01_struct_audit.py \
  /data/ptp-paper2/challenge1m/out-v1/corpus-units.tsv /data/ptp-paper2/splits/private/tasks.tsv \
  /data/ptp-paper2/patentsview /data/ptp-paper2/oa2017 struct-audit.json
```

**Existing configuration inspected (read only):**
- Code: `bridgeret/code/{build_bridgeret_texts.py, bridgeret_query.py, serialise_bridgeret_texts*.py, dense_bridgeret_v2/v3.py, bm25_bridgeret.py, queue_*.sh}`.
- Run commands and logs: `bridgeret/{ser,serq,serp,bm25,zarctic,zqwen3,zpe}.time` and `z*.log`.
- Reports: `bridgeret/texts-v1/report.json`, `bridgeret/truncation-arctic-*.json`, `challenge1m/out-v1/report.json`,
  `challenge1m/build_challenge1m_sealed.py`, `manifest-v1/continuity/continuity-stats.json`.
- Model `config.json` and `tokenizer_config.json` for the three encoders.

The run was CPU only. The background V100 was not used.
