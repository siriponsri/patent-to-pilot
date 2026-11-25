# P2-T04 prospective freeze, 25 Nov 2026

**State at freeze:** NOT_RUN. D19 selected both complete-content dense controls. No matched-screen retrieval
or scores had been produced.

| Pin | Value |
|---|---|
| Runner and separate evaluator | `ff9c20480a7d7bb3c569b912260355d2966596c0` |
| Runtime manifest SHA-256 | `e08af0434ace53069ed21e3cc62a9ff411ee282017800e91746b14de3ce97979` |
| Evaluator manifest SHA-256 | `16d733d7fbe4f3fbb29e7735a87ff35c3174f346534d415a51b3baf084cd908b` |
| Ordered cohort SHA-256 | `3911605ec0a8351d573c4f540a96387d998c78f5cd5273f7ed56500b2f5b4b4d` |
| CPU launcher SHA-256 | `ce7eed33edb697b5d5495bdc02d76e88781725d8455c4d38ac617c9adef0fce9` |
| PatEmbed C1 route SHA-256 | `94ced5664a9944a3ee153f99c93a35be20fd6869d6301bedcf0d1fa9b99d9d6c` |
| Qwen3 C1 route SHA-256 | `8df67c32daacbad2bdd044c9583902543138936ded80c8cfcff4c22674cd3fb9` |

Manifests are retained under `../_private_artifacts/p2t04-preflight-20261124/freeze-v1/`. The dr-train root is
`/data/ptp-paper2/p2t04-run-prep-20261124`. The runtime has only original P1-DEV query/source inputs and
precomputed rankings. The evaluator manifest binds the P1-DEV judgments and art units separately.

## Frozen comparison

Use the **Proposed freeze values** in the [prepared design](../../../healthtech/research/p2-coverage/P2-T04-SCREEN-PREPARATION.md)
as the frozen table. Both D19 models use C1 alongside Arctic C1 and BM25-full. Run the 2,000-app SHA-256 cohort
and the same 200-unit seed, lexical index, eligibility and reranker across arms. Keep the exact historical A3r1 F3*
as a same-cohort reference. Its representation is the earlier C0 configuration.

The unresolved-relation action uses the pinned P2-T03 policy and the deterministic English condition proxy.
Compare the targeted action to the deeper original query, static requirement, generic term-frequency feedback,
extractive feedback and shuffled binding variants. Retain inactive, empty and unjudged cases according to their
declared evaluator support. Report paired ALL, IN and OUT recall at 200 and recovery/displacement against each
comparison on the fixed cohort. Examiner art-unit bootstrap uses 10,000 replicates and seed 20261119.

For the progression decision, choose the strongest reported ALL mean among close controls, seed-only rerank,
complete-content fusion and individual complete-content routes. Ties go by arm ID. The targeted action must improve
ALL by at least 0.010 with lower bound above zero and IN and OUT lower bounds above −0.005. Report negative,
smaller and unsupported contrasts. Keep the result exploratory on P1-DEV.

## Execution gate

Require exact reproduction of the archived BM25-full top-1000 rows and displayed scores for every frozen app
before creating matched rankings. The hosted NumPy/scikit-learn environment is accepted only if the exact gate passes.
Run one CPU stage at a time on dr-train with up to eight numeric-library threads and a 30 GiB MemAvailable watchdog
restricted to the project job group. Estimated peak is 36 GiB. Prelaunch read showed about 118 GiB MemAvailable
and 985 GB free disk. Both runtime and evaluator require their recorded manifest hashes. No paid work is planned.
The final transfer verified the Qwen3 C1 route, both manifests and the launcher on dr-train before benchmark execution.

## Owner-approved cutoff amendment, 25 Nov 2026

**State at amendment:** matched-screen rankings and scores NOT_RUN. The preceding exact gate failed. Its separate
lexical census found 1,996 exact top-1000 runs and four differences confined to a verified score tie at the cutoff.
All 2,000 ordered top-200 prefixes and displayed scores were exact. The owner chose A and authorized one CPU-only
matched run under the following prospective validation rule.

Accept exact reproduction by default. For an unequal top-1000 pair under `verified-cutoff-tie/1`, require both
lists to have 1,000 rows. Compute the finite, positive raw cutoff score from the rebuilt rank 1,000 and find its tied
suffix. Require identical rows including displayed scores above the suffix, including all ranks 1 to 200. Require
every archived suffix unit to be eligible under the same filing-date and self-unit rules, with a rebuilt raw score
exactly equal to the cutoff and the matching four-decimal archived score. Reject every other difference. Record
exact and accepted-tie query counts, and bind the evaluator to the selected gate and counts.

| Amendment pin | SHA-256 |
|---|---|
| Runtime manifest `runtime-cutoff-v1.json` | `d3b7826783d53e958280f3c5150e0fb80a1264e9b315493e2f6e2f6f37f9a407` |
| Evaluator manifest `evaluator-cutoff-v1.json` | `5e16c2f3e77fece4fc97a8d2563d34aab39a25f420de2431d6fdac19ce681da8` |
| Launcher `launch-cutoff-v1.sh` | `0267033ecfe024ed421a10281ea7888ca2a63d5e51aef81afbd815492bd95343` |
| Runtime module `p2t04_run_screen.py` | `7d1aa3d397d896b82541144726d837b69737f3102e1ef3a97159eff424b06c1d` |
| Evaluator module `p2t04_evaluate_screen.py` | `35d0258101608ba332317895bd2fb93ec4463668ffff5ae5072ba5c38f8b0f73` |

The runtime manifest adds only the gate field, and the evaluator manifest updates only its runtime reference.
The same cohort, archives, candidate acquisition, evaluator, controls, bootstrap and progression rule apply.
The run uses the verified scikit-learn 1.7.2 overlay, existing NumPy 2.2.6 and SciPy 1.18.1, default AVX2,
one guarded CPU group at a time and the original memory limits. RunPod spend for P2-T04 is USD 0.

The targeted runner and evaluator fixtures passed. The full pypdf/PyThaiNLP test gate reported only the eight
known SACR r2/r3 budget supervisor failures allowed by `AGENTS.md`. The remote staged files matched all five
pins and both entry points loaded without reading benchmark inputs.
