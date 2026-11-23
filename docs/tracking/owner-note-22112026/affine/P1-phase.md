# P1 — Reproducible model-panel and A3 experiment

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P1-T01 | Resolve paid execution prerequisites and exact scope | ✅ COMPLETE | ENGINEERING_VERIFIED | P1-T02 |
| P1-T02 | Calibrate the complete output contract on TRAIN only | ✅ COMPLETE | ENGINEERING_VERIFIED | P1-T03 |
| P1-T03 | Freeze A3r1 eligibility, configuration and pilot manifest | ✅ COMPLETE | ENGINEERING_VERIFIED | P1-T04 |
| P1-T04 | Execute the declared four-model DEV pilot and spending decision | 🔄 IN_PROGRESS | NOT_RUN | P1-T05 on GO; P1-T06 on STOP |
| P1-T05 | Run one selected Stage B only after GO | ⏳ NOT_STARTED | NOT_RUN | P1-T06 |
| P1-T06 | Close A3 evidence and hand off the constructive ladder | ⏳ NOT_STARTED | NOT_RUN | P2-T02; P2-T04; P5-T02 when evidence exists |

## P1-T01 — Resolve paid execution prerequisites and exact scope

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T04; P0-T05; P0-T07
- **Acceptance evidence:** Verify credentials by presence only, exact served IDs, documented controls and the accepted budget scope; no generation call. Record readiness true only with matching authority and feasible complete planned scope.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json
- **Check:** keys present (presence only); Typhoon /v1/models lists typhoon-v2.5-30b-a3b-instruct; E1R approved in ledger; OpenRouter credits total 20
- **Next:** P1-T02
- **Blocker:** —
- **Notes:** [2026-11-22] E1R approved and recorded in ledger (D11); Typhoon stays in panel (D12); PatenTEB partial audit accepted (D14)

## P1-T02 — Calibrate the complete output contract on TRAIN only

- **Status:** see the table above (single place to update)
- **Depends on:** P1-T01
- **Acceptance evidence:** Use the same fixed 32 allowed TRAIN cases per primary model; record all 128 initial attempts, raw/parsed completeness, truncation and cost; no retrieval-quality scoring.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P1-T02_format_cost_receipt.md; docs/tracking/owner-note-22112026/receipts/P1-T02_calibration_manifest.json
- **Check:** 128/128 complete, 0 truncation, 0 reasoning tokens, USD 0.0152
- **Next:** P1-T03
- **Blocker:** —
- **Notes:** [2026-11-23] sample rule = caller-config rule (disclosed deviation from proposed amendment text); calibration routing unpinned

## P1-T03 — Freeze A3r1 eligibility, configuration and pilot manifest

- **Status:** see the table above (single place to update)
- **Depends on:** P1-T02
- **Acceptance evidence:** Freeze panel, prompts, cap, failure handling, prices, eligibility and complete-stage forecast before DEV scores; reserve approved budget; preserve exact A3 effectiveness rules.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P1-T03_freeze_receipt.json; docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json
- **Check:** config sha256 3d21f02e...; 3 paid models Stage-B-eligible (bound 17.8-21.0 <= 50); Typhoon pilot-descriptive
- **Next:** P1-T04
- **Blocker:** —

## P1-T04 — Execute the declared four-model DEV pilot and spending decision

- **Status:** see the table above (single place to update)
- **Depends on:** P1-T03
- **Acceptance evidence:** Run the same declared 2,000 DEV queries per eligible planned model; report all attempts/populations and paired results; apply frozen GO without adding a later IN/OUT rule.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md
- **Check:** NOT_CHECKED
- **Next:** P1-T05 on GO; P1-T06 on STOP
- **Blocker:** —
- **Notes:** [2026-11-23] pilot generation started 23 Nov (4 models x 2,000 P1-DEV, E1R ledger) | [2026-11-23] A3r1 evaluation on RunPod (D23): pods 7fvpne0e0o2od1 (qwen3) and 5ouqfjd1xmjdsk (patembed), A100 SXM secure US-MD-1, USD 2.19/h each, started 14:40 UTC; rebuild gate before frozen GO/STOP

## P1-T05 — Run one selected Stage B only after GO

- **Status:** see the table above (single place to update)
- **Depends on:** P1-T04
- **Acceptance evidence:** Reuse selected pilot outputs; run remaining declared DEV/VAL under reservations; disclose repeated VAL exposure and unchanged evaluator rules.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P1-T06
- **Blocker:** —

## P1-T06 — Close A3 evidence and hand off the constructive ladder

- **Status:** see the table above (single place to update)
- **Depends on:** P1-T04
- **Acceptance evidence:** Attach scored result or documented Stage B skip, model eligibility, failure rates, all costs and next decision; distinguish format, exploratory gain and supported evidence.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P2-T02; P2-T04; P5-T02 when evidence exists
- **Blocker:** —
