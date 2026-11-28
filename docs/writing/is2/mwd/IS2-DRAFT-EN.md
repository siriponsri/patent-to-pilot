# แฟ้มข้อมูลช่วงเวลาเข้าสู่ตลาดยาสามัญและเกณฑ์มาตรฐาน LOE-Bench สำหรับจัดลำดับการทบทวนหลักฐาน

# Market Window Dossier and LOE-Bench for Prioritizing Generic Drug Evidence Review

นายศิริพล ศรีเฮงไพบูลย์\*¹ และ ผศ.ดร.ทัศนัย พลอยสุวรรณ²\
คณะเทคโนโลยีสารสนเทศ สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง\
เลขที่ 1 ซอยฉลองกรุง 1 แขวงลาดกระบัง เขตลาดกระบัง กรุงเทพฯ 10520

Mr. Siripon Srihangpiboon\*¹ and Asst. Prof. Dr. Tuchsanai Ploysuwan²\
School of Information Technology, King Mongkut's Institute of Technology Ladkrabang\
1 Chalong Krung 1 Alley, Lat Krabang, Bangkok 10520

## บทคัดย่อ

ทีมพัฒนายาสามัญต้องประเมินว่าคู่แข่งจะเข้าตลาดก่อนหรือไม่ และจัดลำดับงานตามกำลังผู้ตรวจสอบเสรีภาพในการดำเนินการ (freedom to operate: FTO) งานนี้ใช้ LOE-Bench ประเมินการพยากรณ์การอนุมัติยาสามัญครั้งแรกในสหรัฐอเมริกาจากข้อมูลเปิด ณ วันตัดข้อมูล ที่ความจุคิวร้อยละ 20 ผลเฉพาะขั้นพัฒนาพบว่า กราฟหลักฐาน M3 เพิ่มการครอบคลุมเหตุการณ์เทียบกับวิธีฐานตามอายุยา B1 ที่ระยะ 24 เดือน 9.80 จุดร้อยละ (ช่วงความเชื่อมั่น 95% [0.14, 19.65]) และที่ระยะ 12 เดือน 13.00 จุดร้อยละ [3.27, 23.17] ผลต่างจากแบบจำลองที่ยังไม่เพิ่มสถานะกราฟ M1 ที่ระยะ 24 เดือนอยู่ที่ 5.49 จุดร้อยละ [−2.00, 11.25] คิว M3 ครอบคลุมยาที่มีผู้ได้รับอนุมัติหลายรายมากกว่า B1 ณ วันตัดข้อมูลเดียว ขณะที่ตัวคูณราคา FDA เพิ่มความคลาดเคลื่อนของยอดเบิกจ่าย Medicaid แบบย้อนหลัง ส่วนแบบจำลองภาษาที่ได้รับหลักฐานต้นทางชุดเดียวกันครอบคลุมเหตุการณ์น้อยกว่า M3 ผลชุดปิดผนึกและการประเมินไปข้างหน้ายังรออยู่ แฟ้มนี้ช่วยจัดลำดับงานและส่งต่อหลักฐาน มิใช่ความเห็นด้าน FTO หรือความเห็นทางกฎหมาย

**คำสำคัญ** ยาสามัญ, ช่วงเวลาเข้าสู่ตลาด, กราฟหลักฐาน, การจัดลำดับการทบทวน, เสรีภาพในการดำเนินการ

## Abstract

Generic drug developers must assess the risk that competitors will enter first and allocate limited freedom-to-operate (FTO) review capacity. We used LOE-Bench to evaluate forecasts of first US generic approvals from open records available at each cutoff. At a 20% review budget, development-only recall for the evidence graph M3 exceeded the age baseline B1 by 9.80 percentage points at 24 months (95% confidence interval [0.14, 19.65]) and 13.00 points at 12 months [3.27, 23.17]. The 24-month difference relative to M1, which omits graph states was 5.49 points [−2.00, 11.25]. At one cutoff, M3 captured more drugs with multiple approved applicants than B1. Applying an FDA price multiplier increased retrospective Medicaid reimbursement forecast error. A language model supplied with the same upstream evidence captured fewer approvals than M3. Sealed and prospective evaluations remain pending. The dossier supports decisions and evidence hand-off. It is not an FTO or legal opinion.

**Keywords** generic drugs, market window, evidence graph, review prioritization, freedom to operate

\* 68076060@kmitl.ac.th\
¹ นักศึกษาปริญญาโท สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ / Postgraduate Student, Artificial Intelligence for Business Analytics Program\
² ผู้ช่วยศาสตราจารย์ คณะเทคโนโลยีสารสนเทศ / Assistant Professor, School of Information Technology, KMITL

## 1. Introduction

Before committing to bioequivalence or comparative trials, a Thai generic or biosimilar developer needs to decide which product candidates warrant closer review. Two questions arise at different stages. At the development decision, will the planned launch still reach a market with enough demand once competitors have entered? At the hand-off, which candidates and unresolved patent questions should a specialist examine first? The project treats limited evaluator capacity and the risk of a shrinking commercial window as design requirements. A local estimate of specialist capacity would require separate evidence. [CITATION NEEDED: empirical evidence on FTO reviewer capacity in Thai generic and biosimilar development]

Market Window Dossier connects these decisions. A team enters the active ingredient, formulation, jurisdiction, decision date and expected launch date. It receives a review priority and a packet with the regulatory and patent evidence behind that priority, market scenarios and a checklist for further investigation. The dossier supports decisions and is not an FTO or legal opinion. A qualified evaluator must assess the relevant claims, their status and their application to the particular product. The study evaluates the US forecast with LOE-Bench and uses Thai and ASEAN sources to examine what can be carried into a local dossier.

The authors' earlier work on patent reranking, reported as Paper 53 [1], found near-zero instruction contrasts in the candidate pools it examined. The original run records were unavailable for independent reanalysis. That work motivates a change in research question. Here we test whether representing dated regulatory evidence as a graph improves review prioritization, and compare that system with a language model that receives the upstream evidence used to build it. A result on the present task does not reproduce the reranking experiment.

- **RQ1 (confirmatory, specified in the preregistration protocol).** At a 20% review budget, does M3 capture more impending first generic approvals than B1 at 24 months (H1), more than M1 at 24 months (H2), and more than B1 at 12 months (H3)? The tests follow this order at one-sided α = 0.025.
- **RQ2 (exploratory).** Do the frozen queues identify drugs with at least three distinct approved generic applicants within 36 months? Does an FDA price-erosion factor improve forecasts of Medicaid reimbursement when applied to queued ingredients?
- **RQ3 (system and exploratory evaluation).** Can open records support a dossier whose material claims can be traced to source records? How does L1e, a language model given the same upstream evidence, compare with M3 on the same forecast rows?

## 2. Background and Related Work

### 2.1 Forecasting generic approval and regulatory timing

Hu et al. modelled first abbreviated new drug application (ANDA) submission for new chemical entities [2]. Hopefl et al. applied random survival forests to first submissions for orphan drug products [3]. These studies are external comparators for the task of forecasting regulatory milestones. Submission comes before the first final approval measured here, and the published studies do not supply a score on the LOE-Bench roster. Beall et al. compared the onset of biosimilar and generic competition [4], while an FDA follow-up studied whether approved first generics were marketed [5]. The distinction matters for a planning dossier because the public date of approval marks a regulatory milestone, whereas launch requires separate evidence of marketing. Biosimilar competition also calls for its own sources and outcome definitions.

Patent terms and exclusivity periods constrain the set of plausible approval dates. Hemphill and Sampat studied how patent challenges and listings relate to effective market life [6], and Kannappan et al. compared stay expirations with generic entry timing [7]. These studies motivate using challenge evidence alongside expiry dates. A case filed before the cutoff, its public visibility at the cutoff and its eventual disposition are different facts. The Rai et al. replication dataset [8] supplies candidate filing witnesses for the benchmark. Treating the filing date as an availability proxy for some historical matches leaves uncertainty about when a user could have found them.

### 2.2 Competition, price, and demand

Reiffen and Ward modelled industry dynamics in relation to entry and prices [9]. Conrad and Lutter reported a relationship between the number of generic producers and lower prices using FDA price measures [10]. The number of legally distinct applicants that obtained final approvals can be reconstructed more readily than the number of suppliers actively selling. The regulatory count can help prioritize an investigation of crowding, but each approval still requires separate evidence on launch and supply. Applying the FDA factor to Medicaid payments tests a new use of that factor. Provider reimbursement mixes utilization and payment per prescription and can move differently from average manufacturer price. Nikolopoulos et al. provide a pharmaceutical forecasting precedent for comparing a proposed adjustment with simple extrapolation [11]. In this study the carry-forward and drift forecasts give the reimbursement scenario explicit comparison points.

### 2.3 Patent review and local evidence

The World Intellectual Property Organization (WIPO) gives guidance on preparing patent landscapes [12] and on searching for and assessing information relevant to FTO [13]. A landscape can organize search results by family and jurisdiction. A hand-off needs additional detail about the proposed product, claims, status and currency of the cited records. Overlapping families across jurisdictions do not settle whether the relevant claims are effective in a particular jurisdiction. A documented failed lookup therefore leaves an open item for review. Thai work by Leela and Kessomboon provides context for pharmaceutical patent examination [14]. The ASEAN IP Register provides a regional discovery source [15]. These sources motivate the local trace layer and do not establish the coverage of historical Thai pharmaceutical records or the accuracy of a Thai forecast.

### 2.4 Dated evidence, model comparisons and review budgets

Paleka et al. describe pitfalls in evaluating language models on historical forecasting tasks [16]. Supplying only timely documents at inference limits input leakage. It does not exclude earlier exposure to historical outcomes during pretraining. ForecastBench uses questions resolved after forecasts are collected [17] and motivates the prospective prediction freeze. The historical benchmark also requires documentary proof that a source edition was available at the cutoff, independently of the dates inside it. Superseded listings and later corrections can change the information a developer could have used.

Selective prediction studies examine how errors vary with the fraction of cases handled by the system [18]. The staffing decision in this study calls for a direct measure of how many priority events can be brought into review at a specified capacity. Cluster resampling preserves the dependence among repeated observations on the same drug [19]. The confirmatory comparisons use a fixed testing order, following the gatekeeping principle in FDA guidance [20]. Outcome-based reinforcement learning supplies a precedent for an optional forecast experiment [21]. Its direct comparator here is a supervised adapter initialized from the same checkpoint, rather than an accuracy number from an external forecasting task.

Together, this work motivates an open-data benchmark that joins dated first-approval forecasts, a fixed review capacity and a source-level hand-off. The question is whether the additional structure benefits the queue under matched evaluation, with market and jurisdictional extensions tested on outcomes appropriate to their sources.

## 3. Methods

### 3.1 Dossier workflow and traceability

Figure 1 follows an analyst from the input product and decision date through the launch-window forecast and evidence review to the FTO hand-off. The queue ranks an active-moiety set for review. The dossier describes the proposed product and jurisdiction so a reviewer can decide whether the ranked ingredient-level evidence applies to the specific formulation. A commercial scenario can add information about competition, demand and price assumptions when the underlying records support it. A reviewer can inspect each source and request evidence that is missing, outdated or inconsistent.

![Market Window Dossier workflow](../../../assets/market-window-flow.svg)

*Figure 1. Market Window Dossier workflow from product intake and launch-window forecast to evidence hand-off for specialist review.*

The evaluation labels in the figure describe the planned design. At this draft stage, C′ remains sealed and the Track A prediction freeze is pending.

Each material claim is designed to carry a source identifier, version, content hash, exact locator and availability basis. The reader should be able to retrieve the cited edition and inspect the specific table row, register entry or document passage. A dated application record is an observation. A queue score is a model estimate. A price multiplier applied to a forecast is a scenario assumption. The dossier specifies which kind of claim is being made, and separately records known, unknown and not applicable states. An unavailable register or unresolved match generates a checklist item for manual verification. A matching hash supports reproducibility of the source bytes. A traceability audit must also check whether the identified passage supports the proposition.

The Thai source inventory probes national patent and drug records, reference prices and procurement sources. The ASEAN layer records family or status leads for verification in the relevant jurisdiction. The system design provides sections for the decision page, market window, competitors, patents and exclusivity, Thai and ASEAN records, the specialist checklist and reproducibility notes. The product-level traceability audit and its acceptance result remain pending. [Thai source inventory](../../../loe-bench/THAI-OPEN-DATA.md) · [Dossier specification](../../../loe-bench/PLAN.md)

### 3.2 As-of cohort and outcome

LOE-Bench treats each set of active moieties at an annual cutoff as an observation. A drug qualifies if it has a usable ingredient key, an original final new drug application (NDA) approval dated by the cutoff and an original final NDA record with the exact classification TYPE 1 by that date. It must have no dated first final ANDA on or before the cutoff. The endpoint is the first dated original final ANDA approval (ORIG/AP) after the cutoff and through the horizon end, inclusive. Tentative approvals, authorized generics under NDAs and supplements as first approvals are excluded. Every row requires complete follow-up even when an approval has already occurred. Repeated rows for the same ingredient set remain in one drug cluster.

Drugs@FDA supplies approvals and dated administrative records. The Global Substance Registration System (GSRS) supports identity resolution. The frozen linkage uses substance identifiers and aliases, with flagged normalized-name fallback when needed. A record without a usable date or link cannot establish an eligible event. Missing predictors on eligible rows are retained. For patent, exclusivity and product breadth, C′ requires the newest eligible historical Orange Book ZIP whose content date falls within the inclusive prior six calendar months, with independent evidence of availability by the cutoff and a matching file hash. Eligible editions can report future expiry dates. Later products and patent submissions are filtered out.

Challenge evidence uses fresh, availability-proven FDA Paragraph IV editions and qualifying court witnesses. A matched undated submission without another timely witness is unknown. A timely court witness can establish an observed challenge. Verified non-observation in a fresh list is an operational negative. If no qualifying edition or positive witness is available, the challenge state is unknown. For expanded court matches, the filing date is an availability proxy and the patent association may be incompletely verified. Later dispositions, approvals and marketing fields are excluded from the predictors. Table 1 gives the cutoff schedules. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

*Table 1. Annual cutoff schedule by horizon.*

| Horizon | Training cutoff year | Development validation years | Sealed C′ cutoff years |
| --- | ---: | --- | --- |
| 12 months | 2010 | 2012–2015 | 2017–2025 |
| 24 months | 2010 | 2013–2014 | 2017–2024 |

Cutoffs are on 1 January. The training label availability boundary is the day before development validation starts. The preceding outcome window must end before the next partition begins. The observation end is 27 November 2026 for the scheduled C′ windows. Earlier aggregate baseline results from an overlapping retrospective period were disclosed, along with the inventory and preflight access described in the protocol. The present C′ scores remain sealed.

### 3.3 Models, queues and inference

B1 assigns a smoothed approval hazard using age since first NDA approval, with a prevalence fallback for an unseen age bin. M1 uses standardized L2 logistic regression with age, NDA and regulatory indicators, product breadth, patent and exclusivity information, challenge observations, missingness flags and the B1 logit. M3 uses the same inputs and model family and adds indicators for the graph state: OPEN, BLOCKED or CONTESTED. The graph evaluates whether all recorded exclusivities expire by the horizon and whether all recorded patents expire by then or a challenge has been observed. Under Kleene three-valued logic each input can be true, false or unknown. An empty set of expiry dates leaves the corresponding condition unknown. The graph states summarize evidence for predicting an FDA event and have no legal effect.

For each cutoff and horizon, the benchmark ranks all eligible cases by unrounded native risk, prior to calibration or graph policy actions. The review queue takes the integer part of one fifth of the roster. If a tie crosses the boundary, each tied case receives equal fractional credit for the remaining slots. Recall pools the expected captured event rows across cutoffs and divides by all qualifying event rows. Precision divides the expected hits by the slots. Distinct event-drug capture counts a drug's probability of being captured at least once on an event row. A first approval can qualify in overlapping windows, so the pooled and distinct measures answer different questions.

Inference uses 2,000 paired whole-drug bootstrap draws per horizon with fixed fitted models, shared cluster multiplicities and newly computed queue sizes and ties in each draw. The one-sided decision uses the linear empirical α quantile. A reached step succeeds only when its lower bound exceeds zero. A failed or unevaluable step stops formal testing and later steps are descriptive if estimable. Any undefined replicate makes the corresponding interval unevaluable. Two-sided 95% percentile intervals accompany estimable contrasts. The development-based T4c simulation estimated an H1 minimum detectable gain of about 14 percentage points for 80% power at 75 event-drug clusters. This is a scenario-specific planning estimate, separate from the blinded event-admission criterion. [FREEZE](../../../loe-bench/receipts/FREEZE.md) · [Power receipt](../../../loe-bench/receipts/T4c.md)

### 3.4 Registration, blinded admission and prospective follow-up

The Open Science Framework (OSF) registration record is pending [OSF DOI PENDING]. The sealed release is designed to require the first author's authorization, the hash of the OSF-issued registered PDF, the pinned code and source identities and a PASS from the blinded gate. The gate first verifies the required edition coverage for every scheduled cutoff. It then checks whether at least 50 distinct eligible event drugs meet the 24-month rule. It releases a verdict while withholding counts and outcomes. Only a technical failure permits one documented retry on identical pinned inputs. A final failure yields feasibility evidence and leaves H1–H3 untested on C′. Figure 2 outlines the release and follow-up sequence.

> [FIGURE PLACEMENT: study timeline]

*Figure 2. Evidence timeline from development through OSF registration and blinded C′ admission to the prospective prediction freeze and outcome readouts.*

After the C′ disposition, Track A retains the same recipe and retrains the core fitted arms on eligible windows matured by the prospective origin of 27 November 2026. The core includes B1, M1, M3 and the descriptive expiry-only comparator B3. Eligible exploratory arms may be included under their own admission rules. The roster, sources, models, code, policies and predictions must be hashed, tagged in Git and externally timestamped in OSF before 31 January 2027 at 23:59 UTC and before any post-origin outcome fetch. If that condition fails, subsequent analyses are exploratory. The prospective windows mature on 27 November 2027 and 27 November 2028, respectively. Track A is confirmatory if C′ did not run as a confirmatory analysis, and a replication otherwise. Formal H3 still depends on both preceding steps. [Preregistration protocol](../../../loe-bench/PREREGISTRATION.md)

### 3.5 Exploratory analyses

For crowding, the frozen 24-month queues are evaluated at the mature 2013 cutoff against the longer 36-month outcome. The outcome requires at least three distinct legal applicants with final original ANDA approvals. Strengths and repeat approvals are collapsed, and applicant identity uses the first eligible historical Orange Book listing through 12 months after approval, with documented overrides. The current sponsor name supplies a sensitivity analysis. An unresolved applicant remains unknown. Queue membership and tie weights come from the original roster.

For Medicaid, the analysis forecasts next-year prescription counts and annual gross reimbursement, with a separate fourth-quarter reimbursement-per-prescription endpoint. It uses the mapped subset of national State Drug Utilization Data from the Centers for Medicare & Medicaid Services. Carry-forward is the primary baseline and drift is secondary. On exact cutoff and identity matches, the adjusted arms use the frozen 12-month queues and a shared deterministic boundary order. Each queued ingredient's carry-forward reimbursement forecast is multiplied by 0.465, the FDA median generic-to-brand average manufacturer price ratio under a two-producer scenario. Unqueued ingredients retain carry-forward. No historical Medicaid release vintage was verified for the evaluated origins, and the FDA factor was published after those origins. The analysis is retrospective and vintage-uncontrolled. [Crowding receipt](../../../loe-bench/receipts/C3b.md) · [Reimbursement receipt](../../../loe-bench/receipts/C4b.md)

L1 and L1e use the same pinned Qwen2.5-7B-Instruct checkpoint and decoder. L1 receives ingredient identity, cutoff and horizon. L1e also receives the dated upstream evidence used by M3, including graph input clocks and challenge witnesses. It does not receive fitted risks, B1 hazard, graph verdicts, actions or outcomes. The prompt change includes instructions for using the new fields. The contrast evaluates the combined change in evidence presentation and instructions. An optional Track A comparison pairs group relative policy optimization (GRPO) with supervised fine-tuning (SFT) on common inputs at 24 months, subject to a completed pair before the core freeze. [L1](../../../loe-bench/receipts/L1DEV.md) · [L1e](../../../loe-bench/receipts/C2.md) · [C9](../../../loe-bench/receipts/C9.md)

## 4. Results

### 4.1 RQ1: First-approval review queues

The FREEZE results are development-only. At 12 months, the panel had 2,161 rows, 90 event rows from 90 drugs and 430 review slots. At 24 months it had 1,083 rows, 91 event rows from 67 drugs and 215 slots. Table 2 reports recall and the 95% paired intervals for the prespecified contrasts. The intervals use whole-drug resampling with all draws defined. They characterize development performance and do not enter the confirmatory testing sequence.

*Table 2. Frozen first-approval recall at a 20% budget and development-only contrasts.*

| Months | B1 | M1 | M3 | Contrast | Difference, pp [95% CI] |
| ---: | ---: | ---: | ---: | --- | --- |
| 24 | 39.65% | 43.96% | 49.45% | H1: M3 − B1 | +9.80 [+0.14, +19.65] |
| 24 | 39.65% | 43.96% | 49.45% | H2: M3 − M1 | +5.49 [−2.00, +11.25] |
| 12 | 48.11% | 61.11% | 61.11% | H3: M3 − B1 | +13.00 [+3.27, +23.17] |

Both contrasts with the age baseline have development intervals above zero. The H2 interval allows a modest loss as well as an improvement. H2 was sensitive to the coding of undated challenges on TRAIN, so the comparison warrants particular care after a test release. The separate development auto-clear diagnostic failed its safety criterion for every estimable arm-horizon. Cases outside the queue remain in the normal review process. [FREEZE](../../../loe-bench/receipts/FREEZE.md)

- [RESULT PENDING: blinded C′ admission verdict and disposition]
- [RESULT PENDING: H1 C′ recall difference, 95% CI and decision]
- [RESULT PENDING: H2 C′ recall difference, 95% CI and decision if reached]
- [RESULT PENDING: H3 C′ recall difference, 95% CI and decision if reached]
- [RESULT PENDING: Track A timestamped prediction freeze and outcome readouts]

RQ1 remains unanswered on confirmatory evidence. If admission fails, the C′ entries will record feasibility and the hypotheses will remain untested on that track.

### 4.2 RQ2: Applicant crowding and Medicaid reimbursement

At the single mature 2013 cutoff, the applicant analysis covered 539 rows, 107 review slots per arm and 21 event drugs. The frozen M3 queue recalled 71.43% of crowding events, compared with 45.83% for B1. The difference was +25.60 percentage points (paired drug-cluster 95% CI [+6.25, +45.00]). The current-sponsor sensitivity yielded the same result on this cutoff. The interval is descriptive and the comparison has no confirmatory test or multiplicity adjustment. [C3b](../../../loe-bench/receipts/C3b.md)

In the retrospective Medicaid analysis, both FDA-factor queue adjustments increased mean absolute error (MAE) compared with unadjusted carry-forward on both reimbursement endpoints. Table 3 reports paired ingredient-cluster percentile intervals. The linked analyses cover four origins. They use 160 ingredient-origin pairs from 68 ingredients for reimbursement per prescription and 150 pairs from 64 ingredients for annual reimbursement.

*Table 3. Paired reimbursement MAE differences relative to carry-forward on the linked development subset.*

| Adjustment | Fourth-quarter USD per prescription [95% CI] | Annual USD millions [95% CI] |
| --- | ---: | ---: |
| B1-adjusted | +372.05 [193.27, 587.26] | +4.98 [2.24, 8.29] |
| M3-adjusted | +381.24 [203.61, 606.77] | +21.43 [4.07, 53.21] |

Gross reimbursement per prescription rose for queued ingredients in the observed subset, and shrinking the carried-forward forecast worsened underprediction. These descriptive contrasts have no multiplicity adjustment. Payment totals are gross and pre-rebate, include amounts in the source's Medicaid and non-Medicaid fields, and reflect mapped packages only. National full-ingredient totals could not be estimated. In answer to RQ2, the development queue comparison supports investigating applicant crowding, while the reimbursement comparison does not support using the FDA factor as a Medicaid forecast adjustment. [C4b](../../../loe-bench/receipts/C4b.md)

### 4.3 RQ3: Source trace and evidence-matched language model

The Thai source inventory identified sources suitable for partial demonstrations and gaps that prevent a complete local forecast. The dossier contract accommodates these gaps by recording the trace of an observed record and carrying unresolved fields into the specialist checklist. A complete claim-level audit and an assessment of reviewer benefit remain pending. [RESULT PENDING: dossier claim-level traceability audit]

The exploratory L1e run completed the full matched development roster. Table 4 reports the C2 comparisons. Grouped average precision (AP) treats equal scores as a group. The 12- and 24-month panels have the event counts reported in Section 4.1. Differences use paired whole-drug bootstrap intervals without multiplicity adjustment. The recall gap was negative relative to both L1 and M3 at each horizon.

*Table 4. Evidence-matched language model and comparator results on development data.*

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

Against M3, L1e recall was lower by 36.87 percentage points at 12 months (L1e − M3, 95% CI [−47.40, −23.92]) and 30.37 at 24 months [−43.08, −16.44]. Against L1, the differences were −10.68 [−17.96, −3.63] and −9.51 [−16.26, −2.43], respectively. Thus the tested evidence presentation did not close the development gap with the trained graph model. This is a comparison between implementations with different training and evidence encodings. It does not isolate the effect of the graph or generalize to other language models. [C2](../../../loe-bench/receipts/C2.md)

[RESULT PENDING: optional Track A GRPO versus SFT comparison if admitted]

## 5. Conclusion

Market Window Dossier uses dated evidence to prioritize drug candidates and prepare a traceable hand-off. For RQ1, M3 covered more development approval events than B1, while the 24-month difference from M1 remained uncertain. The sealed sequence and prospective evaluation are the planned sources of evidence for a confirmatory answer. For RQ2, the single-cutoff crowding result motivates a broader regulatory follow-up, while the retrospective reimbursement result supports leaving the FDA factor as a scenario assumption. For RQ3, the dossier specifies a source trail and a way to carry unknowns into review. The L1e development results establish a performance gap for the implementation examined here, and dossier-wide claim coverage still needs to be measured.

Several limits affect interpretation. The US cohort is restricted to eligible new molecular entity histories and the endpoint is final regulatory approval. Historical editions can miss prior changes, the identity crosswalk partly relies on later records, and some challenge witnesses have uncertain historical availability. A small number of independent event drugs limits power even when the gate admits the analysis. The crowding check covers one cutoff. The reimbursement analysis uses retrospectively mapped packages without verified historical release vintages. These results do not establish Thai demand, product-level freedom to operate or a workload benefit for evaluators. The language-model comparison is limited to a single checkpoint and prompting configuration and leaves pretraining exposure unresolved.

Future work should complete the blinded admission and timestamp the Track A predictions before outcome access, then score each matured window under the fixed protocol. The dossier needs a claim-by-claim audit of the evidence actually shown, with Thai and ASEAN gaps logged for local verification. Direct records of marketing, procurement and utilization would support separate studies of launch and demand. Measuring evaluator effort and decision quality would require a review study using the final workflow and appropriate institutional clearance.

## References

[1] S. Srihangpiboon and T. Ploysuwan, “Diagnosing near-zero instruction effects in cross-domain patent reranking,” iSAI-NLP conference program, paper 53, 2026. [Program](https://isai-nlp2026.aiat.or.th/program).

[2] M. Hu, A. Babiskin, and S. Wittayanukorn, “Predictive analysis of first abbreviated new drug application submission for new chemical entities based on machine learning methodology,” *Clin. Pharmacol. Ther.*, 2019. [doi: 10.1002/cpt.1479](https://doi.org/10.1002/cpt.1479).

[3] R. Hopefl et al., “Predictive analysis for first submission of generic drug application for orphan drug products using random survival forest,” *Clin. Transl. Sci.*, 2025. [doi: 10.1111/cts.70365](https://doi.org/10.1111/cts.70365).

[4] R. F. Beall et al., “Comparing onset of biosimilar versus generic competition in the United States,” *Clin. Pharmacol. Ther.*, vol. 108, no. 6, pp. 1308–1314, 2020. [doi: 10.1002/cpt.1981](https://doi.org/10.1002/cpt.1981).

[5] H. S. Chahal, R. Patel, and M. Shimer, “Marketing of first generic drugs approved by U.S. FDA from January 2010 to June 2017,” US FDA, 2021. [Report](https://www.fda.gov/media/154101/download?attachment=).

[6] C. S. Hemphill and B. N. Sampat, “Evergreening, patent challenges, and effective market life in pharmaceuticals,” *J. Health Econ.*, vol. 31, no. 2, pp. 327–339, 2012. [Article](https://www.sciencedirect.com/science/article/abs/pii/S0167629612000057).

[7] S. Kannappan, J. J. Darrow, A. S. Kesselheim, and R. F. Beall, “The timing of 30-month stay expirations and generic entry: A cohort study of first generics, 2013–2020,” *Clin. Transl. Sci.*, vol. 14, no. 5, pp. 1917–1923, 2021. [doi: 10.1111/cts.13046](https://doi.org/10.1111/cts.13046).

[8] A. K. Rai, S. Vishnubhakat, J. Lemus, and E. Hovenkamp, “Replication data for: Post-grant adjudication of drug patents: Agency and/or court?,” Harvard Dataverse, ver. 1.0, 2021. [doi: 10.7910/DVN/YCMKVU](https://doi.org/10.7910/DVN/YCMKVU).

[9] D. Reiffen and M. R. Ward, “Generic drug industry dynamics,” *Rev. Econ. Stat.*, vol. 87, no. 1, pp. 37–49, 2005. [Working paper](https://www.ftc.gov/sites/default/files/documents/reports/generic-drug-industry-dynamics/industrydynamicsreiffenwp_0.pdf).

[10] R. Conrad and R. Lutter, “Generic competition and drug prices: New evidence linking greater generic competition and lower generic drug prices,” US FDA, 2019. [Report](https://www.fda.gov/media/133509/download).

[11] K. Nikolopoulos, S. Buxton, M. Khammash, and P. Stern, “Forecasting branded and generic pharmaceuticals,” *Int. J. Forecast.*, vol. 32, no. 2, pp. 344–357, 2016. [doi: 10.1016/j.ijforecast.2015.08.001](https://doi.org/10.1016/j.ijforecast.2015.08.001).

[12] World Intellectual Property Organization, *Guidelines for Preparing Patent Landscape Reports*, WIPO Publ. 946, 2015. [Guide](https://www.wipo.int/edocs/pubdocs/en/wipo_pub_946.pdf).

[13] World Intellectual Property Organization, *Identifying Inventions in the Public Domain: A Guide for Inventors and Entrepreneurs*, WIPO Publ. 1062, 2020. [Guide](https://www.wipo.int/publications/en/details.jsp?id=4501).

[14] P. Leela and N. Kessomboon, “Challenges of examination processes of pharmaceutical patent application in Thailand,” *Isan J. Pharm. Sci.*, vol. 11, suppl., 2016. [Article](https://he01.tci-thaijo.org/index.php/IJPS/article/view/48601).

[15] ASEAN Intellectual Property Portal, “ASEAN IP Register.” [Register](https://ip-register.aseanip.org/).

[16] D. Paleka, S. Goel, J. Geiping, and F. Tramèr, “Pitfalls in evaluating language model forecasters,” arXiv:2506.00723, 2025. [Preprint](https://arxiv.org/abs/2506.00723).

[17] E. Karger et al., “ForecastBench: A dynamic benchmark of AI forecasting capabilities,” in *Proc. ICLR*, 2025. [Paper](https://arxiv.org/abs/2409.19839).

[18] J. Traub et al., “Overcoming common flaws in the evaluation of selective classification systems,” in *Adv. Neural Inf. Process. Syst.*, 2024. [Paper](https://proceedings.neurips.cc/paper_files/paper/2024/file/047c84ec50bd8ea29349b996fc64af4b-Paper-Conference.pdf).

[19] C. A. Field and A. H. Welsh, “Bootstrapping clustered data,” *J. R. Stat. Soc. B*, vol. 69, no. 3, pp. 369–390, 2007. [doi: 10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x).

[20] US FDA, *Multiple Endpoints in Clinical Trials: Guidance for Industry*, 2022. [Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/multiple-endpoints-clinical-trials).

[21] B. Turtel, D. Franklin, K. Skotheim, L. Hewitt, and P. Schoenegger, “Outcome-based reinforcement learning to predict the future,” arXiv:2505.17989, 2025. [Preprint](https://arxiv.org/abs/2505.17989).
