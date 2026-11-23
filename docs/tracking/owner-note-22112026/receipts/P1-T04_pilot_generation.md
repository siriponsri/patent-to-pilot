# P1-T04 (part 1): A3r1 DEV pilot generation, 23 Nov 2026

**Status:** generation COMPLETE. Route building, evaluation and the GO/STOP decision are **pending**: dr-train
(100.77.149.83) has been unreachable since about 07:00 Bangkok (SSH timeouts). No retrieval number exists yet.

| Model | Attempts | Usable | Content-unusable | Salvaged (cut at cap) | USD |
|---|---|---|---|---|---|
| qwen/qwen3-32b | 2,000 | 2,000 | 0 | 0 | 0.204912 |
| deepseek/deepseek-v4-flash-0731 | 2,000 | 2,000 | 0 | 0 | 0.236195 |
| google/gemini-2.5-flash-lite | 2,000 | 2,000 | 0 | 1 | 0.328229 |
| typhoon-v2.5-30b-a3b-instruct (pilot-descriptive) | 2,000 | 1,999 | 1 | 3 | 0.000000 |

- **Population:** the 2,000 frozen pilot apps (`g03-dev/a3/apps-pilot.json`). Frozen config sha256 `3d21f02e…`, with
  routing pins in force.
- **Retries and unknown cost:** 0 transport retries, 0 unknown-cost entries.
- **Ledger (E1R):** committed USD 0.785192 over 8,132 attempts, including the smoke and calibration calls.
- **Private outputs:** `../_private_artifacts/g03-a3r1/ledger/A3r1/<model>/P1-DEV.jsonl`; costs in
  `../_private_artifacts/g03-a3r1/pilot-costs.json`.
- **Next (when dr-train is back):**
  1. upload the ledgers to `g03-dev/a3r1/ledger/` and the costs to `g03-dev/a3r1/pilot-costs.json`;
  2. copy `g03_a3_routes.py`, `g03_a3_decide.py` and `g03_queue_a3r1_pilot.sh` to `g03-dev/code/`;
  3. run the queue detached under the GPU lock;
  4. apply the frozen GO rule. On GO, Stage B runs automatically (owner D16).

## Pilot evaluation on RunPod (D22/D23; amendment `A3R1-AMENDMENT-RUNPOD-REBUILD.md`) — 23 Nov 2026, 14:40–17:25 UTC

**Pods** (Secure Cloud US-MD-1, A100 SXM 80 GB, USD 2.19/h each; both deleted):

| Pod | Role | Run | Estimated cost |
|---|---|---|---|
| `5ouqfjd1xmjdsk` | patembed (H routes) | 14:40–16:17 | about USD 3.5 |
| `7fvpne0e0o2od1` | qwen3, then assemble | 14:40–17:25 | about USD 6.0 |

Both are charged to R2. Exact figures come from the billing read.

**Rebuild gate (amendment §3): PASSED, all parts.**
- A: corpus byte-identical.
- A2: query records identical.
- B: unit order identical.
- C: BM25-C0, copied from the P2-T02 pod, which had passed gate C exactly.
- E: PatEmbed-C0 per query identical on 99.932% of queries; the largest mean difference is 0.00015.
- D: Qwen3-C0 passed within its tolerance.
- F: v0 F\* passed.
- G: pilot population identical (25,626 apps; sample of 2,000).
- H: ledgers OK.
- The gate file and pod logs are in `../_private_artifacts/g03-a3r1-runpod/`.

**Frozen decision (`results-a3r1-pilot.json`): GO, Stage B with `deepseek/deepseek-v4-flash-0731`.**

Pilot F\* ALL R@200 = 0.4334 on 2,000 apps. Δ is the best allocation minus F\*, with a cluster bootstrap by art unit:

| Model | Stage-B-eligible | G_m | Best allocation | Δ ALL [95% CI] | Δ IN | Δ OUT |
|---|---|---|---|---|---|---|
| DeepSeek V4 Flash | yes | **0.4579** | L0-Q1-P1-H1-K1 | **+0.0245 [0.0179, 0.0310]** | +0.0230 [0.0139, 0.0320] | +0.0293 [0.0198, 0.0387] |
| Qwen3-32B | yes | 0.4443 | L0-Q2-P1-H1-K0 | +0.0109 [0.0051, 0.0168] | +0.0104 | +0.0110 |
| Gemini 2.5 Flash-Lite | yes | 0.4431 | L0-Q1-P1-H2-K0 | +0.0097 [0.0043, 0.0150] | +0.0104 | +0.0097 |
| Typhoon2.5 (descriptive only) | no | 0.4471 | L0-Q1-P1-H2-K0 | +0.0137 [0.0076, 0.0195] | +0.0129 | +0.0133 |

- The integrity check (`alloc-L0-Q2-P2-H0-K0` = F\* per query) holds for every model.
- **This pilot number is optimistic.** It is the best of about 66 allocations on the same queries, so it only gates
  spending. The research result is the VAL principal F3\* − F\* after Stage B, under the frozen continue/revise/park rule.
- Stage B started 2026-11-24 00:39 Bangkok time on the owner PC under E1R: 23,626 P1-DEV requests (the pilot reused)
  plus 1,919 VAL requests.
