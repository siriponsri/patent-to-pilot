# แฟ้มข้อมูลช่วงเวลาเข้าสู่ตลาดยาสามัญและเกณฑ์มาตรฐาน LOE-Bench สำหรับจัดลำดับการทบทวนหลักฐาน

# Market Window Dossier and LOE-Bench for Prioritizing Generic Drug Evidence Review

นายศิริพล ศรีเฮงไพบูลย์\*¹ และ ผศ.ดร.ทัศนัย พลอยสุวรรณ²\
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง\
เลขที่ 1 ซอยฉลองกรุง 1 แขวงลาดกระบัง เขตลาดกระบัง กรุงเทพฯ 10520

Mr. Siripon Srihangpiboon\*¹ and Asst. Prof. Dr. Tuchsanai Ploysuwan²\
School of Information Technology, King Mongkut's Institute of Technology Ladkrabang\
1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520

## บทคัดย่อ

หากทบทวนได้หนึ่งในห้าของชุดส่วนออกฤทธิ์ของยา (active-moiety set) ที่เข้าเกณฑ์ หลักฐานทางทะเบียนที่ระบุวันที่จะช่วยให้คิวครอบคลุมการอนุมัติยาสามัญขั้นสุดท้ายครั้งแรกของสำนักงานคณะกรรมการอาหารและยาสหรัฐฯ (FDA) ได้มากขึ้นหรือไม่ LOE-Bench วัดการครอบคลุม ส่วน Market Window Dossier กำหนดแฟ้มหลักฐานสำหรับผู้เชี่ยวชาญ

ในชุดพัฒนา ที่ระยะ 24 เดือน ผลต่าง M3 เทียบกับวิธีฐานตามอายุยา B1 และแบบจำลอง M1 ที่ไม่มีสถานะกราฟ เท่ากับ +9.80 [0.14, 19.65] และ +5.49 [−2.00, 11.25] จุดร้อยละ ต่ำกว่าเกณฑ์ประโยชน์เชิงปฏิบัติ +10 จุดร้อยละที่กำหนดไว้ล่วงหน้า ที่ระยะ 12 เดือน M3 สูงกว่า B1 +13.00 [3.27, 23.17] จุดร้อยละ และเท่ากับ M1 ที่ร้อยละ 61.11 วงเล็บเหลี่ยมแสดงช่วงความเชื่อมั่น 95%

ในชุดพัฒนา L1e (Qwen2.5-7B-Instruct) ครอบคลุมเหตุการณ์น้อยกว่า M3 ใน C2 ช่องหลักฐานและคำสั่งเปลี่ยนพร้อมกันจาก L1 เป็น L1e ตัวคูณ 0.465 เพิ่มความคลาดเคลื่อนเฉลี่ยสัมบูรณ์ในชุดย่อย Medicaid ที่จับคู่ได้ การตรวจรับและให้คะแนน C′ การตรึงคำพยากรณ์ Track A และการตรวจแฟ้มรายข้อความยังรออยู่ หลักฐานทางทะเบียนที่ระบุวันที่ควรได้รับการประเมินต่อ ส่วนประโยชน์ที่เพิ่มจากกราฟยังไม่แน่นอน [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [C2](../../../loe-bench/receipts/C2.md) · [C4b](../../../loe-bench/receipts/C4b.md) · [โพรโทคอล](../../../loe-bench/PREREGISTRATION.md)

**คำสำคัญ** ยาสามัญ, ช่วงเวลาเข้าสู่ตลาด, กราฟหลักฐาน, การจัดลำดับการทบทวน, เสรีภาพในการดำเนินการ

## Abstract

Given review capacity for one in five eligible active-moiety sets, can dated US regulatory evidence bring more impending first final generic approvals by the US Food and Drug Administration (FDA) into review? LOE-Bench measures event capture, and Market Window Dossier specifies the evidence packet for specialist follow-up.

On development data, the 24-month recall gains for M3 versus the age baseline B1 and versus M1, which omits graph states, were +9.80 [0.14, 19.65] and +5.49 [−2.00, 11.25] percentage points, respectively. Both point estimates fell below the prespecified +10-point practical-usefulness threshold. At 12 months, M3 exceeded B1 by +13.00 [3.27, 23.17] points and tied M1 at 61.11% recall. Brackets give 95% confidence intervals.

On development data, L1e (Qwen2.5-7B-Instruct) captured fewer events than M3. C2 changed evidence fields and prompt instructions together between L1 and L1e. Applying the 0.465 price factor increased mean absolute error on the mapped Medicaid subset. C′ admission and scoring, the prospective Track A prediction freeze and the dossier’s claim-level audit remain pending. Dated regulatory predictors warrant further evaluation. The graph’s incremental value remains uncertain. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [C2](../../../loe-bench/receipts/C2.md) · [C4b](../../../loe-bench/receipts/C4b.md) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

**Keywords** generic drugs, market window, evidence graph, review prioritization, freedom to operate

\* 68076060@kmitl.ac.th\
¹ นักศึกษาปริญญาโท สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ / Postgraduate Student, Artificial Intelligence for Business Analytics Program\
² ผู้ช่วยศาสตราจารย์ คณะเทคโนโลยีสารสนเทศ / Assistant Professor, School of Information Technology, KMITL

## 1. Introduction

Given review capacity for one in five eligible active-moiety sets, can dated US regulatory evidence bring more impending first final generic approvals into review? LOE-Bench measures event capture, and Market Window Dossier specifies the evidence packet for specialist follow-up. We specified a 20% review budget as a design assumption. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

Before investing in bioequivalence or comparative trials, generic and biosimilar developers must decide which products warrant closer review. Competitor entry may shrink the commercial window before a product is ready to launch. When a case goes to a freedom-to-operate (FTO) specialist, the developer also needs to identify the product, relevant patent claims and unresolved questions.

Market Window Dossier uses the proposed ingredient, formulation, jurisdiction, decision date and expected launch date to prepare a review priority, dated evidence, market scenarios and a verification checklist. Qualified specialists assess claim scope, legal status and applicability. LOE-Bench evaluates the US forecast. Thai and ASEAN sources inform the local hand-off.

Our earlier study asked whether instructions changed rankings within a fixed candidate pool. The authors’ prior report described near-zero instruction contrasts in that pool. The conference program for Paper 53 [1] verifies the title and authorship, and the original run records were unavailable for independent reanalysis. Here we ask what a reviewer can recover when dated evidence and review capacity are fixed.

- **RQ1 (confirmatory, specified in the preregistration protocol).** At a 20% review budget, does M3 capture more impending first generic approvals than B1 at 24 months (H1), more than M1 at 24 months (H2), and more than B1 at 12 months (H3)? The tests follow this order at one-sided α = 0.025.
- **RQ2 (exploratory).** Do the frozen queues identify drugs with at least three distinct approved generic applicants within 36 months? Does an FDA price-erosion factor improve forecasts of Medicaid reimbursement when applied to queued ingredients?
- **RQ3 (system and exploratory evaluation).** Can open records support a dossier whose material claims can be traced to source records? How does L1e, a language model given the same upstream evidence, compare with M3 on the same forecast rows?

## 2. Background and Related Work

### 2.1 Forecasting generic approval and regulatory timing

Hu et al. forecast first abbreviated new drug application (ANDA) submission for new chemical entities [2]. Hopefl et al. forecast first ANDA submission for orphan drug products using random survival forests [3]. LOE-Bench measures first final ANDA approval, a later regulatory milestone. These are external precedents without a measured head-to-head comparison. Beall et al. studied the onset of biosimilar and generic competition [4], and an FDA follow-up checked marketing among approved first generics [5]. Commercial launch requires separate evidence of marketing.

Hemphill and Sampat linked patent challenges and listings to effective market life [6]. Kannappan et al. compared stay expirations with generic entry timing [7]. These studies motivate using challenges alongside expiry dates. The Rai et al. replication dataset [8] supplies candidate court filings. Filing dates proxy historical availability for some matches, with actual availability uncertain.

### 2.2 Competition, price, and demand

Reiffen and Ward modelled entry and prices [9]. Conrad and Lutter linked producer counts to lower prices using FDA measures [10]. We count approved applicants as a regulatory signal. Active suppliers require separate evidence. Applying an average manufacturer price factor to Medicaid reimbursement tests transfer to a different measure. Following Nikolopoulos et al. [11], we use simple extrapolation comparators, carry-forward and drift.

### 2.3 Patent review and local evidence

The World Intellectual Property Organization (WIPO) guides patent landscaping [12] and FTO information searches [13]. A specialist hand-off needs the product, jurisdiction, claims and current status of the relevant records. Failed lookups leave open checklist items. Leela and Kessomboon describe Thai pharmaceutical patent examination [14]. The ASEAN IP Register supports regional discovery [15]. Historical coverage and Thai forecast accuracy require separate evaluation.

### 2.4 Dated evidence, model comparisons and review budgets

Paleka et al. document temporal leakage in historical language-model forecasts, including possible pretraining exposure [16]. The benchmark checks when each source edition became available as well as the dates it contains. ForecastBench motivates freezing predictions before outcomes resolve [17].

Selective prediction relates error to case coverage [18]. Here we measure event recall at a fixed review budget. Cluster resampling preserves within-drug dependence [19], and FDA guidance informs fixed-sequence testing [20]. Outcome-based reinforcement learning motivates the optional C9 forecast experiment [21]. A supervised adapter initialized from the same checkpoint supplies its direct comparator.

## 3. Methods

### 3.1 Dossier workflow and traceability

Figure 1 shows the proposed workflow from product intake to the evidence hand-off. The queue ranks active-moiety sets. The dossier records the formulation and jurisdiction so specialists can judge whether the ingredient-level evidence applies to the product. Demand and price outputs are scenarios, and missing or inconsistent records become checklist items for review.

![Market Window Dossier workflow](../../../assets/market-window-flow.svg)

*Figure 1. Proposed dossier workflow for specialist review. Historical development evaluation is complete. Sealed C′ admission and scoring, the Track A prediction freeze and the dossier’s claim-level audit are pending. Demand and price are scenario outputs.*

Each material claim carries a source identifier, version, content hash, exact locator and availability basis in the proposed design. The dossier labels observations, estimates and scenario assumptions, and sends unknowns for manual verification. The audit checks source integrity and whether the cited passage supports the claim.

The Thai inventory covers domestic patent, drug, reference-price and procurement records. ASEAN records supply family and status leads for national verification. [Thai source inventory](../../../loe-bench/THAI-OPEN-DATA.md) · [Dossier specification](../../../loe-bench/PLAN.md)

### 3.2 As-of cohort and outcome

LOE-Bench treats each active-moiety set at an annual cutoff as an observation. A drug qualifies if it has a usable ingredient key, an original final new drug application (NDA) approval dated by the cutoff and an original final NDA record with the exact classification TYPE 1 by that date. It must have no dated first final ANDA on or before the cutoff. The endpoint is the first dated original final ANDA approval (ORIG/AP) after the cutoff and through the horizon end, inclusive. Tentative approvals, authorized generics under NDAs and supplements as first approvals are excluded. Every row requires complete follow-up even when an approval has already occurred. Repeated rows for the same active-moiety set remain in one drug cluster.

Drugs@FDA supplies approvals and dated administrative records. The Global Substance Registration System (GSRS) supports identity resolution. The frozen linkage uses substance identifiers and aliases, with flagged normalized-name fallback when needed. A record without a usable date or link cannot establish an eligible event. Missing predictors on eligible rows are retained. For patent, exclusivity and product breadth, C′ requires the newest eligible historical Orange Book ZIP whose content date falls within the inclusive prior six calendar months, with independent evidence of availability by the cutoff and a matching file hash. Eligible editions can report future expiry dates. Later products and patent submissions are filtered out.

Challenge evidence uses fresh, availability-proven FDA Paragraph IV editions and qualifying court witnesses. A matched undated submission without another timely witness is unknown. A timely court witness can establish an observed challenge. Verified non-observation in a fresh list is an operational negative. If no qualifying edition or positive witness is available, the challenge state is unknown. For expanded court matches, the filing date is an availability proxy and the patent association may be incompletely verified. Later dispositions, approvals and marketing fields are excluded from the predictors. Table 1 gives the cutoff schedules. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

*Table 1. Annual cutoff schedule by horizon.*

| Horizon | Training cutoff year | Development validation years | Sealed C′ cutoff years |
| --- | ---: | --- | --- |
| 12 months | 2010 | 2012–2015 | 2017–2025 |
| 24 months | 2010 | 2013–2014 | 2017–2024 |

Cutoffs are on 1 January. The training label availability boundary is the day before development validation starts. The preceding outcome window must end before the next partition begins. The observation end is 27 November 2026 for the scheduled C′ windows. An earlier 36-month evaluation exposed aggregate B0–B2 results on drug histories and periods overlapping C′. The protocol also documents inventory and preflight access. C′ scoring remains pending. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

### 3.3 Models, queues and inference

B1 assigns a smoothed approval hazard using age since first NDA approval, with a prevalence fallback for an unseen age bin. M1 uses standardized L2 logistic regression with age, NDA and regulatory indicators, product breadth, patent and exclusivity information, challenge observations, missingness flags and the B1 logit. M3 uses the same inputs and model family and adds indicators for the graph state: OPEN, BLOCKED or CONTESTED. The graph evaluates whether all recorded exclusivities expire by the horizon and whether all recorded patents expire by then or a challenge has been observed. Under Kleene three-valued logic each input can be true, false or unknown. An empty set of expiry dates leaves the corresponding condition unknown. The graph states summarize evidence for predicting an FDA event and have no legal effect.

For each cutoff and horizon, the benchmark ranks all eligible cases by unrounded native risk, prior to calibration or graph policy actions. The review queue takes the integer part of one fifth of the roster. If a tie crosses the boundary, each tied case receives equal fractional credit for the remaining slots. Recall pools the expected captured event rows across cutoffs and divides by all qualifying event rows. Precision divides the expected hits by the slots. Distinct event-drug capture counts a drug's probability of being captured at least once on an event row. A first approval can qualify in overlapping windows, so the pooled and distinct measures answer different questions.

Inference uses 2,000 paired whole-drug bootstrap draws per horizon. Fitted models stay fixed, and each draw recomputes queue sizes and ties with shared drug-cluster multiplicities. A reached step passes if its one-sided lower bound at the linear empirical α quantile exceeds zero. A failed or unevaluable step stops the sequence. Report all estimable contrasts with two-sided 95% percentile intervals and mark unreached steps descriptive. Any undefined draw makes the interval unevaluable. Report whether each point estimate reaches the prespecified +10 percentage-point practical-usefulness threshold alongside the superiority decision. In T4c, simulated H1 power at +10 points with 75 event drugs was 49.96%. The blinded gate’s minimum of 50 event drugs defines admission, and adequate power needs separate assessment. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [T4c](../../../loe-bench/receipts/T4c.md) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

### 3.4 Registration, blinded admission and prospective follow-up

The Open Science Framework (OSF) registration record is pending [OSF DOI PENDING]. The sealed release is designed to require the first author's authorization, the hash of the OSF-issued registered PDF, the pinned code and source identities and a PASS from the blinded gate. The gate first verifies the required edition coverage for every scheduled cutoff. It then checks whether at least 50 distinct eligible event drugs meet the 24-month rule. It releases a verdict while withholding counts and outcomes. Only a technical failure permits one documented retry on identical pinned inputs. A final gate failure yields feasibility evidence only and leaves H1–H3 untested on C′. The sequence runs from completed development through pending OSF registration and blinded C′ admission to authorized scoring if admitted, with a separately scheduled Track A freeze and readouts at maturity.

Track A follows its own schedule and retrains the core fitted arms using the same recipe on eligible windows matured by the prospective origin of 27 November 2026. The core includes B1, M1, M3 and the descriptive expiry-only comparator B3. Eligible exploratory arms may be included under their own admission rules. The roster, sources, models, code, policies and predictions must be hashed, tagged in Git and externally timestamped in OSF before 31 January 2027 at 23:59 UTC and before any post-origin outcome fetch. If that condition fails, subsequent analyses are exploratory. The prospective windows mature on 27 November 2027 and 27 November 2028, respectively. Track A is confirmatory if C′ did not run as a confirmatory analysis, and a replication otherwise. Formal H3 still depends on both preceding steps. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

### 3.5 Exploratory analyses

For crowding, the frozen 24-month queues are evaluated at the mature 2013 cutoff against the longer 36-month outcome. The outcome requires at least three distinct legal applicants with final original ANDA approvals. Strengths and repeat approvals are collapsed, and applicant identity uses the first eligible historical Orange Book listing through 12 months after approval, with documented overrides. The current sponsor name supplies a sensitivity analysis. An unresolved applicant remains unknown. Queue membership and tie weights come from the original roster.

For Medicaid, the analysis forecasts next-year prescription counts and annual gross reimbursement, with a separate fourth-quarter reimbursement-per-prescription endpoint. It uses the mapped subset of national State Drug Utilization Data from the Centers for Medicare & Medicaid Services. Carry-forward is the primary baseline and drift is secondary. On exact cutoff and identity matches, the adjusted arms use the frozen 12-month queues and a shared deterministic boundary order. Each queued ingredient's carry-forward reimbursement forecast is multiplied by 0.465, the FDA median generic-to-brand average manufacturer price ratio under a two-producer scenario. Unqueued ingredients retain carry-forward. No historical Medicaid release vintage was verified for the evaluated origins, and the FDA factor was published after those origins. The analysis is retrospective and vintage-uncontrolled. C5 uses the FDA ratios in a separate, assumption-based price scenario with a stated marketed-producer count and price basis. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md) [Crowding receipt](../../../loe-bench/receipts/C3b.md) · [Reimbursement receipt](../../../loe-bench/receipts/C4b.md)

L1 and L1e use the same pinned Qwen2.5-7B-Instruct checkpoint and decoder. L1 receives ingredient identity, cutoff and horizon. L1e also receives the dated upstream evidence used by M3, including graph input clocks and challenge witnesses. It does not receive fitted risks, B1 hazard, graph verdicts, actions or outcomes. The prompt change includes instructions for using the new fields. The contrast evaluates the combined change in evidence presentation and instructions. The optional prospective C9 comparison pairs group relative policy optimization (GRPO) with supervised fine-tuning (SFT) on common inputs at 24 months, subject to a completed pair before the core freeze. [L1](../../../loe-bench/receipts/L1DEV.md) · [L1e](../../../loe-bench/receipts/C2.md) · [C9](../../../loe-bench/receipts/C9.md)

## 4. Results

### 4.1 RQ1: First-approval review queues

The frozen first-approval results are development-only. The 24-month panel had 1,083 rows, 91 event rows from 67 event drugs, and 215 slots. The 12-month panel had 2,161 rows, 90 event rows from 90 event drugs, and 430 slots. Figure 2 shows the paired recall differences with two-sided 95% intervals. All resampling draws were defined. [FREEZE](../../../loe-bench/receipts/FREEZE.md)

> [FIGURE PLACEMENT: development paired-effect plot]

*Figure 2. Paired differences in first-approval recall at the 20% review budget on development data. Points are estimates, bars are two-sided 95% whole-drug bootstrap intervals, and vertical lines mark zero and +10 percentage points. Labels give the number of distinct event drugs.*

At 24 months, B1, M1 and M3 recalled 39.65%, 43.96% and 49.45%, respectively. M3 gained +9.80 [0.14, 19.65] percentage points over B1 and +5.49 [−2.00, 11.25] over M1. Both estimates fell below the prespecified +10-point practical-usefulness threshold. At 12 months, the +13.00 [3.27, 23.17] point gain over B1 (48.11% recall) exceeded the threshold on the point estimate. M1 matched M3’s 61.11% recall. H2’s interval includes zero, and undated challenge coding on the training set affected the estimate. The development auto-clear diagnostic failed for every estimable arm and horizon, so cases outside the queue remain in routine review. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

- [RESULT PENDING: blinded C′ admission verdict and disposition]
- [RESULT PENDING: C′ H1–H3 estimable contrasts with two-sided 95% intervals, practical-usefulness checks, reached-step decisions and descriptive labels for unreached steps]
- [RESULT PENDING: Track A timestamped prediction freeze and outcome readouts]

RQ1 remains unanswered on confirmatory evidence. If admission fails, the C′ entries will record feasibility and the hypotheses will remain untested on that track.

### 4.2 RQ2: Applicant crowding and Medicaid reimbursement

At the single mature 2013 development cutoff, M3 captured 15.000 expected events (71.43%) and B1 captured 9.625 (45.83%) out of 21, with 107 slots per arm across 539 rows. Fractional credit for boundary ties explains the non-integer counts. The difference of +25.60 percentage points (paired 95% CI [6.25, 45.00]) describes only this cutoff and the endpoint of at least three distinct applicants receiving final approvals within 36 months. The current-sponsor sensitivity gave the same result. [C3b](../../../loe-bench/receipts/C3b.md)

Applying the 0.465 factor increased mean absolute error (MAE) on both reimbursement endpoints in the retrospectively mapped Medicaid subset, relative to unadjusted carry-forward. Table 2 reports paired ingredient-cluster percentile intervals. The linked analyses cover four origins. They use 160 ingredient-origin pairs from 68 ingredients for reimbursement per prescription and 150 pairs from 64 ingredients for annual reimbursement.

*Table 2. Paired reimbursement MAE differences relative to carry-forward on the linked development subset.*

| Comparison with carry-forward | Fourth-quarter USD per prescription [95% CI] | Annual USD millions [95% CI] |
| --- | ---: | ---: |
| B1-adjusted | +372.05 [193.27, 587.26] | +4.98 [2.24, 8.29] |
| M3-adjusted | +381.24 [203.61, 606.77] | +21.43 [4.07, 53.21] |
| Drift minus carry-forward | −172.13 [−292.12, −66.37] | −3.69 [−8.41, −0.20] |

On the same queue-linked subset, drift reduced MAE for both reimbursement endpoints. Gross reimbursement per prescription rose for queued ingredients in the observed subset, and shrinking the carried-forward forecast worsened underprediction. These descriptive contrasts have no multiplicity adjustment. Payment totals are gross and pre-rebate, include amounts in the source's Medicaid and non-Medicaid fields, and reflect mapped packages only. National full-ingredient totals could not be estimated. In answer to RQ2, the development queue comparison supports investigating applicant crowding, while the reimbursement comparison does not support using the FDA factor as a Medicaid forecast adjustment. [C4b](../../../loe-bench/receipts/C4b.md)

### 4.3 RQ3: Source trace and evidence-matched language model

The Thai source inventory supports partial demonstrations. The dossier routes unresolved fields to the specialist checklist. [RESULT PENDING: dossier claim-level traceability audit]

The exploratory L1e run completed the full matched development roster. Table 3 reports the C2 comparisons. Grouped average precision (AP) treats equal scores as a group. The 12- and 24-month panels have the event counts reported in Section 4.1. Differences use paired whole-drug bootstrap intervals without multiplicity adjustment. The recall gap was negative relative to both L1 and M3 at each horizon.

*Table 3. Evidence-matched language model and comparator results on development data.*

| Months | Arm | Recall at 20% | Queue precision | Grouped AP |
| ---: | --- | ---: | ---: | ---: |
| 12 | L1e | 24.24% | 5.07% | 0.05260 |
| 12 | L1 | 34.92% | 7.31% | 0.06181 |
| 12 | M3 | 61.11% | 12.79% | 0.18860 |
| 12 | B1 | 48.11% | 10.07% | 0.09189 |
| 24 | L1e | 19.08% | 8.08% | 0.10141 |
| 24 | L1 | 28.59% | 12.10% | 0.11646 |
| 24 | M3 | 49.45% | 20.93% | 0.22189 |
| 24 | B1 | 39.65% | 16.78% | 0.17288 |

Against M3, L1e recall was lower by 36.87 percentage points at 12 months (L1e − M3, 95% CI [−47.40, −23.92]) and 30.37 at 24 months [−43.08, −16.44]. Against L1, the differences were −10.68 [−17.96, −3.63] and −9.51 [−16.26, −2.43], respectively. The contrast combines differences in training and evidence encoding. It applies to the tested implementations. [C2](../../../loe-bench/receipts/C2.md)

The optional prospective C9 comparison uses Qwen2.5-1.5B-Instruct for GRPO and SFT. Training and outcomes are NOT_RUN. [C9](../../../loe-bench/receipts/C9.md)

## 5. Conclusion

Dated regulatory predictors warrant further evaluation. The graph’s incremental value remains uncertain. The single-cutoff crowding result motivates follow-up on approved applicants, and the mapped Medicaid results support keeping the price factor as a scenario assumption. The C2 gap applies to the tested language-model implementation. Market Window Dossier specifies how to trace claims and route unresolved items for specialist review. The claim-level audit is pending. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [C3b](../../../loe-bench/receipts/C3b.md) · [C4b](../../../loe-bench/receipts/C4b.md) · [C2](../../../loe-bench/receipts/C2.md)

Several limits affect interpretation. The US cohort is restricted to eligible new molecular entity histories and the endpoint is final regulatory approval. Historical editions can miss prior changes, the identity crosswalk partly relies on later records, and some challenge witnesses have uncertain historical availability. A small number of independent event drugs limits power even when the gate admits the analysis. The crowding check covers one cutoff. The reimbursement analysis uses retrospectively mapped packages without verified historical release vintages. The language-model comparison is limited to a single checkpoint and prompting configuration and leaves pretraining exposure unresolved.

Future work should complete the blinded admission and timestamp the Track A predictions before outcome access, then score each matured window under the fixed protocol. The dossier needs a claim-by-claim audit of the evidence actually shown, with Thai and ASEAN gaps logged for local verification. Future studies should use marketing records for commercial launch, Thai procurement and utilization records for Thai demand, and the completed workflow for reviewer time savings. Product-specific FTO conclusions require a qualified assessment of claims and legal status for the actual formulation and jurisdiction.

## References

[1] S. Srihangpiboon and T. Ploysuwan, “Diagnosing near-zero instruction effects in cross-domain patent reranking,” iSAI-NLP conference program, paper 53, 2026. [Program](https://isai-nlp2026.aiat.or.th/program).

[2] M. Hu et al., “Predictive analysis of first abbreviated new drug application submission for new chemical entities based on machine learning methodology,” *Clin. Pharmacol. Ther.*, vol. 106, no. 1, pp. 174–181, 2019. [doi: 10.1002/cpt.1479](https://doi.org/10.1002/cpt.1479).

[3] R. Hopefl et al., “Predictive analysis for first submission of generic drug application for orphan drug products using random survival forest,” *Clin. Transl. Sci.*, vol. 18, no. 10, e70365, 2025. [doi: 10.1111/cts.70365](https://doi.org/10.1111/cts.70365).

[4] R. F. Beall et al., “Comparing onset of biosimilar versus generic competition in the United States,” *Clin. Pharmacol. Ther.*, vol. 108, no. 6, pp. 1308–1314, 2020. [doi: 10.1002/cpt.1981](https://doi.org/10.1002/cpt.1981).

[5] H. S. Chahal, R. Patel, and M. Shimer, “Marketing of first generic drugs approved by U.S. FDA from January 2010 to June 2017,” US FDA, 2021. [Report](https://www.fda.gov/media/154101/download?attachment=).

[6] C. S. Hemphill and B. N. Sampat, “Evergreening, patent challenges, and effective market life in pharmaceuticals,” *J. Health Econ.*, vol. 31, no. 2, pp. 327–339, 2012. [Article](https://www.sciencedirect.com/science/article/abs/pii/S0167629612000057).

[7] S. Kannappan, J. J. Darrow, A. S. Kesselheim, and R. F. Beall, “The timing of 30-month stay expirations and generic entry: A cohort study of first generics, 2013–2020,” *Clin. Transl. Sci.*, vol. 14, no. 5, pp. 1917–1923, 2021. [doi: 10.1111/cts.13046](https://doi.org/10.1111/cts.13046).

[8] A. K. Rai, S. Vishnubhakat, J. Lemus, and E. Hovenkamp, “Replication data for: Post-grant adjudication of drug patents: Agency and/or court?,” Harvard Dataverse, ver. 1.0, 2021. [doi: 10.7910/DVN/YCMKVU](https://doi.org/10.7910/DVN/YCMKVU).

[9] D. Reiffen and M. R. Ward, “Generic drug industry dynamics,” *Rev. Econ. Stat.*, vol. 87, no. 1, pp. 37–49, 2005. [doi: 10.1162/0034653053327694](https://doi.org/10.1162/0034653053327694).

[10] R. Conrad and R. Lutter, “Generic competition and drug prices: New evidence linking greater generic competition and lower generic drug prices,” US FDA, 2019. [Report](https://www.fda.gov/media/133509/download).

[11] K. Nikolopoulos, S. Buxton, M. Khammash, and P. Stern, “Forecasting branded and generic pharmaceuticals,” *Int. J. Forecast.*, vol. 32, no. 2, pp. 344–357, 2016. [doi: 10.1016/j.ijforecast.2015.08.001](https://doi.org/10.1016/j.ijforecast.2015.08.001).

[12] World Intellectual Property Organization, *Guidelines for Preparing Patent Landscape Reports*, WIPO Publ. 946, 2015. [Guide](https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf).

[13] World Intellectual Property Organization, *Identifying Inventions in the Public Domain: A Guide for Inventors and Entrepreneurs*, WIPO Publ. 1062, 2020. [Guide](https://www.wipo.int/publications/en/details.jsp?id=4501).

[14] P. Leela and N. Kessomboon, “Challenges of examination processes of pharmaceutical patent application in Thailand,” *Isan J. Pharm. Sci.*, vol. 11, suppl., 2016. [Article](https://he01.tci-thaijo.org/index.php/IJPS/article/view/48601).

[15] ASEAN Intellectual Property Portal, “ASEAN IP Register.” [Register](https://ip-register.aseanip.org/).

[16] D. Paleka, S. Goel, J. Geiping, and F. Tramèr, “Pitfalls in evaluating language model forecasters,” in *Proc. ICLR*, 2026. [Conference paper](https://openreview.net/forum?id=z85kARAoyD).

[17] E. Karger et al., “ForecastBench: A dynamic benchmark of AI forecasting capabilities,” in *Proc. ICLR*, 2025. [Paper](https://arxiv.org/abs/2409.19839).

[18] J. Traub et al., “Overcoming common flaws in the evaluation of selective classification systems,” in *Adv. Neural Inf. Process. Syst.*, 2024. [Paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf).

[19] C. A. Field and A. H. Welsh, “Bootstrapping clustered data,” *J. R. Stat. Soc. B*, vol. 69, no. 3, pp. 369–390, 2007. [doi: 10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x).

[20] US FDA, *Multiple Endpoints in Clinical Trials: Guidance for Industry*, 2022. [Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials).

[21] B. Turtel, D. Franklin, K. Skotheim, L. Hewitt, and P. Schoenegger, “Outcome-based reinforcement learning to predict the future,” *Trans. Mach. Learn. Res.*, Nov. 2025. [Journal article](https://openreview.net/forum?id=bbhdeL8EUX).
