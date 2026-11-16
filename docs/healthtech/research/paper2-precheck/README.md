# Paper 2 pre-checks: what has been tested (do not repeat)

Updated 2026-11-16. DAPFAM **dev only** (474 queries; strict-OUT n = 349). The test split was never read. CPU only, USD 0.

Every check was pre-declared before any number was computed and run once. All are development evidence on an exposed dev set, not confirmatory.

## Ledger of tested ideas

| # | Idea | When / where | Result (OUT R@200 vs dense) | Verdict |
|---|---|---|---|---|
| 1 | BM25 alone, and RRF(dense, BM25), at pool 200 | 5 Nov `audits/ptp-org-adaptive-stage1-20261105`; replicated 16 Nov [HEADROOM-RESULT.md](HEADROOM-RESULT.md) | RRF −0.020 (IN −0.055); union pool-400 reaches only 0.168 | NO_GO (replicated) |
| 2 | Six actions incl. LLM functional query, IPC-restricted query, pseudo-document; any fixed mix or per-IPC-section mix at 200 | 5 Nov Stage 1 + Amendment 1 | Best mix below dense (cross-fitted −0.014) | NO_GO |
| 3 | Per-query oracle choice of one action | 5 Nov Stage 1; reproduced 16 Nov | +0.094 headroom; LLM actions reach 120 OUT positives no other action reaches | Headroom exists but only with labels |
| 4 | Citation-learned IPC3 class prior ("which far classes hold the art") | 6 Nov `audits/ptp-solution-atlas-headroom-20261106` | Oracle classes +0.059 R@50; learned prior −0.044 | GO_ORACLE_ONLY, not built |
| 5 | Label-free per-query router (consensus, threshold switch, ridge gain model) on the six Stage 1 lists | 16 Nov [ROUTER-RESULT.md](ROUTER-RESULT.md) | Best router never switches (0% of headroom captured) | NO_GO |
| 6 | Paper 1 query rewriting (FA/GR/SACR) fused with B0; tail fusion A2 | Paper 1 S5 and A2 | ≈ 0 or negative; FA harms IN | Paper 1 (frozen) |

Also known from the earlier configuration study (prior journal draft; do not cite by name in study files): multi-retriever fusion barely beats the best single retriever; deepening the dense pool from 200 to 1,000 raises the perfect-ranker ceiling far more than reordering, yet most cross-domain targets stay unretrieved even at 1,000.

## What this rules out on DAPFAM dev

Label-free ways of mixing, restricting by class, or routing between the existing actions do not beat dense. The measured per-query headroom is real but no signal tested so far can find it without labels.

## Still open (not yet tested)

- Deeper pools (500 to 1,000) plus a reranker, under a matched compute budget.
- A new, legally grounded evaluation set from USPTO office actions (102/103 labels). D1/D2 (OA Research Dataset 2017, PatentsView IPC) are blocked by the USPTO.gov login; see [OA-DATA-FEASIBILITY.md](OA-DATA-FEASIBILITY.md).
- OA set sizing and temporal splits are done (16 Nov), with no retrieval run: [oa/OA-SPLITS.md](oa/OA-SPLITS.md).
  - 378,109 eligible tasks. DEV 2011, P2-TEST 2012, P3-TEST 2013 (about 53-55k tasks each).
  - The open-population corpus needs start year 1976 or 1990 to reach 80% OUT coverage, which means about 175-250 V100-h of encoding.
  - Draft pre-declaration: `plans/P2-OA-PREDECLARATION-DRAFT.md` (not frozen).
- An agent harness prototype exists on branch `claude/paper2-harness-0d504a` (23 CPU tests with doubles; no real backend). Not merged.

## Data already on this machine (check before downloading)

- DAPFAM source parquets: `methodology/datasets/research-only-nc/` (gitignored; identical to HF rev 780f4011; hardlinked into `../_private_artifacts/healthtech/ptp-paper2-oa-dapfam-meta/`).
- Family to IPC3 map: `../_private_artifacts/healthtech/ptp-org-adaptive-20261105/stage1/action-inputs/family-ipc3.jsonl`.
- Stage 1 rankings of all six actions (dev): `../_private_artifacts/healthtech/ptp-org-adaptive-20261105/stage1/`.
- PANORAMA PAR4PC/PI4PC val+test: `../_private_artifacts/healthtech/benchmark-expansion-20261101/`.
- HUPD 2017 (4.4 GB) on dr-train: `/home/chaw/patent-to-pilot-jobs/scout-public-demo/raw/hupd-2017.tar.gz`.
- MTM BigQuery citation extracts (examiner vs applicant flags, no 102/103): `../_private_artifacts/healthtech/medtech-time-machine/`.
