# Patent-to-Pilot HealthTech Handoff

Status: `ACTIVE_WPI_RESEARCH_PACKAGE_TRACK_A_COMPLETE_TRACK_B_DESCRIPTIVE`

## Agent takeover state — 10 Nov 2026 (read this first)

### Latest checkpoint — 10 Nov 2026 (Bangkok)

- **Latest DAPFAM package:** native TA/TAC loader/metric safeguards implemented; [audit](docs/healthtech/audits/ptp-method-first-r1-dapfam-20261110/README.md). Base/last pushed before this package: 6202c58966e85b3c75d306c14228bb09d0161c74. 61 targeted tests and Ruff pass; 12 differential cases against hash-pinned MTEB source and pytrec-eval-terrier 0.5.11 pass. Full corpus retained across ALL/IN/OUT; missing eligible rankings score zero with fixed denominator. Raw backend missing-query omission confirmed on synthetic data. No actual benchmark rows, protected labels, GPU jobs or paid calls. Changed: native dev module/verifier/tests, audit and handoff/progress pointers. Next integrate prospective safe runtime/vector checks; trusted staging still needed for actual dev A03 and ranking parity. Existing untracked research handoff preserved.


- **Owner/goal:** Codex is the single active writer in chat 01a1c2b7-8897-7ea1-b7bb-ad7e8a449775; method-first long-run goal ACTIVE. Follow HANDOFF_PROMPT.md and the local research handoff, with DAPFAM anchor / MTM evaluation / untested SACR. Update both HANDOFF.md and CLAUDE.md at every checkpoint. Prior 10 November checkpoints are preserved in Git and linked audits.
- **Last pushed commit before this receipt:** 1df23a5f81cef4b7cc6eb6045e66c0106ac52627 (actual inspection code). Verify the containing receipt commit remotely before takeover.
- **Completed:** R0 inventory; prospective A01 input/staging contracts; A03 exact-mask dev auditor; A14 identity checks and real CPU observation. Audits: ptp-method-first-r0-20261110, ptp-method-first-r1-boundary-20261110, ptp-method-first-r1-eligibility-20261110, and [A14 result](docs/healthtech/audits/ptp-method-first-r1-vectors-20261110/README.md).
- **Evidence:** 56 targeted tests passed; final 12 vector tests passed after optional identity-file addition; Ruff passed. CPU inspection v2 exit 0, 00:14:21Z–00:16:20Z. Fresh corpus/vector/model weight hashes match historical dev receipts: 899,838 families, 1,553,678 × 1,024 float32 vectors. Ordered family/passage-owner hashes now recorded. Original tokenizer/order attestation absent in historical receipts; actual ranking parity NOT_RUN.
- **Attempts/jobs:** first launcher (bfc12bb, PID 2418646) failed before Python because its exported archive contained CRLF; committed blob had LF. Failure directory preserved. Scoped LF attribute plus archive/Bash checks fixed v2. V2 launcher PID 2427095 / Python 2427097 terminated successfully. No job remains from this package. Remote v2 root: mtm-20261107/r1-vector-identity-20261110-v2; logs/status.log, logs/inspection.log and vector-identity.json preserve evidence.
- **Current changes:** A14 result/verification and both handoff/progress/next-actions pointers. Preserve the existing untracked docs/healthtech/research/PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md; it is not part of this commit.
- **Open boundaries:** A01 real staging/physical isolation, A03 actual dev counts, prospective runner enforcement, native DAPFAM parity and real dense-ranking parity are incomplete. Do not execute mixed-label staging from the development agent. No test labels/scores/rankings were read in these packages. No paid calls, BigQuery pulls, GPU experiments or re-encoding. GPU authorization remains through 31 Dec 2026 16:59 UTC; recheck live resources before use.
- **Next 4 steps:** (1) inspect pinned DAPFAM generic evaluator and implement native parity/denominator fixtures; (2) integrate safe runtime loaders and vector identity enforcement into a prospective parity runner; (3) present the complete curator staging/isolation procedure and obtain the necessary operational handoff; (4) run safe dev A03/ranking-parity checks, then begin authorized R2 specification/fidelity work. Continue independent safe work at protected-data boundaries.
- **Approval gates:** protected scoring only after owner-approved final freeze (at most four systems conservatively), no paid APIs/training/full-corpus re-encoding/new pulls without their required approval, no protocol amendment or release by implication. Optional 3d/cited-distractor work remains out of scope.

The material below preserves earlier research context. This checkpoint supersedes older handoff-process instructions; older job and permission statements require current verification.

**Latest (8 Nov ~13:30 Bangkok; last pushed commit before this note: `9f2a847`):**
- **9 Nov owner handoff:**
  - The owner will continue on another Claude account using the external research handoff `PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md` (not in the repo yet).
  - **That handoff sets a method-first direction:**
    - SACR (selective abstraction with preserved requirements) is the candidate method;
    - DAPFAM is the external anchor;
    - work packages R0–R6 come first, starting with integrity repairs: A01 label separation, A03 gold eligibility, A14 vector manifest.
  - The copy-ready prompt is in `HANDOFF_PROMPT.md`. Phase-3 items 3d and the cited-distractor view are now optional later work.
- **STATE AFTER PHASE 3A/3B (9 Nov, about 07:40 Bangkok):**
  - Eligible for test so far: **V4 only** (Qwen3-8B rerank of the X top 30 + dense, λ 0.5).
  - Done and not eligible: 3a PRF (negative) and 3c (not built; the 3b gate said NO_GO).
  - **Next steps, each needing a methods-log entry first:**
    1. The **cited-distractor corpus view** (robustness): a BigQuery text pull, best done after the December free-tier reset, then an encode of about 1–2 h.
    2. **3d time-safe citation fine-tune.** The owner still has to choose the encoder: A = PatEmbed (CC BY-NC-SA), B = Qwen3-Embedding (Apache-2.0), or C = both. It needs a BigQuery text pull for the 2001–2009 training pairs (December).
    3. **DAPFAM secondary benchmark:**
       - check the DAPFAM protocol code;
       - calibrate the published baselines on all 1,247 queries;
       - run X and V4 on the project's DAPFAM dev split.

       This needs no BigQuery and could run in November.
    4. A **PatEmbed look-ahead check** (does PatenTEB publish its training pairs?).
    5. Freeze at most 4 methods for the single test read, with owner approval.
- **9 Nov: the owner approved phase 3.** The order is in the [phase-3 audit](docs/healthtech/audits/ptp-medtech-tm-phase3-audit-20261109/README.md). 3a and 3b are declared in the methods log (`3792f6d`).
  - **3a PRF done: negative** ([audit](docs/healthtech/audits/ptp-medtech-tm-dev-phase3a-20261109/README.md)).
    - P/main CV out of fold: −0.003 [−0.008, +0.003]. Every variant lowers hit@20 and hit@200. Not eligible.
    - No GPU job is running.
  - **3b probe done: NO_GO** ([audit](docs/healthtech/audits/ptp-medtech-tm-dev-phase3b-20261109/README.md)).
    - The owner raised the cap to 34 GiB. tm06 billed 33.8 GB, producing 1,344,435 edges.
    - Reach is 30.3%, below the 48.8% gate, so **3c is not built**.
    - Co-citation inter-connection is 3.1%. The popularity null reaches 3.7% at hit@200, so the corpus enrichment is not trivially exploitable.
    - 87% of the cited families are outside the corpus.
  - **The owner's IEEE paper** is to be presented on 19–21 Nov 2026; no DOI yet. The data licence (Google Patents Public Data, CC BY 4.0) is confirmed and recorded in the methods log.
- **9 Nov owner decisions:**
  - **GPU window extended to 31 Dec 2026 16:59 UTC** (`local_execution.py`, its test and AUTHORIZATION_AND_BUDGET.md). Runs need a fresh `git archive` that includes this change.
  - Phase 3 is **not approved yet**. The owner asked for a full audit of the plan and current results, plus a literature search. **The audit is done:** [phase-3 audit](docs/healthtech/audits/ptp-medtech-tm-phase3-audit-20261109/README.md).
    - **Key finding:** the corpus is enriched with cited documents (8,518 targets plus distractors matched only on year and CPC section). Citation-derived methods (3c, and partly 3d) need a popularity-null baseline, an open-candidate protocol and a new "cited distractors" view.
    - 3b becomes a gating probe with a fixed go/no-go rule.
    - The V4 gain survives a cluster bootstrap: [+0.010, +0.024].
    - The plan waits for owner approval.
  - Phase-3 draft: 3a vector PRF, 3b BigQuery citation-reuse probe, 3c citation chasing, 3d time-safe citation fine-tune, 3e combined system; DAPFAM as a secondary benchmark.
  - The 3d encoder choice (PatEmbed, NC licence, vs Apache Qwen3-Emb) is open.
- **The MTM baseline job is done.** Test rankings for P/T/A are recorded and **not scored**: [test-rankings audit](docs/healthtech/audits/ptp-medtech-tm-test-rankings-20261108/README.md).
- **Phase 1 ran (V1 BM25, V2 hybrid, V3 bge-reranker; every step exit=0) but is DEFECTIVE.**
  - **The defect:** the PatEmbed query prefix `encode query for different document retrieval: ` leaked into the BM25 tokens (`run_mtm_hybrid.py:168`) and into the reranker input (`run_mtm_rerank_ce.py:66`). The dense side is unaffected.
  - The results stay on record in the [phase-1 audit](docs/healthtech/audits/ptp-medtech-tm-dev-phase1-20261108/README.md), marked defective, and are not eligible for carry-forward.
  - The owner chose not to carry phase 1 to test, before the defect was found.
- **The owner approved phase 1b and phase 2 (8 Nov).** Both are declared in the [methods log](docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md).
  - Phase 2: V4 Qwen3-8B yes/no reranker on the X top 30 (R-neutral and R-cross prompts), V5 reranker + dense fusion, V6 function-channel fusion.
  - The prefix fix is pushed at `14263c9`: `strip_prefix`, a guard, and a test (12 tests pass).
- **Phase 1b is done** (06:50Z, exit=0): [audit](docs/healthtech/audits/ptp-medtech-tm-dev-phase1b-20261108/README.md). On P/main the result is null/negative: hybrid CV +0.002 [−0.008, +0.011], BM25 −0.136, reranker −0.027. On T the hybrid gives +0.014 [+0.008, +0.021] (secondary). Nothing is eligible for test.
- **The V4 smoke test passed** (300 pairs, `$J/smoke-p2`): N 13.9 pairs/s, C 13.0 pairs/s.
  - Projected time is 1.2 h + 1.3 h = 2.5 h, under the 8 h limit, so **PROMPTS=N,C**.
  - The scores are not degenerate.
- **Phase 2 is done** (11:53Z, every step exit=0): [phase-2 audit](docs/healthtech/audits/ptp-medtech-tm-dev-phase2-20261108/README.md).
  - **V4 (Qwen3-8B yes/no on the X top 30, fused with dense, R-neutral, λ 0.5) beats X on P/main.** Out of fold: +0.017 [+0.010, +0.025], hit@20 0.180 → 0.197. It is the only eligible method.
  - V5 bge + dense: +0.007 [−0.001, +0.015], not eligible.
  - V6 function channel: −0.003, not eligible.
  - The R-cross prompt was weaker than R-neutral.
  - No GPU job is running.
- **Waiting on the owner:**
  1. Freeze V4 (R-neutral, top 30, λ 0.5) for the single test read, or run more dev methods first. Once test is read, no new methods can be added.
  2. If frozen:
     - allow test mode in `run_mtm_rerank_llm.py` and `run_mtm_fusion.py` (a reviewed change);
     - score the test X top 30 with prompt N only (about 1.3 h);
     - fuse at λ 0.5;
     - run one test analysis per rules §14 (X vs V4, Holm with 1 method).
- Test stays sealed.

Last pushed commit before this note: `b928456` (handoff before the E3 launch; protocol freeze `4c5a882`). **P2 (E3/E4) is done** (7 Nov 2026). The commit that adds this note also adds the [P2 audit](docs/healthtech/audits/ptp-scout-frozen-eval-20261107/README.md). All work is on `main` in this checkout; there are no worktrees or branches. The handoff rule in `CLAUDE.md` applies: update this section and push after every step.

### Direction

- A product-led WPI paper for **Solution Scout** (Cross-Industry Solution Scout).
  - A short problem brief goes in. Out comes a two-lane shortlist (own field / other industries), a descriptive field constellation, and quote-checked LLM transfer rationales.
- Spec: [SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md](docs/healthtech/research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md). §2 holds the evidence, §6 the evaluation E1–E5, §7 the milestones and progress, §9 the owner approvals.
- **Pre-declared dev results** (the DAPFAM test split has never been read):

  | Check | Result | Audit |
  |---|---|---|
  | Stage 1 | Gate PASS, learnable headroom FAIL | [audit](docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/README.md) |
  | Scout feasibility | `PARTIAL_LANE_ONLY`: LLM rewriting hurts; the lane gain is definitional | [audit](docs/healthtech/audits/ptp-solution-scout-feasibility-20261105/README.md) |
  | Atlas headroom | `GO_ORACLE_ONLY`: the learned class prior hurts | [audit](docs/healthtech/audits/ptp-solution-atlas-headroom-20261106/README.md) |
  | **E3 grounding (frozen, dev + HUPD)** | **`ADOPT_V1`**: G1 +0.237 (CI +0.176 to +0.300); G2 NLI proxy +0.075 (CI −0.013 to +0.166, non-inferior). v1 parse failures 18/236 (more than 3 sentence numbers) vs v0 1/236 | [audit](docs/healthtech/audits/ptp-scout-frozen-eval-20261107/README.md) |
  | **E4 latency** | CPU encode median 533 ms (max 759), search median 124 ms (max 134); V100 rationale median 6.2 s (v1) vs 13.2 s (v0) | same audit |

- The hyperresearch deep-research run was **stopped by the owner** (6 Nov) to save tokens. The research direction is set with the owner directly. Do not resume it.

### Milestones

| M | Status | Where |
|---|---|---|
| M0 contracts, lane logic, quote check | done `7162078` | `src/patent_to_pilot/healthtech/scout.py` |
| M1 replay backend | done `69efd30` | `scout_service.py`, `/scout-sessions…` routes in `http.py` |
| M3 public corpus and live search | done | HUPD 2017 subset of 56,528 applications (CC BY-SA 4.0), V100 PatEmbed vectors, `scout_live.py` (CPU), exact CPU/GPU parity. [Audit](docs/healthtech/audits/ptp-scout-public-demo-20261106/README.md) |
| M2 screens S1–S6 | **done 6 Nov** | `frontend/healthtech-web/app/scout.html`, `scout.css`, `src/scout/*`. S5 is a dossier export (Markdown/JSON keeping source facts, system inference and unresolved items apart); a push into the device-dossier workspace is not built |
| M4 live LLM rationales | open | Recorded rationales only: 56 for the 8 demo briefs; 120 of 158 quotes literal-matched |
| M5 frozen evaluation E1–E5 | **protocol frozen 7 Nov; P2 (E3, E4) done 7 Nov**; P3–P4 pending | The owner approved one DAPFAM test read after a freeze commit, plus the E5 PatenTEB replication |
| M6 paper and demo video | open | — |

Latest suites (7 Nov, code at freeze `4c5a882`): Python 746 passed / 1 skipped; `npm test` 81 passed / 1 skipped; e2e 17/17 (6 Nov).

### Owner decisions in force

- **Deadline 14 Nov 2026, 09:00 (Bangkok): a "Next" part added to the IS short-paper (Paper 53) deck.**
  - The deck is at `C:/Users/User/Desktop/myDegree/IS/IS_1/presentation-is-shortpaper/` (not a Git repo).
  - Status: **draft done 7 Nov**, waiting for the owner's review.
  - Backup before editing: `IS_1/presentation-is-shortpaper_backup_20261107.zip`. The stale `qa/` renders were deleted.
  - Owner decisions:
    - compress the Paper 53 story;
    - add 1–2 new sheets, told with pictures, screenshots and HyperFrames motion;
    - show no benchmark scores, only the concept and its link to Paper 53;
    - include one Solution Scout screenshot.
  - Result: 17 sheets, planned 8:55.
    - rw, s04, s16 and s18 moved to appendix A10–A13.
    - New sheet 16 `n1` is a time machine: HyperFrames clip `assets/video/time-machine.mp4` (20 s) on a real dev-split MTM pair, US9119617B2 (2012, A61) citing US3812859A (1972, A01, examiner `*`).
    - New sheet 17 `n2` holds the benchmark dot funnel (`benchmark-funnel.mp4`, 10 s), a Scout screenshot, and the roadmap.
    - Sources are in `motion-src/`. The script (`assets/js/script-th.js` → `script/script_th.{html,pdf}`) is rebuilt.
  - Owner feedback 7 Nov: "too much text, tell it with pictures". Then "cut them too". All main sheets are now English title + Thai only: the English duplicate lines were removed, while the appendix and the figure captions keep their English. Both clips were re-rendered without English lines.
  - **Scout 409 fixed (7 Nov).** Cause: the stored wearable-patch session in `C:/Users/User/.ptp-scout-data` was made with UI language `th`; the old client key hashed only text + own_ipc3 + split, so the same key came back with `language: "en"` and the server's full-brief hash differed. Now `requestKey()` (`frontend/healthtech-web/app/src/scout/model.js`) hashes the same canonical request as `scout_service.create` (full brief with defaults + split); the key is `scout-` + the first 24 hex digits of the server's `request_sha256`. A shared test vector pins both sides (`scout.test.mjs`, `tests/test_healthtech_scout_http.py`). The server is unchanged.
    - Checked live on a copy of the old data dir: old key + `en` still gives 409 (old entries); new keys never conflict. Old index entries use the old key format, so the first re-run of a brief creates one new session (local search, no paid call) and later runs return it (`duplicate: true`). The old dir itself was not touched.
    - Suites after the fix: `npm test` 82 passed / 1 skipped; Python 759 passed / 1 skipped.

- **HUPD** replaces PatentsView: PatentsView bulk data now needs a USPTO.gov login with MFA, and agents must not log in.
- **Local CPU encoder** for live search.
- PatEmbed-large is **CC BY-NC-SA 4.0**: research use only. Say so in the demo and the paper.
- Name: **Solution Scout**.

### Run the demo

1. Backend (startup about 100 s):
   `C:/Users/User/.ptp-scout-venv/Scripts/python scripts/healthtech/serve_http.py --port 8787 --data-dir C:/Users/User/.ptp-scout-data --scout-live-dir ../_private_artifacts/healthtech/scout-public-demo --scout-model-dir C:/Users/User/.ptp-models/patembed-large --scout-rationales ../_private_artifacts/healthtech/scout-public-demo/rationale-book-v0.json`
2. Frontend: `cd frontend/healthtech-web && npm start`.
3. Open `http://127.0.0.1:5178/scout.html`.

Keep the data dir short: long Windows paths broke rationale writes before the fix.

### Next steps: plan A approved 7 Nov 2026; P1 freeze and P2 done

The protocol [SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md](docs/healthtech/research/SOLUTION_SCOUT_FROZEN_PROTOCOL_20261106_EN.md) and its code are frozen at `4c5a882`. Run in this order. **Never re-run a frozen analysis**; the scripts refuse to overwrite their output. The first output is final.

**P2 (E3, E4): done 7 Nov.** See the [audit](docs/healthtech/audits/ptp-scout-frozen-eval-20261107/README.md). `e3-grounding.json` and `e4-latency.json` are final; do not re-run them.

**Open owner decision from P2:** E3 permits switching the product default to v1 (quote by reference). This has **not** been done.
- A switch needs a declared rule for answers with more than 3 sentence numbers. These caused all 18 v1 parse failures.
- Until then, the demo keeps the v0 book, with unmatched quotes flagged.

**Open owner decision on direction (7 Nov 2026).**
- The owner asked whether to pivot to an "examiner-verifiable claim chart" or an FTO product. The advisor wants the paper to connect visibly to Paper 53.
- See the [literature check](docs/healthtech/research/CLAIM_CHART_AND_SCOUT_LITERATURE_REVIEW_20261107_EN.md). Claim charts and FTO are already benchmarked in 2026 (FiNE-Patents, SIGIR '26; PatentAgentBench, PatSnap; PatRe). Cross-domain evidence on DAPFAM looks open.
- **Owner criteria (7 Nov):** target users are R&D teams and medtech; "wow" means field-shocking numbers plus a live demo.
- The follow-up [deep dive](docs/healthtech/research/DEEP_DIVE_DIRECTION_REVIEW_20261107_EN.md) found:
  - no public device–patent register (JAMA 2026 "Yellow Book" proposal);
  - one AI attempt (Bridge-MedDevKG, ACL 2026) with no analyst-depth metric, no precision and an A61-only corpus; its release is `BLOCKED_LOCAL` here on rights.
- **New agent recommendation:** an open, provenance-tracked device–patent linkage benchmark and demo ("FDA device number → patent wall"). It uses Track B VPM adapters, the Scout lanes, E3 grounding and Paper 53's exposure lens. Keep the Scout P3 protocol in reserve.
- **Owner decisions pending:**
  - the direction;
  - the patent text/CPC source (USPTO ODP key registered by the owner, or HUPD);
  - whether a legal check is needed before releasing identifier pairs.
- Addendum (7 Nov): two further options are in the deep dive §7.
  - **"Time machine"**: a retrospective cross-industry foresight back-test. Dev count: 35 A61 queries with OUT positives; 28% of their targets are at least 10 years older.
  - **Landscape agent**: no LLM-agent vs expert-landscape evaluation found; WIPO Assistive Technology 2021 is a possible gold.
- **Owner chose "time machine" (7 Nov).** The pre-declared dev probe (`013cbb9`) returned **`GO_SHOCK`**, the narrowest pass ([audit](docs/healthtech/audits/ptp-time-machine-dev-probe-20261107/README.md)).
  - Population: 25 A61 dev queries with cross-industry targets at least 5 years older.
  - hit@20: problem brief over all patents 0.08; cross-industry lane 0.28; Δ +0.20 (CI +0.04 to +0.36).
  - Hits were a median of 16 years older. The gain is partly by construction (the lane equals the OUT rule).
  - Next, needing the owner: a dated amendment adding this analysis to P3 **before** the test read, and a demo prototype from the 5 private dev cases.
- [Amendment 1 draft](docs/healthtech/research/SOLUTION_SCOUT_PROTOCOL_AMENDMENT_1_DRAFT_20261107_EN.md) (E6 time machine on test): **DRAFT, NOT IN FORCE**.
  - It comes into force only with owner approval plus the frozen `analyze_time_machine_test.py`, before the test read.
  - The owner is considering dev-only expansion of the data and the effect first.
- **Owner chose "more data" (7 Nov).** See the [data plan draft](docs/healthtech/research/MEDTECH_TIME_MACHINE_DATA_PLAN_DRAFT_20261107_EN.md).
  - Recommended source: USPTO Patent Grant Full Text XML (public domain; examiner-cited references expected), stream-processed on dr-train.
  - **Pending owner approval:** pilot download of one weekly file (about 100–300 MB). Possibly a MyUSPTO API key registered by the owner, and a V100 window extension past 15 Nov.
- **Owner (7 Nov):** both USPTO and Google BigQuery may be used. The owner has a Google Cloud account; no account details are recorded here.
  - Proposed hybrid: BigQuery for the benchmark skeleton and private experiment text; USPTO XML pilot files to cross-check the examiner flag and text; releases carry only IDs and labels.
  - The agent does not log in. The owner runs or authorizes queries; dry-run byte estimates come first.
  - No BigQuery cost beyond the free tier without owner approval.
- BigQuery tooling is ready: `scripts/healthtech/bq_probe.py` (dry-run first, per-query byte cap, refuses to overwrite, never prints credentials) and `scripts/healthtech/sql/tm01_us_citation_categories.sql`.
  - The owner puts credentials in a git-ignored `.env.bigquery` (template in `.env.example`). It cannot go in `.env`: the loader accepts only `OPENROUTER_API_KEY`.
  - Pending: the owner creates a service-account key or gcloud login, and approves `pip install google-cloud-bigquery` into the scout venv.
- **BigQuery live (7 Nov):** [audit](docs/healthtech/audits/ptp-medtech-tm-bigquery-20261107/README.md).
  - tm01 ran (8.06 GB billed): US citations carry category SEA (examiner-cited) vs APP (applicant).
  - tm02 ran after the owner raised the cap to 34 GiB (33.5 GB billed). Of 324,452 US device grants from 2010 to 2023, **59,020 (18.2%)** have an examiner-cited, cross-field US target filed at least 5 years earlier: 139,227 pairs, median gap 14–16 years.
  - [Benchmark rules draft (MTM)](docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md) is awaiting owner approval:
    - family-deduplicated US device grants; dev 2010–2016 and test 2019–2023, 2,000 queries each;
    - examiner-cited cross-field targets at least 5 years older by priority date;
    - a corpus of about 500k matched-distractor families, time-filtered per query;
    - brief P from the frozen prompt; arms U, X and M; hit@20.
  - Owner approved the rules draft and the dry runs (7 Nov).
    - tm03 build query (`scripts/healthtech/sql/tm03_build_mtm.sql`): dry run **365 GiB with claims, 249 GiB without**. Not run; it needs a one-run cap raise by the owner.
    - dr-train has only Qwen3-8B locally (V100 32 GB; no vllm or bitsandbytes).
    - The owner offered a stronger local model or an API. Agent proposal: decide after the MTM dev baseline measures reranking headroom (hit@100 − hit@20, Paper 53 lens). Paid API needs the CLAUDE.md admission process.
  - **Owner approved all (7 Nov)**: the tm03 run with claims and the USPTO pilot.
    - **tm03 done (PASS)**, 392 GB billed: 4,000 queries (2,000 dev / 2,000 test), 8,518 target families, 442,886 matched distractors. Private CSV, 1.06 GB.
      - Validation found a **corpus flaw**: distractors copy the targets' old age profile, so almost no documents have priority after 2012.
      - **tm04 done (PASS)**, 375.6 GB billed: 470,000 uniform families. 21,566 overlap tm03, leaving 448,434 new. The age mix now includes recent years (about 207k with priority 2010–2023).
        - Monthly billed is about 829 GB. Do not re-run tm03 or tm04.
      - MTM pipeline code is written and unit-tested; it is not run and not frozen:
        - `build_mtm_inputs.py`, `run_mtm_dense_pool.py` (time filter, own family, X lane, 4 corpus views from one encoding), `analyze_mtm.py`;
        - tests: `tests/test_mtm_pipeline.py`;
        - proposed ⚙ resolutions are in §12 of the rules draft.
      - **Pre-freeze fix (7 Nov), from an external review the owner relayed:** the time filter must use the publication date of the indexed text, not the family priority date.
        - Code and tests are changed (`visible_from`); see rules §13.
        - Estimated impact: 1.6% of gold pairs; median 4% of eligible candidates per query.
        - tm05 (US publication dates, dry run 4.48 GiB) needs owner approval.
      - **tm05 done** (4.8 GB billed; 22.3M US publication dates). **Inputs built** in `../_private_artifacts/healthtech/medtech-time-machine/inputs/`:
        - corpus of 899,838 families; 1,985 dev / 1,955 test queries;
        - publication-date visibility rule: 173 gold pairs removed across 155 queries; 60 queries dropped entirely (dev 15, test 45).
      - **MTM rules FROZEN (owner approved 7 Nov)** at the commit `research: freeze MTM benchmark rules`. See rules §14: label-free test briefs and rankings may precede the dev method freeze; test scoring runs once, after methods are frozen.
      - **MTM V100 JOB RUNNING (started 7 Nov about 11:45Z).**
        - Job dir `J=/home/chaw/patent-to-pilot-jobs/mtm-20261107`: frozen code from `git archive 7d317e7` in `$J/code`; inputs in `$J/inputs` (hash-identical to local).
        - Script `$J/run_mtm_v100.sh` (copy in `docs/healthtech/audits/ptp-medtech-tm-bigquery-20261107/`) runs in sequence:
          1. dense T-dev, which encodes about 1.4M passages, roughly 6–7 h at about 55 passages/s in fp32, and saves `$J/out/passage-vectors-f32.npy`;
          2. dense A-dev;
          3. briefs P-dev, then queries P-dev, then dense P-dev;
          4. briefs P-test, then queries P-test, then dense P-test;
          5. dense T-test and A-test.
        - Check: `ssh -o BatchMode=yes chaw@100.77.149.83 'cat $J/logs/status.log; ls $J/out'`. Per-step logs in `$J/logs/<step>.log`.
        - No retries. If a step died: do not overwrite; report to the owner. The smoke test in `$J/smoke` passed.
        - Test outputs are label-free (rules §14). **Do not run `analyze_mtm.py --split test`** until the methods are frozen.
        - **Owner approved (7 Nov, ~16:10Z) the dev analysis as soon as dev rankings exist.** The agent runs it on dr-train with the frozen code, CPU only, and writes aggregates only:
          - when `end dense-A-dev` appears: `cd $J/code && $PY scripts/healthtech/analyze_mtm.py --split dev --query-views T,A --queries-meta $J/inputs/queries-meta.jsonl --corpus $J/inputs/corpus.jsonl --rankings-dir $J/out --output $J/analysis/dev-TA.json`;
          - when `end dense-P-dev` appears: the same with `--query-views P,T,A --output $J/analysis/dev-PTA.json`.
          - Copy each JSON to `docs/healthtech/audits/ptp-medtech-tm-dev-20261107/`, write a short README with the dev results, and report to the owner. Rules §11: dev may be re-run into new files; log every run.
          - **T/A dev analysis DONE (7 Nov 20:11Z, exit 0)**: [audit](docs/healthtech/audits/ptp-medtech-tm-dev-20261107/README.md). Dense T-dev ended 20:05Z and A-dev 20:09Z, both exit 0.
            - Corpus view main, title view T: hit@20 is U 0.074 / X 0.129 / M 0.110.
            - X − U is +0.055 (CI 0.045 to 0.065); M − U is +0.036.
            - hit@100 for X is 0.251, so there is reranking headroom.
            - Abstract view A (leakage reference only): U 0.146 / X 0.251.
          - **P,T,A dev analysis DONE (8 Nov ~22:45Z, exit 0)**, `dev-PTA.json` in the same audit.
            - Briefs P-dev: 0 of 1,985 failed.
            - Main view, P: hit@20 is U 0.084 / X 0.180 / M 0.145.
            - X − U is +0.096 (CI 0.084 to 0.109); M − U is +0.062.
            - hit@100 for X is 0.313, so there is reranker headroom of about 13 points.
          - **Running now:** briefs P-test (started 22:40Z, about 2.5 h), then queries and dense P-test, then dense T-test and A-test. All are label-free.
          - **Next (owner):**
            1. Choose the dev methods to try (at most 4, rules §8), for example a reranker on the X top 100.
            2. Freeze them.
            3. Score the test split once.

            Do not run `--split test` before that.
      - **GPU window extended by the owner (7 Nov) to 30 Nov 2026 16:59 UTC** (`local_execution.py`, test and AUTHORIZATION_AND_BUDGET.md updated). The running job uses the frozen copy `7d317e7`, whose check still ends at 15 Nov 16:59 UTC; that is not a problem, because the job ends long before then. Any run after 15 Nov needs a fresh `git archive` that includes the window change. That is not a benchmark-rule change.
      - The owner may lower the cap again if tm04 is declined.
    - **SEA validated against USPTO XML** (owner browser download `ipg180102.zip`): 206,070 citation pairs, SEA = "cited by examiner" with precision and recall 1.000.
  - Nothing is frozen or scored.
- **Do not start P3, any acquisition, or put the amendment in force until the owner decides.**

**P3: DAPFAM test, read once** (the next step if the owner keeps Scout; needs the owner's go-ahead)

1. `run_qwen_scout_actions.py build --split-name test`.
2. On the V100, `generate --actions P` (773 calls).
3. `build_scout_test_inputs.py`.
4. Nine dense runs (u/o/x × P/T/R2), each with `--family-ipc3`.
5. Run `analyze_scout_frozen_test.py` once.

**P4: E5 PatenTEB**

1. `analyze_patenteb_brief_gap.py build`.
2. Two dense runs on the V100 (encode the new corpus).
3. `analyze` once.

**P5:** draft the manuscript and figures. The owner reviews it. Never submit it.

### Running or external state

- **The MTM V100 job runs on dr-train** (see above). The earlier E3 job finished at 06:46Z on 7 Nov: three runs, all exit 0, 416 lines.
  - Outputs and receipts are on dr-train in `/home/chaw/patent-to-pilot-jobs/scout-public-demo/` and copied (hash-checked) to `../_private_artifacts/healthtech/scout-public-demo/e3-*.out.jsonl*`.
- No local servers were listening on 8787 or 5178 on 7 Nov.
- Private data:
  - `../_private_artifacts/healthtech/scout-public-demo/` holds the HUPD subset, vectors, rationales and book.
  - `../_private_artifacts/healthtech/ptp-org-adaptive-20261105/` holds the DAPFAM dev artifacts.
- Local venvs and model:
  - `C:/Users/User/.ptp-scout-venv` (CPU torch);
  - `C:/Users/User/.ptp-models/patembed-large`;
  - `C:/Users/User/.ptp-models/nli-deberta-v3-base` (rev `6c749ce3…`, Apache-2.0; the E3 NLI proxy);
  - `C:/Users/User/.hrv` (stopped hyperresearch; reference only).
- dr-train job directories:
  - `/home/chaw/patent-to-pilot-jobs/scout-public-demo`;
  - `/home/chaw/patent-to-pilot-jobs/org-adaptive-20261105`.

### Standing rules

- No paid API calls without new owner approval. Never read `.env`.
- No worktrees, resets or ACL/hook/global-config changes. Never run `hyperresearch install` in this repo.
- DAPFAM texts and generated texts stay out of Git.
- Never mention the superseded unpublished manuscript or its labels.
- Do not claim business or user validation. Developer decisions are a proxy.

## Current state — 4 Nov 2026 (supersedes the Normal-round hold below)

- Plan: [PTP_JOURNAL_LONG_RUN.md](docs/healthtech/long-runs/PTP_JOURNAL_LONG_RUN.md), with the owner amendments: E2 allowance USD10 cumulative, push after a verified package, dr-train V100.
- Canonical record: [WPI research package](docs/healthtech/audits/ptp-wpi-research-package-20261104/README.md).
- Track A (primary) used PANORAMA PAR4PC; the protocol was frozen at commit `ff603bb` before the test run. On test:
  - PatEmbed-claim MRR 0.933 vs BM25 0.845 (Δ +0.088, CI +0.058 to +0.120);
  - RRF hybrid was worse than dense alone (Δ −0.020, CI −0.038 to −0.004);
  - the cascade matched the hybrid with 57% escalation but did not beat dense alone.
- The PI4PC paragraph-level replication (freeze `1665075`) did **not** replicate the dense advantage (Δ +0.003, CI −0.017 to +0.022). Fusion beat dense there (Δ +0.014, Holm p = 0.042), and the cascade missed its tolerance. The best fixed policy depends on task granularity.
- Track B: canary content audit 9/9 literal-correct. The device known-link cohort stays descriptive.
- Spending this round: USD0 in paid calls and about 289 s of V100 encoding. The E2 ledger is unchanged since the canary (USD0.99945484 left under the code-enforced USD1; the owner allowance is USD10).
- Next steps: [NEXT_ACTIONS](docs/healthtech/audits/ptp-wpi-research-package-20261104/NEXT_ACTIONS.md). Owner decisions: [READINESS](docs/healthtech/audits/ptp-wpi-research-package-20261104/READINESS.md).
- 5 Nov 2026: an organization-adaptive cross-domain acquisition study on DAPFAM, written as a new self-contained manuscript. See the [protocol draft](docs/healthtech/research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md), the [PoC plan](docs/healthtech/research/ORG_ADAPTIVE_POC_PLAN_20261105_EN.md) and the [manuscript plan](docs/healthtech/research/ORG_ADAPTIVE_MANUSCRIPT_PLAN_20261105_EN.md).
  - Owner decisions: earlier unpublished analyses are superseded and not cited; only the neutral terms in the manuscript plan are used; organizations are IPC sections; the fixed baseline is the strongest dense passage retriever.
  - Stage 0 PASS: [audit](docs/healthtech/audits/ptp-org-adaptive-stage0-20261105/README.md). Test was not scored. Multi-window queries did not beat single-window on dev.
  - Stage 1 (dev): [audit](docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/README.md).
    - The preregistered gate passed: oracle − F\* 0.099, Q-only share 23%.
    - M\* is R2. The cross-fitted global mix was below R2 (−0.014, CI −0.028 to −0.002), and the per-section mix was below the global mix (−0.008).
    - Under Amendment 1, neither claim goes forward. Test not opened. Next is an owner decision on the direction.
  - Solution-scout feasibility (dev, 6 Nov 2026): `PARTIAL_LANE_ONLY` ([audit](docs/healthtech/audits/ptp-solution-scout-feasibility-20261105/README.md)).
    - The scout pool was below the lane-only pool (−0.066, CI −0.094 to −0.040), so the LLM claim is not carried forward.
    - Post hoc, the lane gain was traced to the IPC3 mask, which matches the strict-OUT definition. Test not opened; USD0 paid.
  - Solution-atlas headroom (dev, 6 Nov 2026): `GO_ORACLE_ONLY` ([audit](docs/healthtech/audits/ptp-solution-atlas-headroom-20261106/README.md)).
    - Oracle class reordering gave +0.059 R@50. The learned class prior gave −0.044 (CI −0.070 to −0.017).
    - Building an external prior is an owner decision. Test not opened; USD0 paid.
  - Product-led paper approved (6 Nov 2026): [solution-scout product spec](docs/healthtech/research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md). Status: M0 done (contracts, lane logic and the quote check in `src/patent_to_pilot/healthtech/scout.py`). The owner approved the four decisions in spec §9. M1 is done: replay-mode routes under `/scout-sessions` in `http.py`. Next is M2 (frontend).

Earlier status: `PAUSED_BY_OWNER_NORMAL_MAIN_ONLY_AUDIT`

Observed: 2026-11-04, Asia/Bangkok

Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`

This file is the resumable handoff for the existing Patent-to-Pilot goal. It records what is verified, what is still partial or blocked, which artifacts are authoritative, and which local worktrees must not be removed without preserving their uncommitted work. It is not a claim that the research goal, business validation, or journal submission is complete.

## Current Normal-round hold — 2026-11-04

This round works only in the existing `main` checkout. Base HEAD before the round was `a8c8e229e6489bb29ae6f88f310f7307c8a09441`, and `origin/main` matched it. Do not resume the goal, start a long run, create a worktree, dispatch or reserve paid work, push, merge, delete branches, or clean worktrees. The bounded deliverable is the E2 documentation/hash correction, offline fixture verification, isolated test-ledger verification, and this handoff update.

The canonical evidence for this round is `NORMAL_ROUND_20261104.md` plus `normal-verification.json` in `docs/healthtech/audits/ptp-e2-admission-recheck-20261104/`. The prior merge push/cleanup actions and the 20261103 candidate worktree remain historical receipts only.

Follow-up read-only check (2026-11-04T13:31–13:36Z): `docs/healthtech/audits/ptp-normal-mcp-admission-check-20261104/`. OpenRouter MCP account credit, exact-route pricing, account binding (hashed creator/workspace match), rights, writer quiescence, the E2 ledger, and dr-train SSH all passed. Paid admission remains blocked because the MCP key is not the dispatch key: the ledger needs a fresh key-scoped observation of `sha256:7cbe4013…`, plus owner authorization. A one-character erratum in the recorded normalized credit hash was fixed in all five affected files, with owner approval (correct value `…80408f9e9a5f06c5d`).

E2 paid canary (owner-authorized, 2026-11-04T13:54–13:56Z): `docs/healthtech/audits/ptp-e2-paid-canary-20261104T1354Z/`. Status is PASS as engineering/accounting evidence: 3/3 schema-valid, 3 settled attempts, 0 retries, USD 0.00054516 total, reconciled with MCP account usage. The ledger is now `d19f58ec…`, and the E2 epoch has USD 0.99945484 remaining. The paid API state is no longer "blocked before reservation". Any further paid work needs a new owner authorization and a new 300-second admission window.

## 1. Objective and scope

The goal is to deliver a usable Patent-to-Pilot HealthTech evidence workflow and a reproducible computational study suitable for owner review and possible submission to *World Patent Information*. The current study concerns device-patent known-link recovery and adaptive evidence acquisition under incomplete judgments.

The current round is a solo reproducible computational study. There are no external participants, no recruitment route, and no independent customer validation. Human pilot work, revenue, willingness-to-pay, and ROI are future work unless separately measured. A three-case product demonstration is engineering evidence only; it is not a powered scientific evaluation and is not user validation.

The product claim remains bounded: prepare an inspectable evidence dossier for an entrepreneur or investment analyst starting from a named public medical device or comparator. A retrieved candidate is not automatically a disclosed link. A literal field or quote match establishes source integrity only; it does not establish semantic entailment, clinical suitability, FTO, patent validity, regulatory approval, or investment merit.

## 2. Repository and revision state

The main checkout was clean before this handoff-document change.

- Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`
- Branch: `main`
- Main HEAD before this documentation update: `686f8338c4b288cfe706ae16f4aae8f885b81ebb`
- Pushed handoff HEAD: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`
- `origin/main` after push verification: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`
- Source merge already tested: `26be1c1f037c35352a5c0c4bbc8f0fbc0c135f09`
- Candidate integration commit: `a71d808`
- Preserved owner-main commit: `f77c502`
- Prior handoff documentation commit: `7e8fd1a`
- Initial handoff-document commit: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`.
- Cleanup-record commit already pushed: `46421f0d99f3425af1e841991411f80a21031a72`.

The following was the historical handoff check; it is retained for provenance and is not a current push instruction:

```powershell
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git rev-parse origin/main
rtk git rev-list --left-right --count main...origin/main
```

Historical result after push: clean `main`, identical local and remote SHA, and `0 0` ahead/behind.

The push completed on 2026-11-04 at approximately `2026-11-04T12:34:00Z` with `main -> origin/main`. The exact post-push verification at `2026-11-04T12:38:09.5419286Z` returned the same SHA on both sides and `0 0` ahead/behind.

## 3. Verified delivery boundary

### Engineering: COMPLETE for the current offline scope

The merged implementation covers the current offline engineering contract:

- local HTTP/UI path;
- retrieval and evidence projection;
- source inspection;
- edit, save, reopen, and history behavior;
- JSON and Markdown export;
- local generation and guarded accounting paths;
- candidate-bound regression coverage.

Recorded verification from the canonical merge audit:

- Python regression: exit `0`;
- exact candidate-bound receipt: `655 passed, 2 skipped`;
- frontend unit tests: `73 passed, 1 optional skip`;
- HealthTech JSON receipts parsed: `964`;
- source merge-marker scan: clean;
- non-audit `git diff --check`: clean.

This is an engineering statement for the current implementation and receipts. It is not a scientific or commercial completion claim.

### Scientific evidence: PARTIAL

The following remain incomplete or limited:

- no admissible final semantic device-patent holdout is bound to the current final study;
- no powered comparison has established adaptive superiority;
- no paid local/API matched comparison was completed;
- historical PatEmbed and multilingual-e5 artifacts are runtime-bound evidence and must not be silently reinterpreted as a new current-head run;
- Stryker material remains previously exposed diagnostic material, not final gold;
- DAPFAM is diagnostic and is not a semantic device-patent gold standard;
- unlisted links remain unjudged, not negative;
- known-link recall is not exhaustive recall or a lower bound on exhaustive recall.

The manuscript must keep fixed-budget, multi-query, simple-adaptive, and bounded-LLM controls distinct and must freeze cohort, splits, eligible queries, cutoffs, grouping, failure rules, endpoints, and budget controls before any final comparison.

### Business value: PARTIAL, solo proxy and scenario only

Observed engineering quantities may support a practical-potential discussion:

- citation quality and locator integrity;
- evidence coverage within the declared corpus;
- machine/GPU time;
- latency;
- recorded provider cost where an actual receipt exists;
- dossier completion and correction burden in the developer workflow.

The current evidence does not support claims of independent user validation, revenue, willingness-to-pay, customer demand, ROI, or production labor cost. Any labor-rate or volume assumption must remain a scenario or sensitivity analysis and must be labelled as such.

### Manuscript and WPI: PARTIAL

Draft manuscript, methods, figures/tables, references, appendix material, data/code availability language, ethics, funding, conflicts, author contributions, AI-use disclosure, cover letter, and checklist artifacts exist in the repository. Owner review remains required. Official journal-specific Aims and Scope and Guide for Authors details were not fully verified in the local environment, and no manuscript was submitted or accepted.

## 4. Paid/API state

No paid call, reservation, retry, GPU rerun, dataset download, ledger mutation, budget reset, or time-window reset was performed in the merged-main handoff.

Canonical ledger:

`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`

Known ledger state:

- SQLite integrity: `ok`;
- legacy settled receipts: `4`;
- known actual spend: `USD0.0001464`;
- operational attempts: `0`;
- pending or unknown operational attempts: `0`;
- prospective E2 allowance recorded in the handoff: `USD1`;
- unknown history: preserved and not silently treated as zero.

The previous credit snapshot was stale for the 300-second live gate. The paid branch therefore stopped before reservation. Do not create a zero ledger, reset the epoch, resend an unknown request, or edit an observation timestamp.

If paid work is explicitly resumed, the smallest required gate is one fresh non-secret credit snapshot for the existing dispatch key, current exact-route pricing observed in the same admission window, verified export rights, and a single bounded canary through the canonical ledger. The key must never be read from or printed from `.env` in logs or documentation.

## 5. Evidence map

Read these artifacts in this order when resuming:

1. `AGENTS.md`
2. `GOAL.md`, sections 0-4
3. `PLAN.md`
4. `docs/healthtech/progress.json`
5. `memory/next-actions.md`
6. `docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json`
7. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/README.md`
8. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/verification.json`
9. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/CHECKPOINT.json`

Key source and product areas:

- `src/patent_to_pilot/healthtech/` for the current HealthTech runtime;
- `src/patent_to_pilot/providers/` for provider identity, history, credit, and ledger boundaries;
- `scripts/healthtech/` for reproducible runners and audit tools;
- `tests/` for regression and handoff-bound evidence;
- `frontend/healthtech-web/` for the local UI and browser-facing adapters;
- `docs/healthtech/research/manuscript/` for the manuscript package;
- `docs/healthtech/audits/` for canonical receipts and continuation records.

Private artifacts, credentials, restricted corpora, model weights, and local owner evidence are not publication inputs merely because they exist on disk. Publish only permitted links, identifiers, hashes, and authored fixtures.

## 6. Local branch and worktree inventory at handoff

The following inventory was observed before cleanup. A blank status after the branch line means the worktree had no reported tracked or untracked changes at inspection time. Dirty worktrees contain uncommitted work and must not be removed without an explicit decision to discard or archive that work.

Clean or apparently clean at inspection:

- `claude/healthtech-ux-local-20261028` at `7ca0f2eab4a157d208fe0b9b949b83814e4fbcb2`, worktree `_worktrees/patent-to-pilot-claude-ux-20261028`, remote marked gone;
- `codex/remote-embeddings-20261030` at `68219d78ec0de4c6ffab7fdbc2c79bcacbf612cf`, worktree `_worktrees/patent-to-pilot-codex-remote-embeddings`;
- `codex/luna-publication-20261030` at `bf416e9ab6b6d2d031e885d4b6bb0a2d08bf9ebc`, worktree `_worktrees/patent-to-pilot-luna-publication-20261030`;
- `codex/research-product-o1-20261031` at `257037ab349ec88e5600c074deccfc8a62fe5fc2`, worktree `_worktrees/patent-to-pilot-o1-20261031`, with one untracked browser artifact and therefore not fully clean;
- `codex/pepo-ui-integration-20261031` at `0d049802d36bc2eebe60331ec444d62469fd767f`, worktree `C:/Users/User/Documents/Codex/2026-10-31/task/ptp-integration`;
- `codex/pepo-paused-audit-20261101` at `a0809b4b124a6e19b8aea58c4258397aa60715df`, worktree `C:/Users/User/Documents/Codex/2026-11-01/task-3/publish-http`.

Dirty or containing uncommitted work at inspection:

- `codex/patent-to-pilot-long-run-20261031` at `0cf41e0d37cac75bc9475c8604ab3dabb5c5fd66`, worktree `_worktrees/patent-to-pilot-long-run-20261031`; this contains broad source, test, audit, manuscript, and benchmark changes;
- `codex/r1-owner-evidence-20261031` at `f826069dddb74d4df9ca820a33c07355bec8b357`, worktree `_worktrees/patent-to-pilot-o3-safety-repair-20261031`; this contains manuscript, benchmark, audit, test, and protocol changes;
- `codex/pepo-unblock-remote-20261030` at `a0ec9ceaf381ebbce6e6c340a8b420189eb8474c`, worktree `_worktrees/patent-to-pilot-pepo-unblock-20261030`; this contains source, tests, and audit changes;
- `codex/research-product-o1-o4-20261031` at `b4bc13ccf8a9a71a8f50d16346ae1c6557bc69d0`, worktree `_worktrees/patent-to-pilot-research-product-20261031`; this contains benchmark, manuscript, business-value, test, and audit changes.

The cleanup request below is historical and is not executable in the current Normal round:

- clean, unused worktrees and their local branches may be removed after the push check;
- dirty worktrees must remain until their owner explicitly authorizes discard or a recoverable archive is created;
- no `reset --hard`, `checkout --`, `clean -fd`, force push, ACL change, safe-directory change, or deletion of `.git` data is allowed.

### 6.1 Cleanup performed after owner authorization

The owner explicitly authorized removal of worktrees with no filesystem activity for more than three days, and authorized removal of worktrees whose committed branch work was already merged because a new worktree will be created. Using the observed cutoff before 2026-11-01 and the ancestry checks recorded during this session, the following local worktrees/branches were removed:

- `claude/healthtech-ux-local-20261028` at `7ca0f2e...`; branch tip was an ancestor of `main` and last non-Git file activity was 2026-10-30;
- `codex/remote-embeddings-20261030` at `68219d7...`; last non-Git file activity was 2026-10-30 and the branch tip was retained only locally;
- `codex/luna-publication-20261030` at `bf416e9...`; branch tip was an ancestor of `main` and last non-Git file activity was 2026-10-30;
- `codex/research-product-o1-20261031` at `257037a...`; branch tip was an ancestor of `main`, its remaining untracked artifact was older than three days, and the worktree was removed;
- `codex/r1-owner-evidence-20261031` at `f826069...`; last non-Git file activity was 2026-11-01 09:59:41Z, more than 72 hours before cleanup;
- `codex/pepo-unblock-remote-20261030` at `a0ec9ce...`; branch tip was an ancestor of `main`, last activity was 2026-10-30, and the owner authorized cleanup of the old dirty worktree;
- `codex/pepo-ui-integration-20261031` at `0d04980...`; branch tip was an ancestor of `main` and the branch was deleted. Git removed the worktree registry entry, but Windows refused physical directory deletion because the exact orphan directory contained a protected `.pytest_cache` subtree. No ACL or permission bypass was attempted. The remaining orphan path is `C:/Users/User/Documents/Codex/2026-10-31/task/ptp-integration/.pytest_cache`.
- `codex/o3-safety-repair-20261031` at `9ac3872...`; branch-only local reference, no worktree, last commit 2026-10-31, deleted after the more-than-three-day inactivity check.

The following active worktrees were intentionally retained because they had filesystem activity within the last three days or contained newer uncommitted work:

- `codex/patent-to-pilot-long-run-20261031` at `0cf41e0...`; latest observed file activity 2026-11-02 16:59:23Z; dirty source/tests/audits;
- `codex/research-product-o1-o4-20261031` at `b4bc13c...`; branch tip is an ancestor of `main`, but the worktree contains newer uncommitted benchmark/manuscript/audit changes, latest observed file activity 2026-11-02 13:58:15Z;
- `codex/pepo-paused-audit-20261101` at `a0809b4...`; latest observed file activity 2026-11-01 14:20:18Z, which was still within the three-day window at cleanup.

After cleanup, the local branch set is exactly `main` plus the three retained branches above. Remote branches were not deleted because the owner requested local cleanup and a main push only.

## 7. Current Normal-round instructions

Treat `main` and the canonical audit files as the current control plane, but do not resume the goal in this round. Do not combine receipts from different heads into one PASS. A receipt is admissible only when its candidate revision, inputs, configuration, and output hashes match the claim being made.

First perform:

```powershell
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git rev-parse origin/main
Get-Content -Raw AGENTS.md
Get-Content -Raw GOAL.md
Get-Content -Raw PLAN.md
Get-Content -Raw docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json
```

For this round, complete only these local actions:

1. Verify the current `main` status, HEAD, authorship, and preserved worktree inventory.
2. Correct the E2 hash reference without changing the private snapshot or timestamp.
3. Run offline fixtures and the isolated test ledger; record exact commands and outcomes.
4. Update the handoff and stop before fresh credit, paid admission, GPU, long run, push, merge, or cleanup.

Do not rerun completed GPU work merely to refresh a receipt. Do not use the FDA-only canary as the main scientific result. Do not turn schema validity into content or retrieval validity. Do not claim user validation, revenue, willingness-to-pay, or ROI without measured evidence. Do not submit a paper or accept publisher terms for the owner.

## 8. Stop conditions and unresolved permissions

Stop and report when:

- a paid request lacks a fresh credit snapshot or current price;
- account/key binding is not reconciled;
- a request may have unknown billing state;
- source or dataset rights are unclear;
- an artifact is restricted or contains secrets;
- a worktree is owned by another writer and contains dirty changes;
- a result would require merging different candidate heads;
- a claim would exceed the declared cohort, gold, or evaluation design.

The next actor must preserve the existing ledger and historical receipts. The next actor must not manufacture a zero baseline, change timestamps, reopen a completed offline queue, or delete dirty worktrees merely to make the repository look clean.

## 9. Handoff outcome

Engineering: `COMPLETE_CURRENT_OFFLINE_SCOPE`

Scientific evidence: `PARTIAL`

Business validation: `PARTIAL_SOLO_PROXY_ONLY`

Manuscript/WPI readiness: `PARTIAL_OWNER_REVIEW_REQUIRED_NOT_SUBMITTED`

Paid API: `PASS_E2_CANARY_3_OF_3_USD0.00054516` (engineering only; see `ptp-e2-paid-canary-20261104T1354Z`); further paid work needs new owner authorization

Repository handoff: `READY_FOR_REVIEW`

Owner pause instruction: stop this Normal round after the local audit and test evidence. Resume only after the owner requests a new goal prompt; do not open a new goal for the same work.
