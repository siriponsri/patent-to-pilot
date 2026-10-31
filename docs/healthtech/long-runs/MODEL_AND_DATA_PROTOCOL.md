# Model, data และ scientific protocol

## Shortlist ที่เลือกและหลักฐานภายนอก

| บทบาท | Exact model | เหตุผล/ขอบเขต |
|---|---|---|
| Required patent encoder | `datalyes/patembed-base` | Patent-specific model; 193M, final768d, max512tokens, English, NC-SA4; เป็นแกน patent condition ไม่ใช่ claim ว่าเหนือกว่าบน device task นี้แล้ว [Card](https://huggingface.co/datalyes/patembed-base), [PatenTEB paper](https://arxiv.org/abs/2510.22264) |
| Required multilingual bridge | `intfloat/multilingual-e5-base` | 768d/512tokens, MIT,รองรับ Thai ใน multilingual setting; ต้อง query:/passage:แม้ข้อความไทย [Card](https://huggingface.co/intfloat/multilingual-e5-base), [external report](https://arxiv.org/abs/2402.05672) |
| Controls | BM25 + historical MiniLM | Reuse pinned baseline ตาม actual representation ไม่ rename MiniLM เป็น PatEmbed และไม่ใช้ 256tokens เป็น semantic ceiling |
| Local generator/controller | `Qwen/Qwen3-8B` | Apache2.0, local-first; ตั้ง nonthinkingprimary และ boundedcontext/output [Card](https://huggingface.co/Qwen/Qwen3-8B), [Qwen3 report](https://arxiv.org/abs/2505.09388) |
| API generator | `qwen/qwen3-32b` | ExactOpenRouterslug, pinprovider/rate atcall; model cardApache2.0 [Card](https://huggingface.co/Qwen/Qwen3-32B), sameexternalQwen3report ข้างต้น |
| Optional challenger | `Qwen/Qwen3-Embedding-0.6B` | ไม่เป็น requiredthirdencoder เพิ่มเฉพาะถ้า devcriterion/hypothesis/resource ที่เหลือรองรับและไม่ลด coreacceptance [Paper](https://arxiv.org/abs/2506.05176) |

Paper references เป็นงานภายนอกของผู้พัฒนา ไม่ใช่ paper ของ owner และไม่ใช่ independentvalidation ของ Patent-to-Pilot นี้ Spec/model card และ repoimplementation ต้อง pinimmutable artifact ก่อน run ชุดเอกสารนี้ยังไม่ได้ดาวน์โหลดหรือสร้าง vector จาก shortlist Paper86 ใช้ background ได้ ไม่ใช่เหตุผลเลือก model โดยลำพัง

## Encoder correctness และ frozen representations

PatEmbed-base ต้องโหลดครบ SentenceTransformers modules: transformer→masked mean/prompt pooling→learned projection1024→768→declared normalization อย่าใช้ AutoModel mean pool 1024 แล้วอ้างว่าได้ released base embedding ตรวจ `modules.json`, `1_Pooling`, `2_Dense`, `config_sentence_transformers.json` ที่ pinned revision จริง คง mean/prompt pooling ตาม config ไม่ทำ CLS/lasttoken แทนเงียบๆ

Task/field prompts ของ PatEmbed เป็น nested configuration ไม่เอา dict ทั้งก้อนเป็น string Default task/field ยัง null ให้ระบุ exact prompt policy เองจาก runtime-known task ก่อน freeze ห้ามอ่าน qrel IN/OUT/relevance/gold เพื่อเลือก prompt/route ใช้ prompt สำหรับ patent retrieval ที่ประกาศล่วงหน้าหนึ่งแบบ หรือ explicit null baseline ที่ตรวจ runtime รองรับ หากเปลี่ยน prompt เป็น condition ใหม่พร้อม hash

Parent research ระบุ mean pooling ที่รวม prompt และ learnedDenseprojection สำหรับ base ให้ตรวจ/บันทึก `include_prompt` และ nestedtask/fieldresolver จาก artifact ที่ pin จริงก่อน encode ต้อง validateoutput768d และเทียบ releasedSentenceTransformerspath กับ adapter ไม่ใช้ card ตัวอย่าง AutoModel ที่อาจข้าม projection เป็นหลักฐานความเท่ากัน

E5 ต้อง prefix `query: ` สำหรับ query และ `passage: ` สำหรับ candidate แม้ไทย masked average pool แล้ว L2normalization ตาม card คง query/docmodel revision/tokenizer/pooling/projection/dimension/precision/chunkcontract ตรงกัน ห้าม mix768dvectors ของคนละ encoder เพียงเพราะ dimension เท่ากัน

Primaryrepresentation ใช้ samepermittedtitle+abstract/exacttextinput acrossencoders ก่อน longcontexttest ที่ 512tokens สอง requiredmodels ต้องมี truncation/tokencoverage report และ matchedchunkpolicy Chunkingextension แยก condition, stablechunk→document/familymap, aggregate/dedup ก่อน K; BM25textwindow และ indexingbudget ประกาศตรงกัน ไม่เพิ่มข้อมูลให้ method หนึ่งแล้วให้ credit กับ adaptation

English patent condition, Thai/multilingual query slice และ translated/paraphrase diagnostics รายงานแยก ไม่ใช้ Thai absence ใน PatEmbed card เป็นหลักฐานว่าผล Thai เป็นศูนย์ และไม่ใช้ multilingual support เป็นข้อพิสูจน์ Thai MedTech quality Translation/paraphrase ไม่ใช่ independent queries และไม่ใช้ gold ช่วยเขียน

Freeze full modelcommit/artifactSHA256/tokenizer/modules/prompt/confighashes,software/dtype,shardIDorder/textsource hashes,chunkaggregation และ query/documentnamespaces เก็บ local query encoder หรือ compatibleprivatequeryroute สำหรับ interactiveUI คำว่า compatible ต้องมี numeric/ranktests ไม่ใช่ dimension ตรงอย่างเดียว

## Data roles, rights และ provenance

DAPFAM เดิมมี 45336corpus families/1247queries/49869qrels รวม sampledzero rows เป็น citation-derivedprior-artdiagnostic ไม่ใช่ device-patentsemanticgold Existingrealdevicecohort วัด documentedknownlinks; FDAfacts เป็น source integrity; SciFact เป็น evidence/labelcomponent แยก Bridge เป็น conditionalmain เมื่อ rights/cohort/splits พร้อม ไม่ fabricateexpandedgold หรือ unjudgednegatives

ใช้ [existing dataset gap note](../../audits/pepo-audit-20261030T1330Z-db07982/DATASET_GAPS_TH.md) เป็น acquisitionqueue เฉพาะ source ที่เพิ่ม information ให้ task จริง ไม่ bulkdownloadallbenchmarks Quantity ไม่ใช่ completeness เก็บ registry ของ originalURL/release/acquisitiondate/source-date/licenseclauses/intendeduses/raw+canonicalIDs/hashes/bytes/family/companymapping/missingness/dedup และข้อจำกัด unknown

Research/noncommercial ใช้ PatEmbed และ DAPFAM ตาม NC-SA terms พร้อม attribution แต่ commercial/distribution registry ต้อง exclude NC assets/unknown rights/default restrictions ไม่ relicense author code/model/data รวมกัน MIT/Apache model ไม่ได้ทำให้ raw patent pages หรือ training/evaluator labels เป็น commercial-ready ประเมิน code+model+data+derivedvectors+outputs แยกการอนุญาต ไม่ bundlekeys/weights/rawrestrictedcorpora ใน publicGit

ไม่แต่ง project-code license ขึ้นเองหาก owner/repo ยังไม่ประกาศ Registry ต้องบอกแต่ละ asset ว่า research-use/display/API-outbound/redistribution/commercial ใช้ได้เพราะ clause ไหน พร้อม revision/date/hash และ attribution Commercialpreparation คือทำ exclusion/configuration path ที่ตรวจได้ ไม่ประกาศ commercialrelease สำเร็จในรอบนี้

HFdownloads เป็น weights สำหรับ local/remote-ownedcompute ไม่ใช้ HFInferenceProviders หรือ APIembeddings Windows เก็บต้นฉบับ snapshot และ manifest ก่อน copydr-train จด planned/actualbytes ทั้งสองเครื่องรวม temp/cache/duplicates ระบุ resumableallowlist/filesizes/free-spaceguard ก่อน download ไม่ executeunknownmodelcode/datasetscript

OutboundAPI ใช้เฉพาะ source/evidence ที่ policy อนุญาตการส่งให้ provider นั้น Publicpage ไม่เท่ากับ APIsharinglicense ถ้าส่วนใด local-only ให้ excluded จาก pairedpack ทั้ง local และ API เพื่อคง frozen context ไม่ส่ง patient/customer/privatejournals หรือ qrels/gold ออกนอก evaluator

## Evaluation design ที่ตรึงก่อน final

Primarygoal quality at fixed budget: ประกาศ eligiblequeries/corpus/grouping/K (proposal20 สำหรับ device), primaryresourcebudget unit+ceiling/matchingrule, failure/retryrules,endpoint/minimum effect จาก dev แล้ว freeze ก่อน untouchedstudy Indexingcost และ servingcost รายงานแยกทั้งหมด ไม่ถือ localcompute ว่าฟรีเพราะ API$0

คง B0a/B0b/B1/B2/B3/B4 shared candidate universe/actions/metadata/query-reformulationoptions และ reranker ถ้าใช้ แยก semanticsvscompany/assignee/explicitpatentIDs/sharedfamily sensitivity รวม stoppingablation กลุ่มที่ถูกดูผลเพื่อ dev แล้วไม่เรียกว่า untouched Controller เห็นเฉพาะ observablestate ไม่เห็น reference/countremaininggold

Known-link macroRecall@K คือ recovery ของ references ใน cohort ไม่ใช่ exhaustiverecall หรือ lowerbound อัตโนมัติ Unlisted เป็น UNJUDGED ห้าม precision/F1 ของโลกจริงจาก unjudgedasnegative DAPFAMsamplednon-citedzeros เป็น task label ตาม benchmark ไม่พิสูจน์ semanticirrelevance; freezeidentical-ID/self-matchpolicy จาก pinnedsetting และรายงาน diagnostic ถ้ายังไม่มี paritybasis

Evaluator ต้อง reject/diagnoseunknownquery/candidateIDs, duplicatecanonicalIDs ก่อน K, NaN/nonfinite/metricoutofbounds และเก็บ missing/failedqueries ใน denominator ตาม protocol ไม่ clamp เพื่อกลบบั๊ก Uncertainty ใช้ paireddevice/family-connectedgroups/companysensitivity ที่ข้อมูลรองรับ ไม่ใช้ pairrows/seeds/paraphrases เพิ่ม n Train/pretraining overlap กับ publicbenchmarksunknown จนมีหลักฐาน ไม่อ้าง clean-zero-contamination

Generation ใช้ frozenrawquery/evidence pack/order/locators/schema/instructions และ strictoutputbudget เดียวกัน primarynonthinking ตรวจ localchattemplate และ APIrouteparameter/outputmode จริง หาก providerhonormode ไม่ได้ห้ามเรียก matchedmode รายงาน model/backend/quantization/tokenization ความต่าง Local8BvsAPI32B เป็น systemconfigurationcomparison ไม่ใช่ causaldeploymenteffect

Primaryoutputchecks คือ JSONschema, IDs/spans/quotes/version/locator, unsupported claim/abstention/unresolved และ policyenforcement Deterministicliteralchecks ไม่เท่ากับ semantic/clinicalentailment ไม่มี extra paidjudgebydefault Optionalsame generator judge เป็น secondaryproxy ไม่ใช่ independent gold หรือ humanexpertreplacement มี failures/retries/cost/latency และ outputhash ครบ

ถ้า effective groups เล็กให้ descriptivepairedresults/intervalslimits ไม่ inventstatistical power หรือ publicationreadiness หากต้องขยายให้เสนอ new groups/datasets/labels ตาม existingpublishedsemantics ก่อน ไม่ทำ ownerexpertqueue เป็น mandatoryglobalgate
