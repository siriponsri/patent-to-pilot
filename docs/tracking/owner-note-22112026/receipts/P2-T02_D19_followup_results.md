# P2-T02 D19 follow-up receipt, P1-DEV

**Runtime state:** both models completed and all gates passed. Both result bundles were verified and both pods were
deleted. Qwen3 billing still awaits the last posted bucket.
**Protocol:** P2-T02 coverage control `bd30d3f7` with A2 declared in `ffae7a99` and verified implementation
`d30d9d51`. D26 authorizes launch and up to USD 20 inside R2. The local stage is pinned in the
[D19 readiness receipt](P2-T02_D19_readiness.md).

| Model | Pod / region | Hourly price | Start (UTC) | Reservation | Receipt |
|---|---|---|---|---|---|
| PatEmbed | `arm09wy8rok4qk`, Secure A100 SXM 80 GB / US-MD-1 | USD 2.19 compute, up to USD 0.03 disk budget | 2026-11-24 13:47:49 | Released at deletion | PASS, deleted |
| Qwen3 | `10813cm5sej2s2`, Secure RTX PRO 4500 Server Edition / US-KS-2 | USD 0.72 compute, up to USD 0.03 disk budget | 2026-11-24 14:58:21 | Released at deletion | PASS, deleted |

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
Qwen3's fourth shard finished at about 16:53 UTC. It took 2,575 seconds at 467.6 mean tokens. The remaining
2,470,090 windows are length 511. Token and squared-length estimates give 442–480 minutes of remaining
encoding from this checkpoint, then retrieval, evaluation and pull. Keep the 01:46:21 UTC operational deadline.
Shard five was full-width and took 2,821 seconds, finishing around 17:40 UTC. Equal-length scaling of the
remaining 2,207,946 windows projects roughly 396 minutes of remaining encoding from that point.
Shard ten finished around 21:35 UTC at 22,468 seconds cumulative. Full-width shard timing remains on schedule.
Two direct SSH watcher reads failed transiently around 20:00 UTC and recovered. The encode kept running.
Qwen3 C1 encoding finished at 00:16:19 UTC. The encoder logged 32,148 seconds total, including the final merge.
The provider management API remains the verified deletion path. Both in-pod Qwen3 scoped CLI self-lookup
forms were unverified, so the in-pod timeout is only a fallback.

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
provisional total and reconcile posted billing after it catches up. The subsequent provider read after the
16:00 UTC bucket caught up reports USD 5.98138593, including USD 5.92583037 GPU and USD 0.05555556 disk.
This replaces the provisional charge.

## Qwen3 settled result

Bundle `../_private_artifacts/p2t02-d19-runpod/p2t02-d19-qwen3-results.tgz`, SHA-256
`1f64625c0d6d47c5d8f8f96815ba7bd299fc85f3250a9a1432d1707f9d108321`. The frozen analysis is bundle member
`data/ptp-paper2/p2-coverage/d19/qwen3/results-qwen3.json`. All gates passed. V checked 2,048 passages with
100% token identity and minimum cosine 1.0000. Q checked 256 queries and their first 50 units, with median score
difference 0.00013 and 100% of differences at most 0.005. The final gate binds the 511-token window to the build.

| P1-DEV Qwen3 | ALL R@200 | IN R@200 | OUT R@200 | ALL R@1000 | OUT MRR |
|---|---:|---:|---:|---:|---:|
| C0 | 0.34736 | 0.40677 | 0.27408 | 0.51994 | 0.07185 |
| C1 | 0.35941 | 0.41794 | 0.28439 | 0.53721 | 0.07482 |
| C1 − C0 [95% CI] | +0.01205 [0.01007, 0.01409] | +0.01117 [0.00806, 0.01434] | +0.01030 [0.00729, 0.01323] | — | — |

The frozen rule selects **Qwen3 C1**. The evaluator scored 26,547 eligible ALL queries and retrieval ran for
25,626 with text. At 200, C1 newly retrieved 5,229 ALL judged positives and displaced 4,004.

Content build took 292.0 seconds at 14.69 GiB peak RSS. C1 encode took 32,149.0 seconds at 28.02 GiB peak RSS and
retrieval took 660.8 seconds at 25.84 GiB peak RSS. Gates finished 25 Nov 00:27:47 UTC and the result pack
finished at 00:28:47. The archive pull verified 00:30:13. Scoped CLI termination exited 1. Management API delete
returned 204 at about 00:34:53 UTC and a subsequent GET returned 404. The account pod list was empty.

The first Qwen3 post-teardown read showed USD 6.33205 in the 24 Nov billing bucket. The 25 Nov closing bucket
had yet to post. The observed live rate was USD 0.741/hour and the conservative carry is USD 7.20 until posted
billing catches up. D19 posted PatEmbed plus provisional Qwen3 is USD 13.18 of the USD 20 sub-cap, inside R2.
Both complete-content dense representations go into the P2-T04 freeze alongside Arctic C1 and BM25-full.
