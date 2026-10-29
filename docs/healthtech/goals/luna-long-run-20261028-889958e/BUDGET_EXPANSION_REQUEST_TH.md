# Budget/data expansion request — filled draft (no submission)

สถานะเอกสาร: **PENDING / NO EXTRA SPEND AUTHORIZED**
วันที่จัดทำ: 2026-10-29 (Asia/Bangkok)
รอบอ้างอิง: `PTP-HT-OR-R1-20261028-USD8`
ขอบเขต: `research/patent-to-pilot`

เอกสารนี้เป็นคำขอที่กรอกจากหลักฐานปัจจุบันเพื่อให้ owner ตัดสินใจได้ภายหลัง ไม่ใช่การอนุมัติ ไม่ใช่การส่งคำขอภายนอก และไม่ dispatch paid/provider action ใด ๆ ในรอบนี้

## คำขอที่ owner ตัดสินได้

**ข้อเสนอที่แนะนำในตอนนี้:** ขอเพิ่ม API authorization ใหม่ `USD 0.00` และยังไม่เปิด paid round ใหม่ จนกว่าจะปิด blocker ด้านสิทธิ์ cohort, independent company/family groups, final holdout, current model/provider metadata และ provider-transfer bounds ให้ตรวจได้

ทางเลือกที่เตรียมไว้:

- **Approve recommended bounded study:** อนุมัติเฉพาะการเตรียม rights-cleared cohort และ protocol/holdout freeze ก่อน; ยังไม่อนุมัติ API spend ใหม่ในเอกสารนี้
- **Approve smaller design:** ทำ rights/evaluator/backend preparation แบบ offline ต่อด้วย `USD 0.00` API spend
- **No further API spending:** คง paid/provider HT-B4 เป็น `BLOCKED_LOCAL` และทำ offline continuation ต่อ

การซื้อ credits, top-up, subscription, การเปลี่ยน security หรือการซื้อ/โอนข้อมูลเป็น transaction แยกต่างหากและไม่ถูกร้องขอโดยเอกสารนี้

## 1. สิ่งที่ได้จาก R1 แล้ว

- **Report/protocol/final tested evidence:** `docs/healthtech/audits/luna-long-run-20261029-m4-r1-4c863d0/README.md`, `REPORT.md`, `verification.json`; current-head M1 revalidation ที่ `docs/healthtech/audits/luna-long-run-20261029-m1-revalidation-20261029/`; current-head M3 freeze ที่ `docs/healthtech/audits/luna-long-run-20261029-m3-current-head-cf613c0/`
- **Owner cap/policy:** R1 total authorization `$8.00`, admission threshold `$7.00`, internal reserve `$1.00`, phase caps `canary=$0.40`, `paired_pilot=$5.40`, `robustness=$1.20`, concurrency `1`, automatic retries `0`, unknown billing blocks future dispatch. Policy evidence: `docs/healthtech/audits/luna-long-run-20261029-m4-r1-4c863d0/REPORT.md` and `verification.json`
- **Actual paid usage:** provider calls `0`; paid cost `$0.00`; live canary, paid pilot, credential/credit check, and generation reconciliation remain `NOT_RUN`. HT-T2 now has a current local dev prediction manifest and evaluator-only score over `300` claims and `5,183` corpus documents, plus a separate error analysis at `docs/healthtech/audits/luna-long-run-20261029-ht-t2-error-analysis-20261029/`; it remains development-only and separate from HT-T1. The provider-shaped mock is pinned to model `openai/gpt-4.1-mini` through upstream `openai`; the current endpoint snapshot records prompt `$0.40/M`, completion `$1.60/M`, snapshot hash `a990baa4d0ac46e188981b3c8b400c84da38250c5d2ab9fb23eb420ffeb8a267`, and snapshot time `2026-10-29T11:18:41.615320Z`. This documentation package did not open or inspect the private budget journal; no paid reservation was created by this package, and any private-ledger unknown balance remains unverified here.
- **Development cohorts:** Abbott: 3 devices, 41 patents, 61 disclosed pairs, 62 unjudged distractor pairs, 2 exact-patent groups, 1 company group, no final holdout. Boston Scientific WATCHMAN: 2 devices, 7 patents, 13 disclosed pairs, 1 unjudged distractor pair, 1 exact-patent group, 1 company group, no final holdout. Source: `docs/healthtech/audits/luna-long-run-20261029-m3-current-head-cf613c0/comparison.json`
- **Observed offline controller evidence:** Boston macro/micro known-link Recall@20 `1.0/1.0`, ceiling-limited because `K=20` exceeds its 7-patent universe. Abbott macro/micro known-link Recall@20 `0.49880241951853205/0.47540983606557374`; exact-patent group recall `0.3364389233954451` for the MitraClip/TriClip group and `0.8235294117647058` for the Tendyne group. These are offline development results, not paid R1 effects.
- **M10/M11 final-holdout result:** The untouched 3-device/24-patent Stryker holdout reports HT-B4-MOCK macro/micro known-link Recall@20 `0.8857142857142857/0.8461538461538461` across 8 provider-shaped calls and 120 rerank pairs. B4 matches HT-B3 and remains below HT-B0b/HT-B1/HT-B2 on macro recall. Simulated debit was `$0.0008`, paid cost `$0.00`, with 0 unknown/pending billing items and no ledger breach. Consolidated report: `docs/healthtech/audits/luna-long-run-20261029-m11-report-refresh-20261029-r2/`.
- **Decision impact:** This holdout result does not justify paid/provider expansion or a claim of adaptive benefit. The recommendation remains `$0.00` incremental authorization and no paid branch until semantic labels, rights-cleared independent groups, transfer readiness, current provider identity/pricing, hard bounds, and reconciliation are evidenced.
- **What the current evidence answers:** the bounded offline controller can select constrained actions, preserve attempts/resource accounting, and maintain runtime/evaluator separation over the frozen development slices; the shared HT-B0a/B0b/B1/B2/B3 prefix and `K=20` comparator are reproducible at current head.
- **What remains unresolved:** no evidence that adaptive acquisition improves quality or cost; no live/provider HT-B4 result; no rights-cleared main cohort with explicit device-patent semantic labels, multiple independent company/family groups, and a predeclared final holdout; no clinical, FTO, patent-validity, exhaustive-recall, investment, or publication claim.
- **Why more independent groups matter:** current slices have one company group each, few effective exact-patent groups, no final holdout, and Boston is ceiling-limited. Repeated seeds or repeated queries within the same groups would not create independent evidence; a new cohort must be rights-cleared, group-aware, and frozen before any confirmatory interpretation.

## 2. Proposed additional experiment

| Option | Hypothesis / value of information | New eligible independent groups and controls | Chargeable design | What conclusion remains limited |
|---|---|---|---|---|
| A — recommended | A rights-cleared cohort with multiple independent company/family groups and an untouched final holdout is the next discriminator for whether adaptive evidence acquisition changes known-link recovery or resource use. | Freeze the cohort, query universe, group mapping, denominator, fixed HT-B0a/B0b/B1/B2 controls, and simple HT-B3/HT-B4 policy before final access; exact group count is determined by the rights audit, not invented here. | `USD 0.00` now. Revisit a future paid canary/paired design only after current model/provider identity, official pricing snapshot, payload-transfer basis, and worst-case call/token bound are verified. | Still limited to documented device–patent link recovery under incomplete judgments; not semantic relevance gold, clinical suitability, FTO, validity, exhaustive recall, or investment merit. |
| B — smaller | A single additional permitted development slice can test ingestion, joins, provenance, and denominator mechanics without claiming generalization. | One newly rights-cleared development slice plus existing controls; no final scientific claim. | Offline only; `USD 0.00` new API spend. | Precision and generalization remain unresolved; no power estimate and no superiority claim. |
| C — offline only | Completing rights matrix, cohort manifest, HT-T2 prediction/denominator contract, error analysis, and backend checks reduces uncertainty before any paid call. | No new external group required for the engineering pass; keep Abbott/Boston as development-only references. | `USD 0.00` new API spend. | Paid/provider behavior and adaptive benefit remain `NOT_RUN`; HT-T2 remains a dev-only component score with no hidden/test claim. |

Any future model change must be selected on separate development material and evaluated on untouched final groups. Existing development results cannot be reused as confirmation after tuning.

## 3. Cost estimate from current exact pricing

The inspected provider-shaped input package includes an exact endpoint snapshot for `openai/gpt-4.1-mini` through upstream `openai`: prompt `$0.40/M` and completion `$1.60/M`, captured at `2026-10-29T11:18:41.615320Z` with snapshot hash `a990baa4d0ac46e188981b3c8b400c84da38250c5d2ab9fb23eb420ffeb8a267`. This is pricing metadata for admission planning, not evidence of current account credit, provider availability, transfer rights, or a paid request.

| Component | Model/provider/price snapshot | Planned calls | Full input bound | Hard billable output bound | Conservative per-call reservation | Subtotal |
|---|---|---:|---:|---:|---:|---:|
| Canary for changed condition only | `openai/gpt-4.1-mini via openai; prompt $0.40/M, completion $1.60/M; snapshot a990baa4...8a267` | `0 admitted` | `NOT_SET` | `NOT_SET` | `NOT_ADMITTED` | `$0.00 now` |
| Controller/query generation | `openai/gpt-4.1-mini via openai; prompt $0.40/M, completion $1.60/M; snapshot a990baa4...8a267` | `0 admitted` | `NOT_SET` | `NOT_SET` | `NOT_ADMITTED` | `$0.00 now` |
| Charged fixed control | `openai/gpt-4.1-mini via openai; no paid fixed-control run` | `0 admitted` | `NOT_SET` | `NOT_SET` | `NOT_ADMITTED` | `$0.00 now` |
| Required repeat/sensitivity | `openai/gpt-4.1-mini via openai; group design not frozen` | `0 admitted` | `NOT_SET` | `NOT_SET` | `NOT_ADMITTED` | `$0.00 now` |
| Explicit retry/known fees | `R1 policy automatic retries=0; no live receipt` | `0 admitted` | `NOT_SET` | `NOT_SET` | `NOT_SET` | `$0.00 now` |
| Uncommitted safety reserve | Preserve existing R1 internal `$1.00` reserve; do not treat it as new authorization or available balance until the private ledger is checked under the live gate | — | — | — | — | `$0.00 incremental` |
| **Requested incremental ceiling** | | | | | | **`$0.00; not submitted`** |

Cost rule for any later request: `planned maximum attempts × conservative full-request reservation + known fees + explicit reserve`, with exact model/provider/pricing snapshot, tokenization assumptions, transfer bounds, cache/retry policy, and unknown-billing stop recorded before admission. Do not add unused caps or reset historical journals.

## 4. Precision/power and sample-size rationale

**Status: `POWER_NOT_ESTIMABLE`.** The current development evidence has one company group in each cohort, only two exact-patent groups in Abbott, one in Boston, no final holdout, unequal candidate universes, and a Boston `K=20` ceiling. The observed pair counts therefore cannot be treated as independent effective sample size, and no R1 paid paired variance exists.

Use independent company/patent-family groups as the primary unit, with devices and disclosed pairs nested inside groups. Before any confirmatory comparison, predeclare:

- a minimum meaningful quality delta and/or quality–cost margin;
- the primary endpoint and failure denominator;
- group-level paired variance or a cluster/bootstrap simulation method;
- sensitivity to unknown family mapping, group-size imbalance, and the `K` ceiling;
- a final holdout that remains untouched during method/policy selection.

Any normal paired approximation would be a screening calculation only, not a power guarantee for heterogeneous clusters. No exact sample-size or API amount is requested until a rights-cleared cohort and group structure exist.

## 5. Stopping, authorization and deliverables

- **Proposed data-expansion work package:** `HT-DATA-EXPANSION-20261029` (draft only). Preserve R1 authorization `PTP-HT-OR-R1-20261028-USD8`; do not mutate its historical policy or ledger.
- **Paid admission:** blocked until current model/provider identity, official pricing snapshot, approved credential/credit state, provider-transfer rights for every payload field, exact input/output/action bounds, and reconciliation gates are evidenced. If any gate fails, dispatch `0` paid calls and keep the reservation state fail-closed.
- **Early stop:** stop the paid branch on missing rights, missing pricing/identity, unknown billing, insufficient conservative headroom, schema/action/quality failures, no information gain over fixed controls, or a cohort/split change after freeze. Unused authorization remains unused; it is not rolled into a new cap.
- **Data rights:** use only public/licensed, non-sensitive, provider-transfer-permitted inputs with source IDs, revisions, hashes, jurisdiction, dates, exact locators, and policy IDs. No paid data purchase, top-up, new key, deployment, outreach, or public raw-data release is requested.
- **Deliverables if a later round is separately approved:** per-group paired results, cost and failure receipts including unknowns, latency/resource records, reproducible analysis/intervals, error cases, updated policy decision/report, and preserved R1 lineage. No positive finding or publication is guaranteed.
- **Offline work while pending:** rights/cohort audit, manifest and split design, HT-T2 prediction/denominator contract, evaluator/error checks, source-view/export verification, and manuscript limitations/figures using only existing permitted summaries.

Owner decision record: **PENDING / NO EXTRA SPEND AUTHORIZED**. Filling this document or labeling Option A “recommended” does not change authorization.
