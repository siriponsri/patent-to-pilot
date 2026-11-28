# แฟ้มข้อมูลช่วงเวลาเข้าสู่ตลาดยาสามัญและเกณฑ์มาตรฐาน LOE-Bench สำหรับจัดลำดับการทบทวนหลักฐาน

# Market Window Dossier and LOE-Bench for Prioritizing Generic Drug Evidence Review

นายศิริพล ศรีเฮงไพบูลย์\*¹ และ ผศ.ดร.ทัศนัย พลอยสุวรรณ²\
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง\
เลขที่ 1 ซอยฉลองกรุง 1 แขวงลาดกระบัง เขตลาดกระบัง กรุงเทพฯ 10520

Mr. Siripon Srihangpiboon\*¹ and Asst. Prof. Dr. Tuchsanai Ploysuwan²\
School of Information Technology, King Mongkut's Institute of Technology Ladkrabang\
1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520

## บทคัดย่อ

ผู้พัฒนายาสามัญและยาชีววัตถุคล้ายคลึงต้องเลือกว่าจะส่งผลิตภัณฑ์ใดให้ผู้ประเมินเสรีภาพในการดำเนินการ (freedom to operate: FTO) ซึ่งมีจำนวนจำกัดตรวจก่อน โดยมักต้องตัดสินใจหลายปีก่อนวางตลาดและยังไม่รู้ว่าตลาดจะมีคู่แข่งมากเพียงใด งานวิจัยนี้ศึกษาว่าหลักฐานทางทะเบียนของสหรัฐฯ ที่ระบุวันที่ช่วยให้คิวทบทวนซึ่งรับได้หนึ่งในห้าของยาที่เข้าเกณฑ์ครอบคลุมยาที่กำลังจะได้รับอนุมัติยาสามัญครั้งแรกได้มากขึ้นหรือไม่ LOE-Bench เป็นชุดทดสอบมาตรฐานแบบเปิดที่สร้างจาก Orange Book, Drugs@FDA, รายการ Paragraph IV และข้อมูลคดีที่พิสูจน์ได้ว่าเผยแพร่แล้ว ณ วันตัดข้อมูลแต่ละปี ชุดทดสอบถูกปิดผนึกด้วยโค้ดจนกว่าจะลงทะเบียนแผนการวิเคราะห์ล่วงหน้า และคำพยากรณ์ล่วงหน้าจะถูกประทับเวลาก่อนทราบผล ส่วน Market Window Dossier แปลงคำพยากรณ์เป็นแฟ้มหลักฐานที่ตรวจย้อนแหล่งได้สำหรับผู้ประเมิน FTO และทีมวิจัยพัฒนาและพัฒนาธุรกิจ ในชุดพัฒนา แบบจำลองกราฟหลักฐาน (M3) ครอบคลุมการอนุมัติยาสามัญขั้นสุดท้ายครั้งแรกมากกว่าวิธีฐานตามอายุยา 9.80 จุดร้อยละที่ 24 เดือน (ช่วงความเชื่อมั่น 95% 0.14 ถึง 19.65) และ 13.00 จุดร้อยละที่ 12 เดือน (3.27 ถึง 23.17) ส่วนผลต่างเทียบกับแบบจำลองที่ไม่มีสถานะกราฟ 5.49 จุดร้อยละ (−2.00 ถึง 11.25) ยังไม่แน่นอน และผลต่างที่ 24 เดือนทั้งสองค่าต่ำกว่าเกณฑ์ประโยชน์ +10 จุดร้อยละที่กำหนดไว้ล่วงหน้า ในการวิเคราะห์เชิงสำรวจ คิวเดียวกันครอบคลุมยาที่มีผู้ยื่นคำขอยาสามัญได้รับอนุมัติอย่างน้อยสามรายภายใน 36 เดือนร้อยละ 71.43 เทียบกับ 45.83 ณ วันตัดข้อมูลหนึ่งปี และแบบจำลองภาษาขนาด 7B ที่ได้รับหลักฐานชุดเดียวกันครอบคลุมเหตุการณ์น้อยกว่า M3 ผลยืนยันบนชุดทดสอบที่ปิดผนึกและคำพยากรณ์ล่วงหน้ายังรอดำเนินการ

**คำสำคัญ** ยาสามัญ, ช่วงเวลาเข้าสู่ตลาด, กราฟหลักฐาน, การจัดลำดับการทบทวน, เสรีภาพในการดำเนินการ

## Abstract

Generic and biosimilar developers must choose which products to send for scarce freedom-to-operate (FTO) review, often years before launch and without knowing how crowded the market will be. We ask whether dated US regulatory evidence can bring more impending first generic approvals into a review queue limited to one in five eligible drugs. LOE-Bench is an open benchmark built from Orange Book editions, Drugs@FDA records, Paragraph IV lists and court records that were demonstrably public at each annual cutoff; its test set is sealed in code until a preregistered protocol is filed, and prospective forecasts are timestamped before outcomes exist. Market Window Dossier turns the forecasts into a traceable evidence packet for FTO specialists and R&D and business-development teams. On development data, an evidence-graph model (M3) captured 9.80 percentage points more first final approvals than an age baseline at 24 months (95% CI 0.14 to 19.65) and 13.00 points more at 12 months (3.27 to 23.17); its gain over a matched model without graph states, 5.49 points (−2.00 to 11.25), was uncertain, and both 24-month gains fell below the prespecified +10-point usefulness threshold. In exploratory analyses, the same queues captured 71.43% versus 45.83% of drugs that drew at least three approved generic applicants within 36 months at one cutoff, and a 7B language model given the same evidence captured fewer events than M3. Confirmatory results on the sealed test and the prospective forecasts are pending. Dated regulatory evidence warrants further evaluation for review prioritization; the graph's added value remains to be confirmed.

**Keywords** generic drugs, market window, evidence graph, review prioritization, freedom to operate

\* 68076060@kmitl.ac.th\
¹ นักศึกษาปริญญาโท สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ / Postgraduate Student, Artificial Intelligence for Business Analytics Program\
² ผู้ช่วยศาสตราจารย์ คณะเทคโนโลยีสารสนเทศ / Assistant Professor, School of Information Technology, KMITL

## 1. Introduction

Given review capacity for one in five eligible active-moiety sets, can dated US regulatory evidence bring more impending first final generic approvals into review? LOE-Bench measures event capture, and Market Window Dossier specifies the evidence packet for specialist follow-up. We specified a 20% review budget as a design assumption.

Before investing in bioequivalence or comparative trials, generic and biosimilar developers must decide which products warrant closer review. Competitor entry may shrink the commercial window before a product is ready to launch. When a case goes to a freedom-to-operate (FTO) specialist, the developer also needs to identify the product, relevant patent claims and unresolved questions.

Market Window Dossier uses the proposed ingredient, formulation, jurisdiction, decision date and expected launch date to prepare a review priority, dated evidence, market scenarios and a verification checklist. Qualified specialists assess claim scope, legal status and applicability. LOE-Bench evaluates the US forecast. Thai and ASEAN sources inform the local hand-off.

Competition shapes the commercial window: in FDA data, the median generic price fell to 46% of the pre-entry brand price with two marketed producers and to 21% with four [1]. Our earlier study asked whether instruction wording changed rankings within a fixed candidate pool and found near-zero effects [2]. Here we ask what a reviewer can recover when the dated evidence and the review capacity are fixed instead.

This paper makes three contributions. First, LOE-Bench is an as-of benchmark of US first generic approvals built only from open records, with a code-enforced test seal, a preregistered analysis plan and a prospective forecast freeze. Second, it evaluates an evidence-graph review queue at a fixed review capacity against an age baseline and a matched model without graph states. Third, Market Window Dossier links the launch-window forecast to a claim-traceable FTO hand-off designed for Thai and ASEAN developers.

The authors’ earlier conference paper on cross-domain patent reranking is listed as Paper 53 in the iSAI-NLP 2026 program [2].

- **RQ1 (confirmatory, specified in the preregistration protocol).** Using each model’s native scores before deferral, does M3 achieve higher recall of first final original abbreviated new drug application (ANDA) approvals at the 20% review budget? The ordered contrasts are M3 versus B1 at 24 months (H1), M3 versus M1 at 24 months (H2), and M3 versus B1 at 12 months (H3), tested at one-sided α = 0.025.
- **RQ2 (exploratory).** Do the frozen queues identify drugs with at least three distinct approved generic applicants within 36 months? Does an FDA price-erosion factor improve forecasts of Medicaid reimbursement when applied to queued ingredients?
- **RQ3 (system and exploratory evaluation).** Can open records support a dossier whose material claims can be traced to source records? How does L1e, a language model given the same upstream evidence, compare with M3 on the same forecast rows?

## 2. Background and Related Work

### 2.1 Endpoints and dated regulatory evidence

Patent expiry, submission, approval and commercial launch mark distinct points in generic entry. Beall et al. used patent records to approximate entry and found that the approach overstated the observed median time to entry for drugs protected only by secondary patents [3]. In a comparison of biosimilars and generics, they defined expected entry using the later of key patent expiry and statutory exclusivity [4]. Kerr and Glos modelled the interval from new molecular entity approval to first generic approval [5].

Hu et al. and Hopefl et al. forecast first submission of an ANDA for new chemical entities and orphan drug products, respectively [6], [7]. LOE-Bench measures the first final approval of an original ANDA. FDA tracked actual marketing for 687 first generics approved from January 2010 to June 2017. Of these, 118 (17%) had yet to reach the market within the study period. Among the 375 Paragraph IV first generics, 53% reached the market within six months of approval and about 69% within two years [8]. These studies provide external context for LOE-Bench and measure outcomes in their own cohorts.

Hemphill and Sampat related challenges to expiry timing and used patent type as a proxy for quality [9]. Kannappan et al. compared the end of the 30-month stay with launch timing [10]. The digitized Orange Book makes historical listings reconstructable [11]. Establishing when a particular edition was publicly available requires separate evidence. The Rai et al. dataset provides candidate court records [12], whose filing dates may serve as availability proxies.

### 2.2 Applicants, marketed producers and price scenarios

Scott Morton studied firms’ generic entry decisions empirically [13]. Reiffen and Ward modelled the relationship between entry and prices [14]. Hollis studied the first entrant’s relative share of generic units sold in Canada [15]. The number of approved applicants measures potential competition. Counting marketed producers or units sold requires commercial data.

Conrad and Lutter reported median US ratios of generic to brand average manufacturer price (AMP) by marketed-producer count around initial generic entry [1]. AMP incorporates some price concessions and omits rebates to health plans and pharmacy benefit managers. The ratios inform price scenarios. Medicaid reimbursement uses a different payment measure, so applying the AMP ratio to a reimbursement forecast tests transfer between those measures. Carry-forward and drift are transparent baselines for testing reimbursement forecasts, with drift motivated by prior research on pharmaceutical dispensing forecasts [16].

### 2.3 Evidence hand-off and Thai applicability

In WIPO’s landscape guidelines, Trippe illustrates a scope of work that leaves validity and freedom to operate (FTO) outside the commissioned landscape [17]. WIPO’s public-domain guide describes searches and analysis of published patent records for FTO review [18]. PatentAgentBench includes FTO search and design tasks and offers a comparator for task design [19]. The dossier supports specialist review by linking product details, claims and legal-status records and sending unresolved items to a qualified reviewer.

Leela and Kessomboon interviewed 19 purposively selected key informants about Thai pharmaceutical patent examination [20]. Vachanavuttivong et al. reported an average of about 7.5 years from filing to grant for Thai patent applications generally and a range of 4–13 years from request for substantive examination to grant for pharmaceutical patent applications [21]. These sources inform the Thai review checklist. Regional records can supply leads, with claim scope and legal status checked against national records. Forecasting Thai launch dates, utilization or prices requires local drug-level records and separate validation.

### 2.4 Evaluation and research gap

Retrospective language-model forecasts risk exposure to later information through the training corpus or supplied evidence [22]. Chronologically consistent models in finance illustrate a training-time control [23]. ForecastBench provides a prospective comparator by collecting forecasts before outcomes resolve [24]. LOE-Bench checks source availability at each cutoff and plans to timestamp prospective predictions before outcome access. Preregistration of secondary data analysis documents decisions before scoring [25].

Selective classification studies evaluate risk as coverage changes [26]. LOE-Bench uses recall at 20% from each model’s native scores before deferral. A paired bootstrap resamples whole drug histories to preserve dependence across cutoffs [27]. The ordered tests borrow the fixed-sequence principle from FDA clinical-trial guidance [28]. Outcome-based reinforcement learning motivates the optional prospective comparison of reinforcement learning and supervised fine-tuning [29].

At the same review capacity, does adding graph state to a matched model that uses only evidence available at the cutoff capture more impending first final approvals? RQ2 examines counts of distinct approved applicants within 36 months, with development evidence from one cutoff so far. RQ3 asks whether each material dossier claim can be traced to dated evidence.

## 3. Methods

### 3.1 Dossier workflow and traceability

Figure 1 shows the proposed workflow from product intake to the evidence hand-off. The queue ranks active-moiety sets. The dossier records the formulation and jurisdiction so specialists can judge whether the ingredient-level evidence applies to the product. Demand and price outputs are scenarios, and missing or inconsistent records become checklist items for review.

![Market Window Dossier workflow](../../../assets/market-window-flow.svg)

*Figure 1. Proposed dossier workflow for specialist review. Historical development evaluation is complete. Admission and scoring for C′ (the sealed historical test), the prediction freeze for Track A (prospective forecasts) and the dossier’s claim-level audit are pending. Demand and price are scenario outputs.*

Each material claim carries a source identifier, version, content hash, exact locator and availability basis in the proposed design. The dossier labels observations, estimates and scenario assumptions, and sends unknowns for manual verification. The audit checks source integrity and whether the cited passage supports the claim.

The Thai inventory covers domestic patent, drug, reference-price and procurement records. ASEAN records supply family and status leads for national verification.

### 3.2 As-of cohort and outcome

LOE-Bench treats each active-moiety set at an annual cutoff as an observation. A drug qualifies if it has a usable ingredient key, an original final new drug application (NDA) approval dated by the cutoff and an original final NDA record with the exact classification TYPE 1 by that date. It must have no dated first final ANDA on or before the cutoff. The endpoint is the first dated original final ANDA approval (ORIG/AP) after the cutoff and through the horizon end, inclusive. Tentative approvals, authorized generics under NDAs and supplements as first approvals are excluded. Every row requires complete follow-up even when an approval has already occurred. Repeated rows for the same active-moiety set remain in one drug cluster.

Drugs@FDA supplies approvals and dated administrative records. The Global Substance Registration System (GSRS) supports identity resolution. The frozen linkage uses substance identifiers and aliases, with flagged normalized-name fallback when needed. A record without a usable date or link cannot establish an eligible event. Missing predictors on eligible rows are retained. For patent, exclusivity and product breadth, C′ requires the newest eligible historical Orange Book ZIP whose content date falls within the inclusive prior six calendar months, with independent evidence of availability by the cutoff and a matching file hash. Eligible editions can report future expiry dates. Later products and patent submissions are filtered out.

Challenge evidence uses fresh, availability-proven FDA Paragraph IV editions and qualifying court witnesses. A matched undated submission without another timely witness is unknown. A timely court witness can establish an observed challenge. Verified non-observation in a fresh list is an operational negative. If no qualifying edition or positive witness is available, the challenge state is unknown. For expanded court matches, the filing date is an availability proxy and the patent association may be incompletely verified. Later dispositions, approvals and marketing fields are excluded from the predictors. Table 1 gives the cutoff schedules [30].

*Table 1. Annual cutoff schedule by horizon.*

| Horizon | Training cutoff year | Development validation years | Sealed test (C′) cutoff years |
| --- | ---: | --- | --- |
| 12 months | 2010 | 2012–2015 | 2017–2025 |
| 24 months | 2010 | 2013–2014 | 2017–2024 |

Cutoffs are on 1 January. The training label availability boundary is the day before development validation starts. The preceding outcome window must end before the next partition begins. The observation end is 27 November 2026 for the scheduled C′ windows. An earlier 36-month evaluation exposed aggregate results from three earlier baseline models on drug histories and periods overlapping C′. The protocol also documents inventory and preflight access [30]. C′ scoring remains pending.

### 3.3 Models, queues and inference

B1 assigns a smoothed approval hazard using age since first NDA approval, with a prevalence fallback for an unseen age bin. M1 uses standardized L2 logistic regression with age, NDA and regulatory indicators, product breadth, patent and exclusivity information, challenge observations, missingness flags and the B1 logit. M3 uses the same inputs and model family and adds indicators for the graph state: OPEN, BLOCKED or CONTESTED. The graph evaluates whether all recorded exclusivities expire by the horizon and whether all recorded patents expire by then or a challenge has been observed. Under Kleene three-valued logic each input can be true, false or unknown. An empty set of expiry dates leaves the corresponding condition unknown. The graph states summarize evidence for predicting an FDA event and have no legal effect.

For each cutoff and horizon, the benchmark ranks all eligible cases by unrounded native risk, prior to calibration or graph policy actions. The review queue takes the integer part of one fifth of the roster. If a tie crosses the boundary, each tied case receives equal fractional credit for the remaining slots. Recall pools the expected captured event rows across cutoffs and divides by all qualifying event rows. Precision divides the expected hits by the slots. Distinct event-drug capture counts a drug's probability of being captured at least once on an event row. A first approval can qualify in overlapping windows, so the pooled and distinct measures answer different questions.

Inference uses 2,000 paired whole-drug bootstrap draws per horizon. Fitted models stay fixed, and each draw recomputes queue sizes and ties with shared drug-cluster multiplicities. A reached step passes if its one-sided lower bound at the linear empirical α quantile exceeds zero. A failed or unevaluable step stops the sequence. Report all estimable contrasts with two-sided 95% percentile intervals and mark unreached steps descriptive. Any undefined draw makes the interval unevaluable. Report whether each point estimate reaches the prespecified +10 percentage-point practical-usefulness threshold alongside the superiority decision. In a preregistration simulation study, simulated H1 power at +10 points with 75 event drugs was 49.96%. The blinded gate’s minimum of 50 event drugs defines admission, and adequate power needs separate assessment [30].

### 3.4 Registration, blinded admission and prospective follow-up

The Open Science Framework (OSF) registration record is pending [30]. The sealed release is designed to require the first author's authorization, the hash of the OSF-issued registered PDF, the pinned code and source identities and a PASS from the blinded gate. The gate first verifies the required edition coverage for every scheduled cutoff. It then checks whether at least 50 distinct eligible event drugs meet the 24-month rule. It releases a verdict while withholding counts and outcomes. Only a technical failure permits one documented retry on identical pinned inputs. A final gate failure yields feasibility evidence only and leaves H1–H3 untested on C′. The sequence runs from completed development through pending OSF registration and blinded C′ admission to authorized scoring if admitted, with a separately scheduled Track A freeze and readouts at maturity.

Track A follows its own schedule and retrains the core fitted arms using the same recipe on eligible windows matured by the prospective origin of 27 November 2026. The core includes B1, M1, M3 and the descriptive expiry-only comparator B3. Eligible exploratory arms may be included under their own admission rules. The roster, sources, models, code, policies and predictions must be hashed, tagged in Git and externally timestamped in OSF before 31 January 2027 at 23:59 UTC and before any post-origin outcome fetch. If that condition fails, subsequent analyses are exploratory. The prospective windows mature on 27 November 2027 and 27 November 2028, respectively. Track A is confirmatory if C′ did not run as a confirmatory analysis, and a replication otherwise. Formal H3 still depends on both preceding steps [30].

### 3.5 Exploratory analyses

For the approved applicant endpoint, the frozen 24-month queues are evaluated at the mature 2013 cutoff against the longer 36-month outcome. The outcome requires at least three distinct legal applicants with final original ANDA approvals. Strengths and repeat approvals are collapsed, and applicant identity uses the first eligible historical Orange Book listing through 12 months after approval, with documented overrides. The current sponsor name supplies a sensitivity analysis. An unresolved applicant remains unknown. Queue membership and tie weights come from the original roster.

The Medicaid reimbursement analysis forecasts next-year prescription counts and annual gross reimbursement, with a separate fourth-quarter reimbursement-per-prescription endpoint. It uses the mapped subset of national State Drug Utilization Data from the Centers for Medicare & Medicaid Services. Carry-forward is the primary baseline and drift is secondary. On exact cutoff and identity matches, the adjusted arms use the frozen 12-month queues and a shared deterministic boundary order. Each queued ingredient's carry-forward reimbursement forecast is multiplied by 0.465, the FDA median generic-to-brand average manufacturer price ratio under a two-producer scenario. Unqueued ingredients retain carry-forward. No historical Medicaid release vintage was verified for the evaluated origins, and the FDA factor was published after those origins. The analysis is retrospective and vintage-uncontrolled. A separate, assumption-based price scenario uses the FDA ratios with a stated marketed-producer count and price basis.

L1 and L1e use the same pinned Qwen2.5-7B-Instruct checkpoint and decoder. L1 receives ingredient identity, cutoff and horizon. L1e also receives the dated upstream evidence used by M3, including graph input clocks and challenge witnesses. It does not receive fitted risks, B1 hazard, graph verdicts, actions or outcomes. The prompt change includes instructions for using the new fields. The contrast evaluates the combined change in evidence presentation and instructions. The optional prospective comparison pairs group relative policy optimization (GRPO) with supervised fine-tuning (SFT) on common inputs at 24 months, subject to a completed pair before the core freeze.

## 4. Results

### 4.1 RQ1: First-approval review queues

The frozen first-approval results are development-only. The 24-month panel had 1,083 rows, 91 event rows from 67 event drugs, and 215 slots. The 12-month panel had 2,161 rows, 90 event rows from 90 event drugs, and 430 slots. Figure 2 shows the paired recall differences with two-sided 95% intervals. All resampling draws were defined.

![Development recall differences for H1–H3 with 95% intervals](figures/fig2_effects_en.png)

*Figure 2. Paired differences in first-approval recall at the 20% review budget on development data. Points are estimates, bars are two-sided 95% whole-drug bootstrap intervals, and vertical lines mark zero and +10 percentage points. Labels give the number of distinct event drugs.*

At 24 months, B1, M1 and M3 recalled 39.65%, 43.96% and 49.45%, respectively. M3 gained +9.80 [0.14, 19.65] percentage points over B1 and +5.49 [−2.00, 11.25] over M1. Both estimates fell below the prespecified +10-point practical-usefulness threshold. At 12 months, the +13.00 [3.27, 23.17] point gain over B1 (48.11% recall) exceeded the threshold on the point estimate. M1 matched M3’s 61.11% recall. H2’s interval includes zero, and undated challenge coding on the training set affected the estimate. The development auto-clear diagnostic failed for every estimable arm and horizon, so cases outside the queue remain in routine review.

- [RESULT PENDING: blinded C′ admission verdict and disposition]
- [RESULT PENDING: C′ H1–H3 estimable contrasts with two-sided 95% intervals, practical-usefulness checks, reached-step decisions and descriptive labels for unreached steps]
- [RESULT PENDING: Track A timestamped prediction freeze and outcome readouts]

RQ1 remains unanswered on confirmatory evidence. If admission fails, the C′ entries will record feasibility and the hypotheses will remain untested on that track.

### 4.2 RQ2: Approved applicant counts and Medicaid reimbursement

In the applicant-count analysis at the single mature 2013 development cutoff, using 24-month scores to assess the 36-month applicant endpoint, M3 captured 15.000 expected events (71.43%) and B1 captured 9.625 (45.83%) out of 21, with 107 slots per arm across 539 rows. Fractional credit for boundary ties explains the non-integer counts. The difference of +25.60 percentage points (paired 95% CI [6.25, 45.00]) describes only this cutoff and the endpoint of at least three distinct applicants receiving final approvals within 36 months. The current-sponsor sensitivity gave the same result.

Applying the 0.465 factor increased mean absolute error (MAE) on both reimbursement endpoints in the retrospectively mapped Medicaid subset, relative to unadjusted carry-forward. Table 2 reports paired ingredient-cluster percentile intervals. The linked analyses cover four origins. They use 160 ingredient-origin pairs from 68 ingredients for reimbursement per prescription and 150 pairs from 64 ingredients for annual reimbursement.

*Table 2. Paired reimbursement MAE differences relative to carry-forward on the linked development subset.*

| Comparison with carry-forward | Fourth-quarter USD per prescription [95% CI] | Annual USD millions [95% CI] |
| --- | ---: | ---: |
| B1-adjusted | +372.05 [193.27, 587.26] | +4.98 [2.24, 8.29] |
| M3-adjusted | +381.24 [203.61, 606.77] | +21.43 [4.07, 53.21] |
| Drift minus carry-forward | −172.13 [−292.12, −66.37] | −3.69 [−8.41, −0.20] |

On the same queue-linked subset, drift reduced MAE for both reimbursement endpoints. Gross reimbursement per prescription rose for queued ingredients in the observed subset, and shrinking the carried-forward forecast worsened underprediction. These descriptive contrasts have no multiplicity adjustment. Payment totals are gross and pre-rebate, include amounts in the source's Medicaid and non-Medicaid fields, and reflect mapped packages only. National full-ingredient totals could not be estimated. In answer to RQ2, the development queue comparison supports investigating approved applicant counts, while the reimbursement comparison does not support using the FDA factor as a Medicaid forecast adjustment.

### 4.3 RQ3: Source trace and evidence-matched language model

The Thai source inventory supports partial demonstrations. The dossier routes unresolved fields to the specialist checklist. [RESULT PENDING: dossier claim-level traceability audit]

The exploratory L1e run completed the full matched development roster. Table 3 reports the evidence-matched language-model comparison. Grouped average precision (AP) treats equal scores as a group. The 12- and 24-month panels have the event counts reported in Section 4.1. Differences use paired whole-drug bootstrap intervals without multiplicity adjustment. The recall gap was negative relative to both L1 and M3 at each horizon.

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

Against M3, L1e recall was lower by 36.87 percentage points at 12 months (L1e − M3, 95% CI [−47.40, −23.92]) and 30.37 at 24 months [−43.08, −16.44]. Against L1, the differences were −10.68 [−17.96, −3.63] and −9.51 [−16.26, −2.43], respectively. L1e versus M3 compares different modelling approaches and evidence representations. L1e versus L1 changes the evidence and instructions together. The results apply to the tested implementations.

The optional prospective comparison uses Qwen2.5-1.5B-Instruct for GRPO and SFT. Training and outcomes are NOT_RUN.

## 5. Conclusion

Dated regulatory predictors warrant further evaluation. The graph’s incremental value remains uncertain. The single-cutoff applicant-count result motivates follow-up on approved applicants, and the mapped Medicaid results support keeping the price factor as a scenario assumption. The gap in the evidence-matched language-model comparison applies to the tested language-model implementation. Market Window Dossier specifies how to trace claims and route unresolved items for specialist review. The claim-level audit is pending.

Several limits affect interpretation. The US cohort is restricted to eligible new molecular entity histories and the endpoint is final regulatory approval. Historical editions can miss prior changes, the identity crosswalk partly relies on later records, and some challenge witnesses have uncertain historical availability. A small number of independent event drugs limits power even when the gate admits the analysis. The approved applicant analysis covers one cutoff. The reimbursement analysis uses retrospectively mapped packages without verified historical release vintages. The language-model comparison is limited to a single checkpoint and prompting configuration and leaves pretraining exposure unresolved.

Future work should complete the blinded admission and timestamp the Track A predictions before outcome access, then score each matured window under the fixed protocol. The dossier needs a claim-by-claim audit of the evidence actually shown, with Thai and ASEAN gaps logged for local verification. Future studies should use marketing records for commercial launch, Thai procurement and utilization records for Thai demand, and the completed workflow for reviewer time savings. Product-specific FTO conclusions require a qualified assessment of claims and legal status for the actual formulation and jurisdiction.

Data and code availability. Code, frozen configurations, task receipts and the preregistration are available in the project repository [31] and the OSF registration [30]. Restricted test labels remain sealed until the registered release.

## References

[1] R. Conrad and R. Lutter, “Generic competition and drug prices: New evidence linking greater generic competition and lower generic drug prices,” US FDA, 2019. [Report](https://www.fda.gov/media/133509/download).

[2] S. Srihangpiboon and T. Ploysuwan, “Diagnosing near-zero instruction effects in cross-domain patent reranking,” conference paper, iSAI-NLP, paper 53, 2026. [Program](https://isai-nlp2026.aiat.or.th/program).

[3] R. F. Beall, J. J. Darrow, and A. S. Kesselheim, “A method for approximating future entry of generic drugs,” *Value Health*, vol. 21, no. 12, pp. 1382–1389, Dec. 2018. [doi: 10.1016/j.jval.2018.04.1827](https://doi.org/10.1016/j.jval.2018.04.1827).

[4] R. F. Beall et al., “Comparing onset of biosimilar versus generic competition in the United States,” *Clin. Pharmacol. Ther.*, vol. 108, no. 6, pp. 1308–1314, 2020. [doi: 10.1002/cpt.1981](https://doi.org/10.1002/cpt.1981).

[5] K. W. Kerr and L. J. Glos, “Effective market exclusivity of new molecular entities for rare and non-rare diseases,” *Pharmaceut. Med.*, vol. 34, no. 1, pp. 19–29, 2020. [doi: 10.1007/s40290-019-00317-9](https://doi.org/10.1007/s40290-019-00317-9).

[6] M. Hu et al., “Predictive analysis of first abbreviated new drug application submission for new chemical entities based on machine learning methodology,” *Clin. Pharmacol. Ther.*, vol. 106, no. 1, pp. 174–181, 2019. [doi: 10.1002/cpt.1479](https://doi.org/10.1002/cpt.1479).

[7] R. Hopefl et al., “Predictive analysis for first submission of generic drug application for orphan drug products using random survival forest,” *Clin. Transl. Sci.*, vol. 18, no. 10, e70365, 2025. [doi: 10.1111/cts.70365](https://doi.org/10.1111/cts.70365).

[8] H. S. Chahal, R. Patel, and M. Shimer, “Marketing of first generic drugs approved by U.S. FDA from January 2010 to June 2017,” U.S. Food and Drug Administration, Nov. 2021. [Report](https://www.fda.gov/media/154101/download).

[9] C. S. Hemphill and B. N. Sampat, “Evergreening, patent challenges, and effective market life in pharmaceuticals,” *J. Health Econ.*, vol. 31, no. 2, pp. 327–339, 2012. [Article](https://www.sciencedirect.com/science/article/abs/pii/S0167629612000057).

[10] S. Kannappan, J. J. Darrow, A. S. Kesselheim, and R. F. Beall, “The timing of 30-month stay expirations and generic entry: A cohort study of first generics, 2013–2020,” *Clin. Transl. Sci.*, vol. 14, no. 5, pp. 1917–1923, 2021. [doi: 10.1111/cts.13046](https://doi.org/10.1111/cts.13046).

[11] M. Durvasula *et al.*, “The NBER Orange Book dataset: A user’s guide,” *Res. Policy*, vol. 52, no. 7, Art. no. 104791, 2023. [doi: 10.1016/j.respol.2023.104791](https://doi.org/10.1016/j.respol.2023.104791).

[12] A. K. Rai, S. Vishnubhakat, J. Lemus, and E. Hovenkamp, “Replication data for: Post-grant adjudication of drug patents: Agency and/or court?,” Harvard Dataverse, ver. 1.0, 2021. [doi: 10.7910/DVN/YCMKVU](https://doi.org/10.7910/DVN/YCMKVU).

[13] F. M. Scott Morton, “Entry decisions in the generic pharmaceutical industry,” *RAND J. Econ.*, vol. 30, no. 3, pp. 421–440, 1999. [doi: 10.2307/2556056](https://doi.org/10.2307/2556056).

[14] D. Reiffen and M. R. Ward, “Generic drug industry dynamics,” *Rev. Econ. Stat.*, vol. 87, no. 1, pp. 37–49, 2005. [doi: 10.1162/0034653053327694](https://doi.org/10.1162/0034653053327694).

[15] A. Hollis, “The importance of being first: Evidence from Canadian generic pharmaceuticals,” *Health Econ.*, vol. 11, no. 8, pp. 723–734, 2002. [doi: 10.1002/hec.698](https://doi.org/10.1002/hec.698).

[16] K. Nikolopoulos, S. Buxton, M. Khammash, and P. Stern, “Forecasting branded and generic pharmaceuticals,” *Int. J. Forecast.*, vol. 32, no. 2, pp. 344–357, 2016. [doi: 10.1016/j.ijforecast.2015.08.001](https://doi.org/10.1016/j.ijforecast.2015.08.001).

[17] A. Trippe, *Guidelines for Preparing Patent Landscape Reports*, prepared for the World Intellectual Property Organization, WIPO Publ. 946, 2015. [Guide](https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf).

[18] World Intellectual Property Organization, *Identifying Inventions in the Public Domain: A Guide for Inventors and Entrepreneurs*, WIPO Publ. 1062, 2020. [Guide](https://www.wipo.int/publications/en/details.jsp?id=4501).

[19] Y. Hu *et al.*, “PatentAgentBench: Benchmarking LLM agents with professional patent task suites,” arXiv:2610.35031, 2026. [Online]. Available: https://arxiv.org/abs/2610.35031

[20] P. Leela and N. Kessomboon, “Challenges of examination processes of pharmaceutical patent application in Thailand,” *Isan J. Pharm. Sci.*, vol. 11, suppl., pp. 179–189, 2016. [Article](https://he01.tci-thaijo.org/index.php/IJPS/article/view/48601).

[21] D. Vachanavuttivong, P. Naboriboon, and A. Homhuan, “Expediting the patent examination system in Thailand: Recent developments,” Tilleke & Gibbins, Bangkok, Thailand, Mar. 3, 2014. [Online]. Available: https://www.tilleke.com/insights/expediting-patent-examination-system-thailand-recent-developments/

[22] D. Paleka, S. Goel, J. Geiping, and F. Tramèr, “Pitfalls in evaluating language model forecasters,” in *Proc. ICLR*, 2026. [Conference paper](https://proceedings.iclr.cc/paper_files/paper/2026/hash/b9d69c72e4587ddf3fa6352890aefc4f-Abstract-Conference.html).

[23] S. He, L. Lv, A. Manela, and J. Wu, “Chronologically consistent large language models,” *J. Financ. Econ.*, vol. 185, Art. no. 104374, 2026. [doi: 10.1016/j.jfineco.2026.104374](https://doi.org/10.1016/j.jfineco.2026.104374).

[24] E. Karger et al., “ForecastBench: A dynamic benchmark of AI forecasting capabilities,” in *Proc. ICLR*, 2025. [Conference paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea74e45a229dac70b5b63b28d8934db6-Abstract-Conference.html).

[25] O. R. van den Akker *et al.*, “Preregistration of secondary data analysis: A template and tutorial,” *Meta-Psychology*, vol. 5, 2021. [doi: 10.15626/MP.2020.2625](https://doi.org/10.15626/MP.2020.2625).

[26] J. Traub et al., “Overcoming common flaws in the evaluation of selective classification systems,” in *Adv. Neural Inf. Process. Syst.*, vol. 37, pp. 2323–2347, 2024. [Paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf).

[27] C. A. Field and A. H. Welsh, “Bootstrapping clustered data,” *J. R. Stat. Soc. B*, vol. 69, no. 3, pp. 369–390, 2007. [doi: 10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x).

[28] U.S. Food and Drug Administration, *Multiple Endpoints in Clinical Trials: Guidance for Industry*, Oct. 2022. [Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials).

[29] B. Turtel, D. Franklin, K. Skotheim, L. Hewitt, and P. Schoenegger, “Outcome-based reinforcement learning to predict the future,” *Trans. Mach. Learn. Res.*, Nov. 2025. [Journal article](https://openreview.net/pdf/6854ebdc1a775820ad158c9a284cbe20d6241201.pdf).

[30] S. Srihangpiboon and T. Ploysuwan, “Market Window Dossier / LOE-Bench: evidence-graph review queues for forecasting US first generic approvals from dated open regulatory records,” OSF preregistration, 2026. [OSF DOI PENDING]

[31] S. Srihangpiboon, “patent-to-pilot: Market Window Dossier and LOE-Bench,” GitHub repository, 2026. Available: https://github.com/siriponsri/patent-to-pilot
