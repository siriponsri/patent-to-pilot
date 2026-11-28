# Evaluating Time-Stamped Regulatory Evidence for Prioritizing US Generic Drug Review

Siripon Srihangpiboon and Asst. Prof. Dr. Tuchsanai Ploysuwan

School of Information Technology, King Mongkut's Institute of Technology Ladkrabang, Bangkok, Thailand

Corresponding author: [confirm name, institutional email, and postal address]

Research and Applications · Internal draft for author review

## Abstract

**Objective**

To evaluate whether regulatory records available at the time of prediction improve prioritization of drug cases for review before first US generic approval.

**Materials and Methods**

In a retrospective cohort benchmark, we ranked eligible drug cases at annual cutoffs using drug age (B1), a dated evidence table (M1), or the table with graph-derived states (M3). Each queue could hold up to 20% of cases per cutoff. The outcome was the first final approval of an original abbreviated new drug application within 12 or 24 months. We estimated paired recall differences by resampling whole drug histories and applied a registered fixed testing sequence.

**Results**

At 24 months, 368 of 4,639 drug-cutoff cases had an event. At 20% review capacity, M3 achieved 66.85% recall and 26.62% precision. Recall was 46.48% for B1 and 65.49% for M1. M3 exceeded B1 by 20.37 percentage points (95% confidence interval, 14.37 to 26.16). The graph increment over M1 failed the second test (1.36 percentage points, 95% confidence interval, −2.20 to 3.01). The automatic clearance rule exceeded the prespecified missed-event bound at both horizons.

**Discussion**

Dated records supported prioritization in the historical cohort. The added value of the graph for recall remains unconfirmed. Prospective outcomes are pending.

**Conclusion**

The historical results support prioritizing review with dated evidence at a fixed capacity and retaining routine review for cases outside the queue.

**Keywords**

Drugs, Generic; Drug Approval; Forecasting; Databases, Factual

## Background and Significance

A retrospective forecast is informative only to the extent that it reconstructs the evidence a reviewer could have used at the decision date. In pharmaceutical regulation, a current database may carry a patent listing, an application link, or a case disposition that was unavailable when a review would have been scheduled. An analysis needs a rule for admitting older editions and a record of when each source was accessible. It also needs to preserve gaps in observation. A missing challenge record and a recent list on which a challenge was unobserved carry different information.

Prior studies have estimated generic entry from patent and exclusivity records or modeled the first submission of an abbreviated new drug application (ANDA) [1, 2]. Hu and colleagues studied first submission, and Hopefl and colleagues adapted a survival forest to first submission for orphan drug products [2, 3]. The present benchmark uses first final approval. Submission, approval and commercial marketing are distinct events. FDA follow-up of approved first generics documents the variable lag from approval to marketing [4]. The endpoint and cohorts in those studies preclude a numerical performance comparison with the present evaluation.

An operational ranking also needs an explicit review capacity. Surveillance researchers have evaluated event capture together with alert burden and lead time [5]. In the regulatory setting, reviewers may choose which cases to examine earlier while retaining ordinary review for all eligible cases. LOE-Bench connects this scheduling decision to a dated evidence record and evaluates alternative rankings on the same roster. A dated table provides a strong direct comparator for a graph that summarizes dependencies among facts already represented in that table.

## Objective

We evaluated whether a graph-augmented ranking increased recall at fixed review capacity over a drug-age ranking and whether adding graph states increased recall over a ranking based on the dated evidence table alone. We also estimated queue precision and examined missed events under a separate automatic clearance rule. Exploratory analyses evaluated a language-model forecaster on the same historical roster and prepared additional comparators for prospective evaluation.

## Materials and Methods

### Setting, eligibility and outcome

LOE-Bench is an observational prediction benchmark built from US Food and Drug Administration (FDA) records and public corroborating sources [6]. The unit of analysis was an active-moiety set at an annual cutoff. An eligible history had a usable ingredient key and a dated first final approval of an original new drug application (NDA). It also had a dated original final NDA record with the exact FDA submission classification `TYPE 1` by the cutoff, marking a new molecular entity for this cohort. Histories with a final original ANDA approval by the cutoff were ineligible. Eligibility required complete follow-up through the end of the forecast window.

The outcome was the first dated FDA final approval of an original ANDA for the same active-moiety set, identified by an original submission with final approval status (`ORIG/AP`). The window began after the cutoff and included its 12- or 24-month end date. Tentative approvals, supplements, and authorized generics marketed under NDAs could not establish the event. Undated or unlinked records could not establish a dated approval. Follow-up used the pinned Drugs@FDA observation snapshot through 27 November 2026. A drug could remain eligible at successive cutoffs while awaiting a first final ANDA approval. The same approval could therefore contribute an event row to overlapping windows.

### Predictor provenance and missing data

We linked applications to ingredient sets using a frozen Global Substance Registration System identifier crosswalk and documented aliases. A usable normalized name supplied a lower-confidence key when identifier matching was unresolved. Undated product records could assist identity linkage. Route flags required dated product evidence. Later identity linkage aided reconstruction and introduces a limitation on how closely the historical inputs reflect the information then available to reviewers.

For the historical evaluation, we selected the most recent FDA Orange Book edition with a matching file digest, a content date within six calendar months of cutoff, and independent evidence of public availability by that cutoff. Content date and availability date were recorded separately. A patent expiry after cutoff could enter as a predictor when the date was recorded in an admitted edition. A patent submission dated after cutoff was excluded. The source manifests record identifiers, editions, retrieval and availability evidence, raw file digests, and source locators [6, 7].

A dated submission in a qualifying FDA Paragraph IV list or a qualifying court witness supported an observed challenge. For court records drawn from a later compilation, the filing date served as an availability proxy [8]. A fresh FDA list could support operational non-observation. A matched undated list entry without another timely witness, or lack of a qualifying edition in the absence of a positive witness, yielded an unknown state. We retained eligible cases with missing predictors. The frozen tabular coding used zero with an indicator for missing numeric evidence and a separate missing indicator for unknown challenge status. Later litigation dispositions and subsequent approvals were excluded from predictor input. The evaluator held the outcome labels separately (Figure 1).

**Figure 1. Construction and evaluation of a dated review queue.** At each cutoff, applications meeting the eligibility criteria formed a common roster. Evidence admitted by cutoff supplied the predictor inputs. The later approval window supplied outcome labels for scoring. The prospective panel shows a separate reference date, timestamped predictions, and pending follow-up.

**Alt text:** A timeline separates source availability, ranking at cutoff, and outcome ascertainment. Development precedes the historical evaluation. A separate prospective timeline shows frozen forecasts and two future window ends.

[Figure specification for Claude. Align three timeline rows for development, historical C′, and prospective Track A. Use the schedules in Methods and Table 1. Show the source edition and availability check before ranking, and a separate outcome path into the evaluator after cutoff. Label both horizons. Distinguish the prospective reference date from the later freeze timestamp. Use line styles and direct labels that remain readable in grayscale.]

### Model development and historical admission

We fit separate models by horizon using the 2010 annual cutoff. Development validation used 2012–2015 for the 12-month horizon and 2013–2014 for the 24-month horizon. All development and historical cutoffs were on 1 January. Each earlier partition's outcome window ended strictly before the next partition began. The registered historical evaluation (C′) used the later schedules in Table 1. Before scoring, a custodian verified source edition coverage at every scheduled cutoff and checked that at least 50 distinct drugs had an eligible event at 24 months. The gate disclosed its verdict alone. The protocol and amendments were registered on the Open Science Framework (OSF) [6].

The preregistration disclosed earlier aggregate results from an overlapping 36-month baseline analysis, a mixed-period preflight that decoded FDA records, and counts of candidate NDA histories used to size simulations. The record describes no per-case outcome inspection or method selection using the exposed historical results. We interpret C′ as a gated retrospective evaluation with documented prior exposure.

**Table 1. Historical evaluation rosters and available review slots.**

| Horizon, months | Annual cutoffs | Eligible drug-cutoff rows | Distinct drugs | Event rows | Distinct event drugs | Slots per arm |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 12 | 2017–2025 | 5,259 | 803 | 202 | 202 | 1,048 |
| 24 | 2017–2024 | 4,639 | 771 | 368 | 202 | 924 |

Slots are summed after rounding down separately at each annual cutoff. Event drugs count each active-moiety set once within a horizon.

The drug-age comparator (B1) estimated horizon-specific probabilities from the time since first original final NDA approval, smoothing age-bin rates toward the training prevalence. The dated evidence model (M1) used standardized ridge logistic regression with age, administrative and route flags, prior NDA count, the B1 logit, patent and exclusivity summaries, observed challenges, product breadth, and missingness indicators. The graph-augmented model (M3) used the same predictors and fitting procedure with additional indicators for OPEN, BLOCKED and CONTESTED states.

To compute the graph state, the rule evaluated whether all recorded exclusivities expired by the horizon end and whether either all recorded patents expired by that date or a qualifying challenge had been observed. An empty set of dates left its component unknown. Kleene three-valued logic mapped a true, false, or unresolved combined condition to OPEN, BLOCKED, or CONTESTED, respectively. These states describe the recorded evidence relative to the forecast horizon. For probability diagnostics and the clearance policy, each model used a sigmoid fitted on whole-drug out-of-fold training predictions. Fitted calibration functions and policy thresholds were carried forward unchanged into historical scoring [6, 7].

### Queue estimand, inference and clearance diagnostic

At each cutoff, each method ranked the same roster by its unrounded native scores. Available slots equaled one fifth of the roster, rounded down. When a tie straddled the last slot, each tied row received a weight equal to the remaining slots divided by the number of tied rows. The expected count of captured events was the sum of queue weights on event rows, pooled across cutoffs. Recall divided this count by all event rows. Precision divided it by all available slots. We also reported capture by distinct event drug, grouped average precision on native scores, and Brier score and expected calibration error on calibrated probabilities. Calibration error used ten equal-width probability bins.

We estimated paired recall differences in percentage points using 2,000 bootstrap samples per horizon. We resampled complete drug histories with replacement, shared each draw across methods, and rebuilt the cutoff rosters, capacities and boundary ties while holding the fits fixed [6, 9]. The fixed testing sequence compared M3 with B1 at 24 months (H1), M3 with M1 at 24 months (H2), and M3 with B1 at 12 months (H3). Each reached test required its one-sided lower percentile bound at α = 0.025 to exceed zero. An undefined interval or a failed step stopped formal inference. We give two-sided 95% percentile intervals and retain estimates for unreached steps as descriptive. The prespecified 10-percentage-point threshold for practical usefulness was assessed separately.

The frozen clearance policy assigned clear, flag or refer actions using calibrated scores and, for M3, referred high-risk BLOCKED conflicts. The upper threshold targeted the review capacity in training. The lower threshold used the largest observed probability below the upper threshold for which the training clear set was nonempty and no more than 1% of cleared cases had an event. We tabulated the resulting actions apart from the native-score queue. The missed-clear rate divided event rows assigned clear by all clear rows. Safety required a 95% interval upper bound at or below 3%, using whole-drug Chernoff inversion conditional on the observed clear roster. A zero clear count left the rate unevaluable [6, 7]. After development safety and endpoint checks failed, the protocol retained clearance as a secondary diagnostic and used queue capacity and defined endpoints for development acceptance. This change preceded registered C′ scoring.

### Exploratory language-model forecasts

Both prompt arms used a pinned Qwen2.5-7B-Instruct checkpoint and greedy decoding. L1 received the ingredient identity, cutoff and horizon. L1e also received the upstream dated regulatory evidence used by M3 and an instruction to use that evidence. The rendered prompts excluded fitted risks, the age-hazard score, graph verdicts, actions and outcome labels. Because evidence and instructions changed together, the L1e versus L1 contrast describes the combined prompt change. We ranked valid probabilities, including probabilities attached to valid abstentions, using the common queue rule. The local evaluator joined forecast identities with FDA outcomes and applied the paired resampling procedure. Model output supplied forecasts; FDA records supplied event labels [6, 10].

### Prospective replication and reporting

Track A applies the frozen core procedure to a new cutoff roster at the 27 November 2026 reference date. The core models were refitted on historical windows mature by that date. The prospective package freezes forecasts on 651 drugs per horizon, including the core methods and exploratory arms. Two open survival comparators adapt random survival forest and Cox proportional hazards methods to the same event definition and dated feature inputs. Their development evaluations reused validation cutoffs. The historical C′ analysis did not include these comparators [11]. The freeze also includes L1 and L1e forecasts and a 24-month exploratory pair using supervised fine-tuning and group relative policy optimization adapters for Qwen2.5-1.5B-Instruct. The package was frozen on 28 November 2026 at 11:18:44 UTC. Approved OSF update 4 records the package digests, with a submission timestamp of 11:30:06 UTC the same day. The 12- and 24-month windows mature on 27 November 2027 and 27 November 2028, respectively. Outcomes are pending [6, 12].

We used STROBE cohort items to report setting, dates, eligibility, missingness and bias, and adapted TRIPOD+AI items for predictor availability, outcome ascertainment, temporal separation, performance and uncertainty [13, 14]. Patient-specific items are inapplicable to drug-cutoff records. The cohort uses public, secondary regulatory and court records at the drug level.

## Results

### Historical cohort and evidence coverage

The custodian gate passed and the registered historical scoring was completed [7]. Every scheduled cutoff had an admitted Orange Book edition. Missingness remained heterogeneous within that coverage. For example, at the 2024 cutoff, challenge evidence was missing for 572 of 615 eligible cases. The annual audit records exclusions, missing predictors, tied scores and expected captured events by method. The registered young-drug subgroup contained no events, leaving its recall undefined. Table 1 shows the difference between event rows and distinct event drugs when windows overlap.

### Recall and precision at fixed capacity

Table 2 reports recall and precision for each historical queue. At 24 months H1 passed, with an M3 versus B1 difference of +20.37 percentage points (95% confidence interval, +14.37 to +26.16), exceeding the separate practical-usefulness threshold. H2 failed. The M3 versus M1 difference was +1.36 percentage points (95% confidence interval, −2.20 to +3.01). H3 was descriptive because the sequence stopped at H2. The 12-month M3 versus B1 difference was +16.69 percentage points (95% confidence interval, +9.98 to +24.21). All planned draws were defined for the primary contrasts (Figure 2) [7].

**Table 2. Historical recall and precision at 20% per-cutoff review capacity.**

| Horizon, months | Method | Recall, % | Precision, % |
| ---: | --- | ---: | ---: |
| 12 | B1, age | 50.64 | 9.76 |
| 12 | M1, dated table | 67.82 | 13.07 |
| 12 | M3, graph-augmented table | 67.33 | 12.98 |
| 24 | B1, age | 46.48 | 18.51 |
| 24 | M1, dated table | 65.49 | 26.08 |
| 24 | M3, graph-augmented table | 66.85 | 26.62 |

**Figure 2. Registered paired recall contrasts at fixed review capacity.** Points represent differences in recall. Intervals are paired whole-drug bootstrap percentile intervals. Formal inference stopped at H2.

**Alt text:** At 24 months, the interval for M3 versus age is above zero and the practical-usefulness threshold. The interval for M3 versus the dated table crosses zero. The shorter-horizon age contrast appears as a descriptive estimate.

[Figure specification for Claude. Use a shared horizontal percentage-point axis with a zero line and a differently styled practical-usefulness line. Plot registered intervals in testing order. Directly label pass, fail, and descriptive status. Use the exact coordinates reported in Results.]

The secondary M1 versus B1 difference at 24 months was +19.01 percentage points (95% confidence interval, +13.34 to +25.62). The distinct-event-drug measure for M3 was 70.79% at 24 months. Calibrated 24-month M3 probabilities had a Brier score of 0.0647 and expected calibration error of 0.0206. Population of the calibration bins was concentrated at low predicted risks. The diagnostic's single error summary leaves calibration in high-risk bins uncertain [7].

### Missed events under the clearance policy

At both horizons, the upper bound on the missed-clear rate for M3 exceeded the prespecified 3% safety limit (Table 3). All other estimable arm-horizon combinations also exceeded the limit. The 24-month B1 policy cleared no cases, leaving its rate unevaluable [7].

**Table 3. Diagnostic clearance policy actions and missed events for M3.**

| Horizon, months | Clear | Flag | Refer | Events among clear calls | Missed-clear rate 95% CI, % | Safety criterion |
| ---: | ---: | ---: | ---: | ---: | --- | --- |
| 12 | 1,678 | 839 | 2,742 | 16 | 0.05 to 4.39 | Fail |
| 24 | 1,413 | 1,069 | 2,157 | 28 | 0.29 to 6.39 | Fail |

The missed-clear interval uses all clear calls as its denominator. The policy's flag counts come from thresholds on calibrated scores and differ from the fixed-capacity queue slots.

### Exploratory language-model results

Both prompt arms returned 9,898 schema-valid forecasts across the two horizons. At 20% review capacity and 24 months, L1e achieved 12.36% recall and 4.92% precision. The paired difference in recall relative to M3 was −54.48 percentage points (95% confidence interval, −61.18 to −47.61). Relative to L1, the difference was −13.78 percentage points (95% confidence interval, −17.71 to −10.32). These contrasts are exploratory and apply to the tested checkpoint, decoder, prompts and retrospective roster [10].

## Discussion

The historical comparison shows how dated regulatory evidence can change the composition of a limited review queue. The improvement over the age comparator was accompanied by a secondary gain of similar magnitude for the dated table. Adding graph states to that table yielded a small estimated change and an interval spanning zero. The graph's added value for recall is unconfirmed. Because the states summarize predictors already available to M1, the incremental test addresses the value of that representation within the specified fitting procedure. The study did not measure whether graph states help reviewers find or interpret evidence.

Recall describes the share of subsequent event rows captured. Precision describes how often a review slot corresponds to an event within the horizon. The observed precision supports interpreting the ranking as a way to concentrate review, with many queued cases still lacking a recorded approval within the window. Recurrent drug histories contribute to the workload and can produce multiple opportunities to capture the same approval. The whole-drug resampling and distinct-drug summary address different aspects of that repeated observation. The separate clearance diagnostic showed that cases outside the queue should retain routine processing.

The historical reconstruction has several limits. Later ingredient crosswalks could improve linkage relative to what a contemporary reviewer could resolve. The filing-date proxy for some court evidence gives weaker support for historical availability than independent proof that an FDA edition was public. A qualifying archive supports observation of listed records; its gaps and the missingness of particular features limit transport to cutoffs with less complete records. Keeping unknown states explicit makes these assumptions inspectable. Earlier aggregate exposure also tempers the independence of the historical benchmark. Finally, the bootstrap intervals condition on the fitted models and this source reconstruction. They do not represent uncertainty from alternative linkage, model refitting or shifts in the approval process.

The language-model forecasts show limited performance under the tested configuration. Since instructions and evidence changed jointly, the paired prompt comparison cannot identify a separate effect of adding dated evidence. Unknown pretraining exposure to later approvals also limits the interpretation of historical language-model forecasts. Prospective forecasting benchmarks use future resolutions to reduce this ambiguity [15, 16]. Track A fixed forecasts before later outcome sources were fetched and provides a separate replication that still awaits maturity.

Market Window Dossier is a proposed consumer of the dated evidence record. A pre-development reviewer could receive the approval-priority signal alongside the source edition, availability basis, content digest, exact locator and a checklist of open verification questions. This provides an input to specialist review. Product AI assistance with assembling and checking that evidence is future work. The benchmark measured US approval prioritization. Extending it to product-specific decisions in another jurisdiction would require locally verified evidence and a new evaluation.

## Conclusion

At fixed review capacity, dated regulatory evidence increased historical capture of first final US generic approvals relative to ranking by drug age. The registered incremental test left the graph's added value unconfirmed, and the diagnostic clearance policy failed its safety criterion. The prospective replication remains pending.

## Acknowledgments

OpenAI GPT-6.2 Sol, through Codex, generated the initial JAMIA draft, figure specifications and supporting submission drafts from existing project records. The planned critique by OpenAI GPT-6.2 Astra and audit by Anthropic Claude Opus 5.5 are pending. The authors will check the final text, analyses, references and figures against source records and take responsibility for the submitted work. The companion declarations identify the research-model use and AI-assisted research tasks to reconcile before submission.

## Data and code availability

The OSF registration and approved updates document the protocol and the prediction freeze [6]. The project repository contains versioned configurations, source manifests, analysis code and aggregate historical results [7, 10, 12]. Sealed row-level historical labels and protected score exports have restricted project access. Source inputs retain their separate reuse terms. The final statement will identify a verified archive and access route for repeatable analyses once the authors confirm permissions and complete a reconstruction check.

## Supplement outline

- **Cohort construction and evidence availability.** Provide the dated intake and outcome flow, per-cutoff eligibility and exclusions, lower-confidence keys, unlisted drugs, and missing predictor counts. Record source owner, edition, content date, independent availability evidence or proxy, exact record or field locator, file digest and reuse terms for each source family.
- **Analysis specification and reproducibility.** Include label and predictor separation, timeline and exposure inventory, the exact feature dictionary, hyperparameters, calibration settings, comparator rules, bootstrap seed and quantile convention. Provide a hand-checkable tied-queue fixture, an authorized reproduction recipe and digests for the code, inputs and aggregate outputs. Mark restricted steps and specify which summaries can be independently checked from public materials.
- **Historical performance by cutoff.** Give annual slots, eligible and event denominators, tied rows and expected hits. Include distinct-drug capture, grouped average precision, calibration bin counts and available probabilities and observed frequencies, undefined intervals, the young-drug subgroup and full clearance action and event counts. Preserve unrun and unevaluable analyses.
- **Exploratory and prospective records.** Give the language-model configuration, allowed fields, prompt differences, quality gate, abstentions and paired estimates for both horizons. Report survival comparator development results with their reused cutoffs and mark their C′ comparison unrun. Document the approved-applicant analysis and unknown-label handling, and the separate vintage limitation and unrun reserved reimbursement analysis. Include the Track A freeze manifest, prospective comparator roles and pending maturity dates.
- **Reporting checklists.** Crosswalk STROBE cohort items on setting, inclusion, dates, exclusions, missingness, outcomes, estimates and limitations to main text and supplement. Crosswalk TRIPOD+AI items on predictors, outcomes, model fitting, evaluation, uncertainty and open science. Mark patient-specific items inapplicable with the drug-cutoff unit as the reason.

## References

[1] Beall RF, Darrow JJ, Kesselheim AS. A method for approximating future entry of generic drugs. Value Health. 2018;21(12):1382–1389. [doi:10.1016/j.jval.2018.04.1827](https://doi.org/10.1016/j.jval.2018.04.1827).

[2] Hu M, Babiskin A, Wittayanukorn S, et al. Predictive analysis of first abbreviated new drug application submission for new chemical entities based on machine learning methodology. Clin Pharmacol Ther. 2019;106(1):174–181. [doi:10.1002/cpt.1479](https://doi.org/10.1002/cpt.1479).

[3] Hopefl R, et al. Predictive analysis for first submission of generic drug application for orphan drug products using random survival forest. Clin Transl Sci. 2025;18(10):e70365. [doi:10.1111/cts.70365](https://pmc.ncbi.nlm.nih.gov/articles/PMC12497357/).

[4] Chahal HS, Patel R, Shimer M. Marketing of first generic drugs approved by U.S. FDA from January 2010 to June 2017. US Food and Drug Administration. 2021. [FDA report](https://www.fda.gov/media/154101/download).

[5] van der Vegt AH, Campbell VK, Webb R, et al. A novel, standardised approach to balancing effectiveness, efficiency and utility of surveillance AI prediction models for hospitalised patients using sepsis prediction as an exemplar. J Am Med Inform Assoc. 2026;33(2):304–315. [doi:10.1093/jamia/ocaf192](https://doi.org/10.1093/jamia/ocaf192).

[6] Srihangpiboon S. Market Window Dossier / LOE-Bench: evidence-graph review queues for forecasting US first generic approvals from dated open regulatory records. Open Science Framework registration, 28 November 2026, with approved updates [1](https://api.osf.io/v2/schema_responses/6b0a5e871c2cd96b1746bce7/), [2](https://api.osf.io/v2/schema_responses/6b0a61a4341762fcbae66946/), [3](https://api.osf.io/v2/schema_responses/6b0a99f9c46379c38a46bcd3/), and [4](https://api.osf.io/v2/schema_responses/6b0abacc9917f6722859f5ec/). [doi:10.17605/OSF.IO/P2SMD](https://doi.org/10.17605/OSF.IO/P2SMD).

[7] Patent-to-Pilot. LOE-Bench historical scoring receipt, preregistration, and frozen source and configuration manifests. [Versioned SCORE receipt and artifact links](https://github.com/siriponsri/patent-to-pilot/blob/a89fdc85/docs/loe-bench/receipts/SCORE.md).

[8] Rai AK, Vishnubhakat S, Lemus J, Hovenkamp E. Replication data for: Post-grant adjudication of drug patents: Agency and/or court? Harvard Dataverse, version 1.0. 2021. [doi:10.7910/DVN/YCMKVU](https://doi.org/10.7910/DVN/YCMKVU).

[9] Field CA, Welsh AH. Bootstrapping clustered data. J R Stat Soc Series B Stat Methodol. 2007;69(3):369–390. [doi:10.1111/j.1467-9868.2007.00593.x](https://doi.org/10.1111/j.1467-9868.2007.00593.x).

[10] Patent-to-Pilot. LOE-Bench exploratory historical language-model scoring receipt. [Versioned SCORELLM receipt and artifact links](https://github.com/siriponsri/patent-to-pilot/blob/a89fdc85/docs/loe-bench/receipts/SCORELLM.md).

[11] Patent-to-Pilot. LOE-Bench open survival comparators. [Versioned PRIORARMS receipt and artifact links](https://github.com/siriponsri/patent-to-pilot/blob/a89fdc85/docs/loe-bench/receipts/PRIORARMS.md).

[12] Patent-to-Pilot. LOE-Bench prospective prediction freeze. [Versioned TRACKA-FREEZE receipt and artifact links](https://github.com/siriponsri/patent-to-pilot/blob/a89fdc85/docs/loe-bench/receipts/TRACKA-FREEZE.md).

[13] von Elm E, Altman DG, Egger M, et al. The Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) statement: guidelines for reporting observational studies. PLoS Med. 2007;4(10):e296. [doi:10.1371/journal.pmed.0040296](https://doi.org/10.1371/journal.pmed.0040296).

[14] Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ. 2024;385:e078378. [doi:10.1136/bmj-2023-078378](https://doi.org/10.1136/bmj-2023-078378).

[15] Paleka D, Goel S, Geiping J, Tramèr F. Pitfalls in evaluating language model forecasters. International Conference on Learning Representations. 2026. [Conference paper](https://proceedings.iclr.cc/paper_files/paper/2026/hash/b9d69c72e4587ddf3fa6352890aefc4f-Abstract-Conference.html).

[16] Karger E, Bastani H, Chen YH, et al. ForecastBench: a dynamic benchmark of AI forecasting capabilities. International Conference on Learning Representations. 2025. [Conference paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea74e45a229dac70b5b63b28d8934db6-Abstract-Conference.html).
