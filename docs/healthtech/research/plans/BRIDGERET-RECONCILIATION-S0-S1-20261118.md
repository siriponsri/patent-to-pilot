# BridgeRet / CEDS / EG-SHE: reconciliation, S0 readiness and S1 manifest code (2026-11-18)

Status: Phase A (reconciliation) done; Phase B (S0) partly done, read-only; Phase C (S1) code + synthetic tests done.
Nothing was run on real data. No TEST label, qrel or `pairs.tsv` row was read. No download, no GPU, no API, USD 0.

Inputs: owner set `docs/owner/owner-note-18112026/` (owner-local, untracked, not committed), owner decisions
`owner-decisions-20261117-bridgeret.json`, `DIRECTION-20261117-BRIDGERET-HANDOFF.md`, `paper2-precheck/oa/OA-SPLITS.md`.

## 1. Verified checkpoint

- Branch `main`, HEAD `a94eb68` = `origin/main` (0/0). `3732056` is an ancestor (two commits earlier: `a9d56d7`, `a94eb68`).
  So blocker #3 of SOT-0.2 §8 (commit reconciliation, C-12/O11) is resolved: the 18-Nov set was written against
  `3732056`; `a94eb68` only adds the 17-Nov direction docs and the owner-decision record. No code changed between them.
- Untracked: `.claude/`, `docs/owner/`, `uv.lock`, the owner's 9-Nov handoff. All left untouched, as intended.
- dr-train (read-only check): no PTP container or job, V100 and 2080 Ti idle, `/data` 1.1 TB free.
  Present: OA 2017 (`citations`, `office_actions`, `rejections`), PatentsView `g_application`, `g_patent`,
  `g_ipc_at_issue`, `pg_ipc_at_issue`, `pg_published_application` (1.1 GB total), and the R1 private tables
  `splits/private/tasks.tsv` (378,109 rows; columns `app_id split filing_date mail_dt art_unit ipc4_primary n_K n_K_out3 n_foreign_102_103`)
  and `pairs.tsv` (labels; not opened).

## 2. Owner-set inventory (18 Nov)

Present (14): 00, 01, 02, 03, 06, 07, 08, the three manuscript drafts, `master_plan_and_go_assessment.md`,
`product_roadmap.md`, `revision_decision_memo_v2.md`, the SciSpace master prompt.

`MISSING_INPUT` (referenced as existing, not on disk):
- `04_EVIDENCE_LEDGER.md`, `05_PRE_FREEZE_AMENDMENTS_AND_OWNER_DECISIONS.md` (D1-D7 / O1-O13 live there);
- the revised `budget_plan.md` and nine `paper_{1,2,3}_{introduction,literature_review,methodology}.md`.
  Only the 17-Nov versions exist (`owner-note-17112026/`). File 08 lists them as "complete" in a sandbox path.

## 3. Conflict register

| ID | Conflict | Evidence | Resolution here |
|---|---|---|---|
| R-01 | File 01 says O1 (TRAIN 2006-2009) and O2 (n₁) are "pending"; manuscript MS1 says `OPEN_DECISION: n₁ ∈ {8,000; 10,000}`; SOT §8 lists n₁ as open | owner-decisions JSON: O1 = 2006-2009, O2 = 10,000 (recorded 17 Nov) | Code uses the recorded decisions: TRAIN 2006-2009, n₁ = 10,000. Not re-asked. |
| R-02 | **Decision-ID collision.** 17-Nov O3 = base model, O4 = denoise; 18-Nov O3 = "P2 action type", O4 = "P2 E0 encoder" | JSON vs 00 §8 / 08 §4 | Treat as different namespaces. Proposed: rename 18-Nov ones `P2-O3`, `P2-O4`. Needs owner OK only for the renaming. |
| R-03 | Files 01, 02, 08, MS1-3, master plan still cite `SOT-0.1`; 00 is `SOT-0.2` | headers | Cosmetic; owner-local files not edited. |
| R-04 | **VAL = 2010, but R1 found 2010 incomplete** (c = 0.668 vs ~0.80) and excluded it; 2006-2009 were also excluded by R2a | OA-SPLITS.md | Owner overrode R2a for TRAIN (O1). VAL 2010 is then a filing-year cohort with ~33% fewer first actions observed than neighbours: allowed for checkpoint selection, but disclose as a known selection dip; do not use 2010 for σ/design-effect. **No decision required unless owner wants VAL from 2011 instead.** |
| R-05 | **Challenge-1M must contain P1-TEST positives**, yet TEST labels must not be read before evaluation | MS1 §corpus; master prompt §P1; 01 §1.4 | Proposed isolation: a restricted builder process calls `sealed_corpus_union()`; it returns only the unlabelled doc union (salted-hash order), counts and a digest of the positive set. Developers/selectors never see which docs are positives. Requires owner approval of this design before a real corpus build (TEST gold is read by the builder process). |
| R-06 | Family grouping is impossible with downloaded files (no continuity table) | OA-SPLITS.md "Family / continuation chains" | Builder stamps `FAMILY_DISJOINTNESS_PENDING` and L-B = `NOT_ASSESSABLE`. Fix needs a continuity table download (see §5). |
| R-07 | Eligibility (|K| ≥ 3, ≥ 1 OUT3) is label-derived for every split, including TEST | oa_temporal_splits.py | Pre-declared task definition, already run once on 16 Nov; counts already public. Not a new exposure. Manifest builder reads only metadata columns from `tasks.tsv`. |
| R-08 | 08 says "PASS" for documents not on disk (04, 05, revised paper_*) | §2 above | Readiness of these items is `UNVERIFIED`. |
| R-09 | Arm names | 02 vs code | Code (`patex_arms.py`) has no `E0-FT`/`E3-FT`; arms are classes (FixedRetrieval, DeepRetrieval, MultiQuery, ReAct) with an injected ranking, so E0-P1 = E0 with the P1 retriever, and a reranker would be a separate component (none exists). No code change needed now. |

## 4. S0 licence BOM (read-only; Hugging Face API 2026-11-18)

| Item | Licence | Revision seen | Product stack? |
|---|---|---|---|
| Snowflake/snowflake-arctic-embed-m-v2.0 | Apache-2.0 | `95c27414…` | yes |
| Qwen/Qwen3-Embedding-0.6B (fallback / Z-Qwen3) | Apache-2.0 | `97b0c614…` | yes |
| mpi-inno-comp/paecter | Apache-2.0 | `8fee86cd…` | possible |
| datalyes/patembed-* (Z-PatEmbed-large) | CC BY-NC-SA 4.0 | — | **research lane only** |
| USPTO OA Research Dataset 2017, PatentsView | US government data | — | yes; exact terms text still to be quoted (O8) |
| Derived P1 retriever | inherits Apache-2.0 base; training data public-domain USPTO | — | pending O8 write-up |

Not verified: dataset terms text; Qwen3-8B / P3 solver licences.

## 5. S0 data readiness

Have (dr-train): OA tasks, splits, IPC, titles/dates, pre-grant metadata. Abstract: `g_patent` and `pg_published_application`
carry abstracts (to confirm column names before use).

Missing for BridgeRet query/corpus text and for family grouping:
1. claims: `g_claims_{year}` and `pg_claims_{year}` (first independent claim). Covered by the 17-Nov R5 approval (≤ 60 GB).
2. continuity / related documents (grant and pre-grant related-application tables). **Not clearly covered** by R5
   ("text/claims files"); listed separately as an open item on 17 Nov. Needed for D1 family-aware split.
3. Exact file names and sizes: `NOT_VERIFIED`. The PatentsView page now redirects to data.uspto.gov (JS-rendered),
   and the old S3 URLs return 403. The listing step must be done in a browser on data.uspto.gov before any download.

## 6. S1 implementation (this commit)

- `src/patent_to_pilot/research/canonical_split_manifest.py` (stdlib only, runs on dr-train):
  salted hashing; owner 2012 rule verbatim; group-hash 2011 buckets; VAL hash sample; family grouping
  (family_id > continuity closure > singleton + PENDING stamp); option-A family conflict removal from P2-TEST;
  assertions A1-A4, A3, L-B, cross-year stratum; imbalance flag (no rebalancing); metadata-only reader;
  MinHash near-duplicate strata (L-C); unseen-document tags (L-D); self-target check (L-E);
  `ProtectedGoldGate` (approval bound to frozen manifest SHA256, one look per block, append-only open log);
  `sealed_corpus_union` (R-05); canonical-JSON manifest hash; freeze refuses synthetic or tampered manifests;
  hashed-id public view (L-H).
- `scripts/healthtech/build_canonical_split_manifest.py`: `--synthetic` smoke, or real data only with an owner
  build-approval record; never overwrites; never freezes.
- `tests/test_canonical_split_manifest.py`: 17 tests, synthetic fixtures only.

Not done: real manifest build (needs owner approval to run the builder on `tasks.tsv` metadata), tokenizer/query
serialisation and claim parser (need claims text), truncation analysis, throughput pilot.

## 7. Approvals still needed (only these)

1. **Run the manifest builder on real metadata** (`tasks.tsv` metadata columns only, CPU on dr-train, USD 0).
   Without continuity data the result is stamped `FAMILY_DISJOINTNESS_PENDING`.
2. **Continuity tables download** (grant + pre-grant related documents), within the 60 GB cap — if R5 is not read as covering it.
3. **Challenge-1M isolation design** (R-05) before any real corpus build.
4. Optional: rename 18-Nov O3/O4 to `P2-O3`/`P2-O4` (R-02).
5. Unchanged: RunPod pilot (≤ USD 10) dispatch needs its own go.

## 8. Update 2026-11-18 (later): manifest-v1 built; three owner approvals

**manifest-v1** (owner approved the build; receipt `paper1-bridgeret/manifest-v1/build-receipt.json`):
one CPU run on dr-train, exit 0, 3.3 s wall, 246 MB RSS, metadata columns only, `pairs.tsv` and labels not read, USD 0.
manifest_sha256 `5f803b13b976016498278c4868ff9ddad4dc0f0368fd7c729c1577f646a3d83f`, NOT frozen.

| Block | Tasks |
|---|---|
| TRAIN (2006-2009) | 100,376 (matches the project record) |
| VAL (2010, hash sample) | 2,000 |
| P1-DEV / P2-DEV (2011) | 26,320 / 26,486 (imbalance 0.31 %, within ±5 %) |
| P1-TEST (2012 tail) | 10,000 |
| P2-TEST (2012 prefix, cap) | 44,074 |
| P3-TEST (2013) | 55,307 |

Assertions: A1-A4 (app_id disjoint) PASS, A3 PASS; L-B NOT_ASSESSABLE (`FAMILY_DISJOINTNESS_PENDING`).
Eligible tasks with filing years outside every block (1995-2005 stragglers, 2014-2016 censored) are not used.
Private manifest (raw ids) and public view (salted-hash ids; salt only on dr-train) stay on dr-train under
`/data/ptp-paper2/manifest-v1/` (mode 700).

**Owner approvals** (`paper1-bridgeret/owner-decisions-20261118.json`):
1. Continuity tables download: approved. Exact list in `paper1-bridgeret/CONTINUITY-DOWNLOAD-REQUEST-20261118.md`.
   ODP requires the owner's USPTO.gov sign-in (MFA + CAPTCHA), so the owner downloads; the agent then builds manifest-v2.
2. R-05 Challenge-1M sealed-builder isolation: approved (design binding; implementation = `sealed_corpus_union`).
3. 18-Nov O3/O4 renamed `P2-O3` (P2 action type) and `P2-O4` (P2 E0 encoder); O1-O10 keep their 17-Nov meanings.

## 9. Overnight 18->19 Nov (owner asleep; approvals in `paper1-bridgeret/owner-decisions-20261118.json` "later")
- Frozen: manifest-v2 (`c8443600…`), P1-BridgeRet pre-declaration (commit b9b2bd0). Clarifications CL-1/CL-2 logged before the affected runs.
- Built: Challenge-1M v1 (sealed builder, 1M units), text tables, Arctic/Qwen3/PatEmbed serialisations, hard-negative pools.
- DEV descriptive numbers, audits, power planning and the RunPod pilot: see `paper1-bridgeret/MORNING-REPORT-20261119.md`.
- Conflicts found overnight:
  - R-10: the dr-train V100 is shared with an idle CIE TTS service holding 24-26.5 GB; our jobs run memory-capped beside it (one Qwen3 OOM at cap 0.12, retried at batch 8 / cap 0.15).
  - R-11: tasks without a pre-grant publication (P1-DEV 949/26,575) have no query; they score 0 under the frozen rule.
  - R-12: the "other citations from the same application's later actions" guard is not available in pairs-dev; mining applies K(q), own unit and exact-text guards only.
  - R-13: full fine-tuning with 7 x 512-token negatives is ~11.5 A40-h per epoch; amendment A1 proposed (not applied).
  - R-14: RunPod MCP has no file transfer; FT on RunPod needs a pod with our own PUBLIC_KEY env + scp from dr-train (no account change), or the V100 when the TTS frees memory.
