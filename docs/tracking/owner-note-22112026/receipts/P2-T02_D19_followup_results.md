# P2-T02 D19 follow-up receipt, P1-DEV

**Runtime state:** PatEmbed complete, all gates PASS and the pod deleted. Qwen3 C1 encoding active and Qwen3
evaluation NOT_RUN. Qwen3 passed preflight at 15:04:46 UTC, selected window 511 at 15:07:48 UTC and began C1
encoding at 15:20:29 UTC.
**Protocol:** P2-T02 coverage control `bd30d3f7` with A2 declared in `ffae7a99` and verified implementation
`d30d9d51`. D26 authorizes launch and up to USD 20 inside R2. The local stage is pinned in the
[D19 readiness receipt](P2-T02_D19_readiness.md).

| Model | Pod / region | Hourly price | Start (UTC) | Reservation | Receipt |
|---|---|---|---|---|---|
| PatEmbed | `arm09wy8rok4qk`, Secure A100 SXM 80 GB / US-MD-1 | USD 2.19 compute, up to USD 0.03 disk budget | 2026-11-24 13:47:49 | Released at deletion | PASS, deleted |
| Qwen3 | `10813cm5sej2s2`, Secure RTX PRO 4500 Server Edition / US-KS-2 | USD 0.72 compute, up to USD 0.03 disk budget | 2026-11-24 14:58:21 | USD 8.50 | Active |

Operational PatEmbed deadline 17:47:49 UTC includes transfers. The in-container timer reported armed for
17:55:49 UTC as a fallback. SSH upload started 13:49:10 UTC. Settlement will record actual disk, compute,
retrieval evidence, termination and any retries here.

Qwen3's RTX operating deadline is 25 Nov 01:46:21 UTC, including transfers, with a fallback timer at 01:54:21 UTC.
Combined reservations are USD 18. A fresh availability check showed capacity after the earlier monitored queue
expired. Dispatch is independent of any score.
Qwen3 uses the standard transfer route from its first launch. The success-only Bash collectors verify the pulled
archive hash before requesting termination, with independent provider-side verification still required.

## Incidents before any model result

- PatEmbed transfer finished and the remote input manifest passed at 13:54:45 UTC. Attempt 1 reached model
  provisioning and stopped at `models-patembed-pins` at 13:55:20 UTC. The downloader reported that
  `HF_HUB_ENABLE_HF_TRANSFER=1` required the absent optional `hf_transfer` package. Weight hashes had not yet been
  compared. Retry once on the same pod using the normal transfer path with this acceleration toggle set to zero.
  Preserve attempt 1 logs. The pinned files, verification requirements and teardown deadline stay fixed.
  The retry passed W and C-R at 13:57:05 UTC, completed serialisation and determined a window of 504 at 14:01:50 UTC.
- Qwen3's quote was lost during scheduling. The 13:54 UTC create returned HTTP 400, the account enumerated only
  PatEmbed, and a fresh US L40S catalog check returned NONE. No Qwen3 resource exists. Billing remains pending.
- The 14:36 UTC RTX direct creation also returned HTTP 400 with the provider reporting that no matching instance
  remained. A follow-up readiness read showed NONE and the account still listed only PatEmbed. The bounded queue
  request returned QUEUED at 14:37:38 UTC with `podId=null`. It reached EXPIRED at 14:45:36 UTC and still showed
  `podId=null`. The account listed only PatEmbed.

Four PatEmbed shards completed in 1,247 seconds of C1 encoding. The fourth shard averaged 461.2 tokens and the
remaining windows are length 504. Scaling the fourth shard by tokens or squared length projects another
84–92 minutes of encoding from that checkpoint, before retrieval, evaluation and pulling. This is a resource
estimate and does not alter the operational deadline.
Qwen3's first two shards completed in 1,240 seconds. The second shard took 941 seconds at 201.7 mean tokens, while
the remaining mean was 492.0. Token scaling gives about 437 minutes of remaining encoding from that point.
Squared-length scaling gives 1,039 minutes and extrapolates from much shorter sequences. Reassess using a later
matched-length shard. The separate Qwen3 operational deadline and reservation remain fixed.

## Reusable lexical corpus

PatEmbed produced the declared content at 14:09:25 UTC. The full-text passages were streamed to
`../_private_artifacts/p2t02-d19-runpod/complete-lexical-passages.jsonl.gz`. Decompressed SHA-256
`72e959189cc00e53233fd87f27296bb0dfd4eef067f83c1c4126437d20d15d79` equals the archive's Arctic
`ser-full/passages.jsonl` digest. The compressed SHA-256 is
`79b53f8dc994c6124ebe1f0498563077f5e9ab0c22a580135545773c1154b94d` (1,587,754,946 bytes).
This reusable representation artifact precedes any C1 effectiveness result.

## PatEmbed settled result

Bundle `../_private_artifacts/p2t02-d19-runpod/p2t02-d19-patembed-results.tgz`, SHA-256
`48f6bdac21c22fa37174f74bda900b322b398937c1232983836f63d5fadd3250`. The frozen analysis is the bundle member
`data/ptp-paper2/p2-coverage/d19/patembed/results-patembed.json`. All preflight, weights, relay, content, vector,
score and final gates passed. V checked 2,048 passages with token identity 100% and minimum cosine 1.0000.
Q checked 256 queries and their first 50 units with median score difference 0.00002 and 100% of differences
at most 0.005. The final gate binds the 504-token window to the content build.

| P1-DEV PatEmbed | ALL R@200 | IN R@200 | OUT R@200 | ALL R@1000 | OUT MRR |
|---|---:|---:|---:|---:|---:|
| C0 | 0.41806 | 0.49097 | 0.32821 | 0.61268 | 0.08008 |
| C1 | 0.42523 | 0.49730 | 0.33406 | 0.61766 | 0.08248 |
| C1 − C0 [95% CI] | +0.00718 [0.00505, 0.00936] | +0.00634 [0.00332, 0.00929] | +0.00585 [0.00290, 0.00884] | — | — |

The frozen rule selects **PatEmbed C1** as the representation baseline. The evaluator scored 26,547 eligible
ALL queries and retrieval ran for 25,626 with text. At 200, C1 newly retrieved 5,003 judged positives and
displaced 4,234 across the ALL comparisons. This is representation-control evidence.

Content build took 455.7 seconds at 14.63 GiB peak RSS, C1 encode took 6,203.0 seconds at 26.44 GiB peak RSS and
C1 retrieval took 1,238.4 seconds at 24.78 GiB peak RSS. The pack and provider pull check completed at 16:27:35 UTC.
The scoped CLI termination request exited 1. Management API delete returned 204 shortly after and GET returned 404.
Only Qwen3 remained in the account. Billing read immediately after deletion showed USD 3.80595 in posted buckets,
ending before the actual deletion. The observed effective running rate was USD 2.211/hour. Carry USD 6.00 as a
provisional total and reconcile posted billing after it catches up.
