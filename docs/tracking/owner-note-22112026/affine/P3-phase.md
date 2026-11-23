# P3 — Thai transfer and structural scope evaluation

Phase status: **IN_PROGRESS**

**Entry rule:** Start each task only when its listed task dependencies and execution authority hold. Entry requirements describe the first available work; AFFiNE and full P0 completion do not gate research.

**Exit rule:** Required tasks have verified evidence or an explicit permitted skip; material blocked work prevents COMPLETE. Research outcome is reported separately.

| Task | Title | Status | Outcome | Next |
|---|---|---|---|---|
| P3-T01 | Prepare Thai dataset/profile rights and exposure adapters | ✅ COMPLETE | ENGINEERING_VERIFIED | P3-T02 (needs per-item download approvals / packet rights) |
| P3-T02 | Build grouped source packets and independent judgments | 🔄 IN_PROGRESS | NOT_RUN | P3-T04 |
| P3-T03 | Run separate Thai text-transfer comparisons | ⏳ NOT_STARTED | NOT_RUN | P3-T05 |
| P3-T04 | Evaluate structural scope and OCR end to end | ⏳ NOT_STARTED | NOT_RUN | P3-T05; P4-T03 |
| P3-T05 | Freeze supported Thai scope and transfer claims | ⏳ NOT_STARTED | NOT_RUN | P4-T05; P5-T02 |

## P3-T01 — Prepare Thai dataset/profile rights and exposure adapters

- **Status:** see the table above (single place to update)
- **Depends on:** P0-T06
- **Acceptance evidence:** Pin allowed releases, units, licenses and prior exposure; separate Gazette, NitiBench/NitiBench+, real packets and OCR diagnostics; do not accept a gate or download without authority.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P3-T01_thai_data_contract.md; src/patent_to_pilot/workbench/datasets/thai_contract.py; tests/test_p3_t01_thai_contract.py
- **Check:** 36 new + G02 dataset tests = 63 pass; no downloads
- **Next:** P3-T02 (needs per-item download approvals / packet rights)
- **Blocker:** —
- **Notes:** [2026-11-22] agent started (no downloads) | [2026-11-23] pins: Gazette 87e695ee (CC BY 4.0, exposed), NitiBench 9f756970 (MIT), NitiBench+ 41286bcb (gated, not accepted), ThaiOCRBench ca610d1a (CC BY-SA); six separate scoreboards enforced; Gazette marked exposed + not product-bundled

## P3-T02 — Build grouped source packets and independent judgments

- **Status:** see the table above (single place to update)
- **Depends on:** P3-T01
- **Acceptance evidence:** Separate development and held-out families/variants; retain source rights and provenance; prioritize binding/annex/table/date tasks; label synthetic versus real; ground judgments independently of the tested policy.
- **Evidence:** docs/tracking/owner-note-22112026/receipts/P3-T02_thai_data_download.md
- **Check:** NOT_CHECKED
- **Next:** P3-T04
- **Blocker:** dr-train unreachable (ssh timeout) 23 Nov: local copy verified, remote copy pending
- **Notes:** [2026-11-23] D18 downloads done locally: Gazette 87e695ee, NitiBench 9f756970, statute 069e774f, WangchanX train 654e1a10 (17 files, sha256 = Hub oids); test splits labelled HELD_OUT; WangchanX train overlaps NitiBench-CCL -> audit before DEV use

## P3-T03 — Run separate Thai text-transfer comparisons

- **Status:** see the table above (single place to update)
- **Depends on:** P3-T01; P2-T05
- **Acceptance evidence:** Use the frozen engine on a declared Thai scoreboard; compare relevant specialist/parent baselines fairly; disclose Typhoon-S specialization and public-benchmark exposure.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P3-T05
- **Blocker:** —

## P3-T04 — Evaluate structural scope and OCR end to end

- **Status:** see the table above (single place to update)
- **Depends on:** P3-T02; P2-T03
- **Acceptance evidence:** Compare equal-content flat/parent/page controls, actual evidence correctness and changed bindings; distinguish Garuda-like appearance from issuer/authenticity; report OCR effects separately.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P3-T05; P4-T03
- **Blocker:** —

## P3-T05 — Freeze supported Thai scope and transfer claims

- **Status:** see the table above (single place to update)
- **Depends on:** P3-T03; P3-T04
- **Acceptance evidence:** State which languages/document types/tasks were actually tested, which improved, and which failed; retain separate scoreboards and data provenance.
- **Evidence:** pending
- **Check:** NOT_CHECKED
- **Next:** P4-T05; P5-T02
- **Blocker:** —
