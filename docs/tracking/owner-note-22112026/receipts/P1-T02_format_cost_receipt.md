# P1-T02 — A3r1 format and cost calibration (TRAIN only)

Recorded 2026-11-23T06:00:00+07:00. Status: COMPLETE. Outcome: ENGINEERING_VERIFIED. This is not a retrieval result: no label,
qrel or retrieval score was read.

## Result

| Model | Complete / 32 | Truncated | Reasoning tokens | Prompt tokens max | Completion max | USD |
|---|---|---|---|---|---|---|
| deepseek__deepseek-v4-flash-0731 | 32 | 0 | 0 | 1601 | 376 | 0.003605 |
| google__gemini-2.5-flash-lite | 32 | 0 | 0 | 1582 | 403 | 0.005633 |
| qwen__qwen3-32b | 32 | 0 | 0 | 1788 | 364 | 0.005976 |
| typhoon-v2.5-30b-a3b-instruct | 32 | 0 | 0 | 1784 | 453 | 0 |

**Total:** 128 initial attempts, 128 usable, 0 retries, 0 unknown cost. USD 0.015214 under E1R.
Typhoon reported no cost; it is settled at 0 per owner decision D12.

**Format gate (amendment 3R1 §4):** every model passes (a) ≥ 30/32 complete, (b) ≤ 1 truncation,
(c) zero reasoning tokens and (d) every cost reconciled. No contract revision was needed.

## Deviations, disclosed

- **Sample rule.** The caller config committed before any call (c7b1686c) defines the sample: the 8 longest built
  prompts plus the 24 smallest sha256("g03-a3r1-calibration-v1:"+app_id). The PROPOSED amendment text described
  16 long + 16 general with another salt. The sample is TRAIN-only, deterministic, identical for all models, and
  excludes the A3r0 smoke app. It tests the output contract only. The difference is disclosed and changes no
  effectiveness rule.
- **Routing.** Calibration ran with unpinned OpenRouter routing (the served providers are listed in
  P1-T02_calibration_manifest.json). The pins in §3 apply from the pilot on. Qwen3-32B was partly served by
  SiliconFlow, which the pins now exclude.
- **Prompt length.** The measured maximum prompt is 1,582–1,788 tokens, above the planning figure of 1,100. The
  reservation bound uses the measured maximum, as §6.1 requires.
