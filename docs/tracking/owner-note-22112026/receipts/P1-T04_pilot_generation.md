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
