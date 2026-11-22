# P0-T04: Prospective A3r1 protocol and no-call provider plan (22 Nov 2026)

**Result:** COMPLETE as a document. The protocol status is **PROPOSED**, not frozen. It freezes only at P1-T03.

**Spend for this task:**
- USD 0 and 0 inference calls.
- Free catalogue reads only: OpenRouter model, endpoint and docs metadata, and public Typhoon docs.
- No key and no `.env` file was read.

**Artifacts:**
- Amendment: [docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md](../../../healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md)
- Provider readiness, with ids, endpoints, prices and the forecast: [P0-T04_provider_readiness.json](P0-T04_provider_readiness.json)
- The A3r0 freeze file `G03-DEV-AMENDMENT-3-20261122.md` and `g03-dev-a3-spend.json` are untouched.

## Acceptance check (phase_tasks.csv row P0-T04)

| Criterion | Where |
|---|---|
| A3r0 preserved (prompt, 400 cap, 4 smoke receipts, USD 0.00064223) | Amendment §0 |
| Exact four-model, three-lineage panel | Amendment §2: `qwen/qwen3-32b`, `deepseek/deepseek-v4-flash-0731`, `google/gemini-2.5-flash-lite` (OpenRouter), and `typhoon-v2.5-30b-a3b-instruct` (native Typhoon API). Qwen3-32B and Typhoon2.5 share the Qwen3 lineage |
| Common proposed 800-token cap | Amendment §3 |
| Same 32 TRAIN cases per model, 128 initial attempts, deterministic | Amendment §4: two strata of 16 smallest sha256(`g03-a3r1-format-v1` + app_id). The long stratum has abstract and claim both at the 1,500-character cut. TRAIN only, smoke app excluded |
| Prices, identity and access recorded without model calls | Readiness JSON. Every credential is "credential not verified" |

## Decided in the proposal (subject to freeze)

- **Effectiveness rules are kept from A3r0 unchanged:**
  - the endpoint, the same 2,000 P1-DEV pilot apps, the 70 arms and the integrity gate;
  - the GO rule (Δ ≥ +0.005 and CI lower bound > 0);
  - Stage B, the F3\* tie rule and the VAL CONTINUE / REVISE / PARK rule;
  - the bootstrap, and the fourth-VAL-look disclosure.
- **Declared pre-effectiveness changes:**
  - (1) the panel;
  - (2) `max_tokens` 400 → 800, common to all models;
  - (3) pinned provider routing with `max_price`;
  - (4) the format gate and failure accounting;
  - (5) selection of m\* only among models that are **Stage-B-eligible under the approved envelope**. Eligibility is
    frozen before the pilot.
  - Change (5) fixes the A3r0 gap where Haiku's Stage B of about USD 7.8 could not finish under the USD 6 stop.
- **The A3r0 prompt is kept verbatim.** No `response_format` and no per-model repetition penalty are used.
- **A3r1 results stay on scoreboard A only.**

## Forecast summary (USD; details in the JSON)

| | Qwen3-32B | DeepSeek V4 Flash 0731 | Gemini 2.5 Flash-Lite | Typhoon2.5 |
|---|---|---|---|---|
| Pilot, 2,000 calls (central / bound) | 0.36 / 0.98 | 0.32 / 0.81 | 0.49 / 0.86 | unknown |
| Stage B, 25,545 calls (central / bound) | 4.64 / 12.52 | 4.05 / 10.35 | 6.31 / 10.98 | unknown |
| Complete programme if selected (central / bound) | 6.91 / 17.69 | 6.23 / 15.20 | 8.83 / 15.93 | unknown |
| E1 (stop at 6.00) | no | no | no | no (unknown cost) |
| E1R (50, pending) | yes | yes | yes | pending access and terms |

The complete-programme figure includes the smoke spend, all three paid calibrations and pilots, the USD 0.20 Workbench
reserve and a 15% reserve.

- **Planned initial requests:** 33,677. That is 96.2% of the E1 cap and 33.7% of the E1R cap.
- **Under E1, no primary model can finish Stage B**, so by the amendment's §6.1 the A3r1 pilot does not dispatch.

## Pending (not decided here)

1. **Owner:** approve E1R, or an approved alternative. This is the P1-T01 prerequisite.
2. **Owner:** provide a Typhoon API key (`TYPHOON_API_KEY`) and confirm the free-tier terms or quota for about 27,600
   requests. Otherwise Typhoon is declared "deferred (access)" at freeze and the pilot runs with three models.
3. **Owner:** set `OPENROUTER_API_KEY`, which P0-T01 recorded as absent. Top up OpenRouter credits before Stage B; about
   USD 8.365 is left.
4. **P1-T01:** do a fresh catalogue read, finalise the routing pins, and check key presence only.
5. **P1-T02:** run the calibration. Measured token maxima replace the planning assumptions.
6. **P1-T03:** reconcile the denominators. The manifests give 25,626 P1-DEV and 1,919 VAL; the evaluator n is 26,547 and
   1,999. Then freeze and reserve.
