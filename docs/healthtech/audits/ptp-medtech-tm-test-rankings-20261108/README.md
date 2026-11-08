# MTM test rankings, label-free (8 Nov 2026)

**Status: PASS (rankings only, NOT scored).** No labels were read, and `analyze_mtm.py --split test` has **not** run. Under rules §14, test scoring runs once, after the dev methods are frozen with owner approval.

## What ran

The MTM V100 job ran on dr-train (frozen code `7d317e7`, job dir `/home/chaw/patent-to-pilot-jobs/mtm-20261107`). See `status.log`. Every step exited 0, and the job ended `all done` at 2026-11-08T01:14:19Z.

| Step | Result |
|---|---|
| Briefs P-test (Qwen3-8B, greedy, fp16, prompt `ptp-solution-scout-v1`) | 1,955 calls; 0 failed, 0 truncated, 0 retries. Ran 22:40–01:03Z, mean latency 4.39 s. See `briefs-P-test.receipt.json` |
| Queries P-test | 1,955 queries, 0 briefs outside 25–120 words |
| Dense P-test, T-test, A-test | 1,955 queries each, 4 corpus views × lanes U/X, depth 200. Reused passage vectors (sha256 `8bb35aba…`), about 110 s ranking per view. See `receipt-{P,T,A}-test.json` (`labels_used: false`) |

The 24 ranking files and the briefs stay on dr-train and in the private artifacts. Only their sha256 values, recorded in the receipts, are in Git.

## Use

These files are the sealed baseline for the single test read. A dev-selected method that needs new test rankings, such as BM25 or a reranker, must produce them with code frozen before the read.
