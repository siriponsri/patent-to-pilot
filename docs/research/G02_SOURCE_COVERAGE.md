# G02 — Primary-source coverage and locators

24 ตุลาคม 2026 · selected methods review จาก local collection เดิม · ไม่ reproduce งาน/ไม่สร้าง performance result ใหม่

Page locators เป็น **PDF page number เริ่มที่ 1** เว้นแต่บอก printed page เพิ่ม Filename/version/source identity อิง [literature manifest](../../literature-review/manifest.json); เปิด local PDF ด้วย PyMuPDF เพื่ออ่านข้อความในหน้าที่ระบุ ไม่ใช้ title/abstract หรือ metadata อย่างเดียวแทน methods review Page count/extractability ไม่เป็น proof ว่า source claim ถูกต้อง

**Repository publication note:** every local PDF link in this document points to a workspace-only reading copy; the PDFs and G02 acquisition manifest are not included in the public repository. Use the citation/official source link on the same entry instead. For the two G02 additions, the official sources are [SkillOpt arXiv v2](https://arxiv.org/abs/2605.23904v2) and [HarnessOpt-Bench arXiv v1](https://arxiv.org/abs/2608.06301v1).

Text ของ selected pages อ่านครบตามที่ระบุ ส่วน figure images ตรวจเพิ่มใน S01 PDF p.3, S06 p.7 และ S08 p.2 ไม่มีการคัดลอกรูปลง deliverables ไม่อ้าง visual review ของทุกหน้า/appendix Text extraction ทั้งไฟล์ที่ใช้เตรียมอ่านเป็น scratch work ไม่เท่ากับ critical reading ของทุกหน้า

## S01 Oltra-Garcia 2018

**Efficient searching with situation specific and adaptive search strategies: Training material for patent searchers** · World Patent Information 54 (2018), S29–S32 · [DOI](https://doi.org/10.1016/j.wpi.2017.05.001) · [local PDF](../../literature-review/pdfs/02-patent-ai/29_oltra_garcia_2018.pdf)

- **Read:** full four-page text, PDF pp.1–4 = S29–S32; image of adaptive diagram on PDF p.3/S31 inspected in G02; earlier project note covers both diagrams
- **Witness:** §3/S30 linear stages; §4/S31 uses intermediate results to reassess earlier what/where/how; §5/S31–S32 compares alternatives during search; S32 describes learning across searches and tool independence
- **Limits:** instructional/practitioner account; four pages contain no quantified controlled task/label/timing study No legal-completeness guarantee or measured PTP saving follows from it Copyright/acceptance year 2017 does not change displayed 2018 volume citation
- **Claim links:** C02/C07, adaptive comparator; not firstness evidence

## S02 PatExpert

**Towards Automated Patent Workflows: AI-Orchestrated Multi-Agent Framework for Intellectual Property Management and Analysis** · arXiv:2409.19006v2 · [primary](https://arxiv.org/abs/2409.19006v2) · [local PDF](../../literature-review/pdfs/02-patent-ai/03_patexpert.pdf)

- **Read:** PDF pp.3–6, §2, Figure 1 caption, §§3.1–3.3; selected methods/datasets/metrics, not full results/appendix appraisal
- **Witness:** p.3 meta/sub-agent orchestration, critique, Graph RAG and hypothesis generation; p.4 subtask DAG/tool planning; p.5 critique iteration bound and patent tasks; pp.5–6 task/evaluation setup
- **Limits:** §3.2/p.5 calls GPT-4o-style generated hypotheses/analyses gold/expert references; that wording does not supply independent human clinical/legal validation Assertions that critique ensures accuracy remain paper claims, not a guarantee we adopt No PTP downstream-change experiment is inferred from this task list
- **Claim links:** C01/C06; no patent-agent/hypothesis firstness

## S03 ACE

**Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models** · arXiv:2510.04618v3 · [primary](https://arxiv.org/abs/2510.04618v3) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/07_ace.pdf)

- **Read:** PDF pp.3–6, §§2–3.2 and §§4.1–4.2 portion; main method and evaluation setup, not full result/appendix replication
- **Witness:** §3/p.4 generator/reflector/curator, deterministic merge of itemized deltas; §§3.1–3.2/p.5 IDs/helpful-harmful counters, localized updates/grow-and-refine; §4.1/p.6 distinguishes offline adaptation from sequential online update; §4.2/p.6 includes ICL with demonstrations when they fit context
- **Limits:** prior context adaptation already uses feedback without weight updates Published in-context comparison is not automatically identical to our exact confirmed-corrections control Our checkpointed fresh-test design differs from ACE's described online predict-then-update test stream
- **Claim links:** C03; ACE-style comparator is interpretation unless actually reproduced

## S04 ShareMem

**Learning from Others, Acting for You: Cross-User Memory Sharing for LLM Agents** · arXiv:2609.32511v1 · [primary](https://arxiv.org/abs/2609.32511v1) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/08_sharemem.pdf)

- **Read:** PDF pp.3–5, §§3.1–3.3,4.1 and beginning 4.2; method/splits/controls plus selected result context, not all 24 pages
- **Witness:** p.3 separate user preferences/local experience/shared experience; p.4 scope-first local/shared retrieval and environment-fixed user preference access; p.5 NONE/PREF/LOCAL/SHARE-ALL/SHAREMEM controls and offline-fixed versus full-reward online update protocols
- **Limits:** supplied environment scopes and preference access boundaries are part of evaluated setting Do not claim that merely adding organization IDs is novel or that cross-user sharing proves confidentiality of a new implementation
- **Claim links:** C03/C04, no-memory/retrieval/scope controls

## S05 AFTER

**Managing Procedural Memory in LLM Agents: Control, Adaptation, and Evaluation** · arXiv:2606.23127v1 · [primary](https://arxiv.org/abs/2606.23127v1) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/09_after.pdf)

- **Read:** PDF pp.2–5, §§2–3.2 and selected §4 setup/results; not all appendices/splits inspected
- **Witness:** pp.2–3 describes 382 workplace tasks/six roles and fixed task–skill annotations; §2.3/p.4 specificity/generality and task success metrics; §3.2/p.4 EVOLUTION trace/version/promotion/rollback interface; p.5 distinguishes static skill content and refinement/transfer experiments
- **Limits:** task–skill annotations fixed at definition separate skill quality from retrieval quality New benchmark construction reports expert refinement/review (pp.3–4); do not pretend our newly constructed plans inherit that expert validation Cross-task/role/model transfer already exists as research question
- **Claim links:** C03/C06, transfer separation and versioning prior work

## S06 PolicyBank

**PolicyBank: Evolving Policy Understanding for LLM Agents** · arXiv:2604.15505v1 · [primary](https://arxiv.org/abs/2604.15505v1) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/10_policybank.pdf)

- **Read:** PDF pp.5–8, §§4–6.1 and beginning 6.2; complete method and selected evaluation design; Figure 2/p.7 image inspected
- **Witness:** §4/pp.5–6 constructs clarifications and simplified/different-instance/complex sister tasks; §5/pp.6–7 initializes capability-level memory from policies/schema/tools and updates add/revise/omit from developer reward+explanation; §6.1/p.8 injects sister tasks immediately after parents, uses same ordering and memory baselines with adapted retrieval
- **Limits:** evaluation intentionally exploits specification–requirement gaps in airline/retail tasks with manually formulated clarifications This is strong collision with feedback-driven organization learning, but immediate sister-task transfer is not distant family-disjoint patent-project evidence Policy interpretation here cannot license an agent to rewrite our approved hard constraints by itself
- **Claim links:** C03; include PolicyBank-style method if claiming a new policy-learning mechanism

## S07 ESCROW

**ESCROW: Guarded and Dual-Objective Continual Maintenance for Agents in Policy-Governed Enterprise Workflows** · arXiv:2608.01772v2 · [primary](https://arxiv.org/abs/2608.01772v2) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/11_escrow.pdf)

- **Read:** PDF pp.3–6 (§§3.1–3.6 and §4.1), p.20 (D.3), pp.31–32 (J; p.31 also contains end of theoretical discussion) Selected text/algorithm/captions, not all 39 pages or all numerical claims
- **Witness:** p.4 linked policy skills/structured cases, continuous human/trajectory/policy feedback and retrieved scope; p.5 guarded scoped mutation and persistent regression sample/anchors; p.6 accuracy–cost frontier and proprietary FinDAS setup; D.3/p.20 distinguishes executable feedback from read-only experiential advice and says advice did not contribute measured numbers; J/p.32 states no code/data release and evaluation-cost limitation
- **Limits:** paper-reported primary setting is one proprietary financial workflow; public transfer probes preliminary (J/p.31) Release status statement is version-specific, not a new exhaustive repository search Do not import its operational expert feedback as something our project possesses
- **Claim links:** C02/C03/C04, scoped changes/cost/regression already prior work

## S08 GCJR

**Localizing Emergent Failures in Agentic AI: Recovering Minimal Repair Families via Counterfactual Replay** · **arXiv:2608.29228v2** · [primary](https://arxiv.org/abs/2608.29228v2) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/12_gcjr.pdf)

- **Read:** all five PDF pages including references; §II/p.2 figure and equations visually inspected
- **Witness:** §I/p.1 explicitly oracle-assisted, no automatic repair-message generation; §II.A/p.2 replay replaces candidates with paired clean messages; §II.B/C/p.2 graph-feasible singleton/pair domain and conditional exactness; §III/p.3 symbolic DAG/arithmetic pilot and missing-edge boundary test
- **Limits:** success localizes repair events under a matched-clean intervention backend It is not evidence that PTP can autonomously generate correct repairs Exactness requires declared domain/fixed replay outcomes and adequate dependency graph; no numeric saving is transferred to PTP
- **Claim links:** C02; source correction from earlier v1 references: G02 uses actual local v2 only

## S09 Programmatic Search Agents

**Programmatic Search Agents: Extending Agentic Search Beyond Query Reformulation** · arXiv:2610.06689v1 · [primary](https://arxiv.org/abs/2610.06689v1) · [local PDF](../../literature-review/pdfs/01-adaptive-agents/06_psa.pdf)

- **Read:** PDF pp.4–5, §§3–3.3, method/Figure 3 caption; experiments not re-appraised
- **Witness:** persistent candidate workspace, executable composition of retrieve/filter/rerank/extract/dedupe, source IDs and query provenance, selected observation separated from retained workspace
- **Limits:** reuse of candidates/selective evidence presentation already exists No claim about PTP cost gain or across-project organization learning follows from this method description
- **Claim links:** C02 mechanism/search comparator boundary

## S10 ReformIR

**When More Reformulations Hurt: Avoiding Drift using Ranker Feedback** · arXiv:2605.00560v1 · [primary](https://arxiv.org/abs/2605.00560v1) · [local PDF](../../literature-review/pdfs/02-patent-ai/28_reformir.pdf)

- **Read:** PDF pp.2–4, motivation/§3–3.3 and Figure 2 caption; no numerical-result verification or venue re-verification
- **Witness:** reranker feedback anchored to original query, reformulations as surrogate-model features, candidate BM25 pool, budgeted feedback/adaptive weighting
- **Limits:** not a source of our confirmed organization-policy feedback Retrieval relevance teacher is a proxy for that task, not new clinical/scientific plan gold Running header is a template; G02 cites arXiv version, not an inferred proceedings citation
- **Claim links:** C02, no query-expansion/adaptive-feedback firstness

## S11 ALCE

**Enabling Large Language Models to Generate Text with Citations** · EMNLP2023 proceedings PDF · [primary](https://aclanthology.org/2023.emnlp-main.398/) · [local PDF](../../literature-review/pdfs/03-evaluation/23_alce.pdf)

- **Read:** PDF pp.3–4 = printed pp.6467–6468, §3/§§3.1–3.3 and figure captions; not new human-study/appendix appraisal
- **Witness:** separately measures fluency, correctness and citation quality; correctness references/proxies differ by task; citation recall/precision use NLI entailment checks rather than citation existence alone
- **Limits:** an NLI-based attribution proxy is not independent clinical/legal/engineering truth Source existence/locator integrity is weaker than source support; report distinct metrics
- **Claim links:** C05/X02

## S12 CheckList

**Beyond Accuracy: Behavioral Testing of NLP Models with CheckList** · ACL2020 proceedings PDF · [primary](https://aclanthology.org/2020.acl-main.442/) · [local PDF](../../literature-review/pdfs/03-evaluation/24_checklist.pdf)

- **Read:** PDF pp.2–3 = printed pp.4903–4904, §2/§§2.1–2.3 and figure captions; not full user-study appraisal
- **Witness:** minimum-functionality, invariance and directional expectation tests; relation-based checks can operate without each perturbed example's independent label
- **Limits:** preconditions/task relevance of transformation still matter Relations can be consistently wrong without literal/explicit-contract checks Do not call behavioral testing itself our novelty
- **Claim links:** C05/C06/X01

## S13 SkillOpt

**SkillOpt: Executive Strategy for Self-Evolving Agent Skills** · arXiv:2605.23904v2 (25 May 2026) · [primary](https://arxiv.org/abs/2605.23904v2) · [local PDF](../../literature-review/g02-additions/pdfs/skillopt_2605.23904v2.pdf) · [official code](https://github.com/microsoft/SkillOpt)

- **Read:** first-page title/affiliations visually; methods PDF pp.4–6 (§§3.1–3.7), analysis/transfer/cost pp.12–16 (§§4.3–4.5/§5), protocol/algorithm pp.21–22 Not every appendix/table or every reported performance cell verified
- **SOURCE_REPORTED:** train/selection/test separation, bounded trajectory-driven skill edits, validation acceptance and portable best_skill.md; target frozen Training cost separate from deployed optimizer calls (§3/pp.4–6; §4.4/pp.14–15) Transfer tested in listed model/harness/nearby-benchmark settings (§4.3/pp.12–13)
- **INFERENCE/LIMIT:** does not establish PTP organization-policy/source-fidelity transfer; validation optimizes its scoring contract, not independent clinical truth No adoption of the paper's firstness claim or numeric gain as ours
- **PROPOSAL:** use existing optimizer as base/closest comparator under matched feedback/compute; test added domain safeguards separately (C03/C08) First-page affiliations Microsoft plus collaborating universities; code inspected as public documentation, not installed/run

## S14 HarnessOpt-Bench

**HarnessOpt-Bench: Evaluating LLMs at Harness Optimization** · arXiv:2608.06301v1 (6 Aug 2026) · **Scale AI**, not Microsoft · [primary](https://arxiv.org/abs/2608.06301v1) · [local PDF](../../literature-review/g02-additions/pdfs/harnessopt_bench_2608.06301v1.pdf)

- **Read:** first page visually; PDF pp.4–6 (§§3.1–3.2/experimental setup), p.11 (limitations) Not all reported rankings/appendices reproduced
- **SOURCE_REPORTED:** candidates include memory/prompts/tools/control-flow/code; fixed target model/environment/verifier; dev traces, aggregate validation and hidden test; candidate versions and target-evaluation budget (§3.1/p.5) Optimizer inference metered but uncapped in this study Limits include fixed-evaluator exploitation, seed dependence and Python/single-target setting (p.11)
- **INFERENCE/LIMIT:** memory-versus-code is not a valid separation from this search space Benchmark protocol is not a single new optimizer algorithm; no claim its domain gains establish PTP business/clinical utility
- **PROPOSAL:** borrow disclosure/version discipline, cap total optimizer+target costs for PTP and test patent-specific source/org-policy failure modes (C03/C08) No claim of novel generic harness optimization

## Context sources not newly re-appraised in G02

The remaining papers in the 35-source collection remain reading context at their previously recorded level FollowIR/IFIR/INSTRUCTIR/MAIR, other RAG/reflection papers, datasets/enterprise papers and metamorphic tools are not all method-reproduced here Existing [organization reading notes](../../literature-review/notes/30-35_organization_profile_reading.md) and [manifest](../../literature-review/manifest.json) provide their earlier review/access levels G02 uses them to distinguish task conventions, not to assert newly verified clinical/pharma capability labels

Paper53 is internal only under [provenance](../../literature-review/internal/PROVENANCE.md), outside this external source list and external manuscript bibliography Original 35-source PDFs/shared bibliography/manifest were not modified G02 downloaded only S13/S14 into its own literature directory with [separate manifest](../../literature-review/g02-additions/manifest.json), verified signatures/hashes/page/text/title and first-page images Both succeeded; no owner download help is needed
