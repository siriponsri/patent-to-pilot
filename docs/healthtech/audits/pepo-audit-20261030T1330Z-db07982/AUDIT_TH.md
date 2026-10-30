# Audit งาน Luna หลัง 889958e ถึง db07982

**Audit COMPLETE ตาม scope ที่ระบุ; backend/research handoff CHANGES_REQUIRED; โครงการยังไม่ COMPLETE**

Snapshot ที่ตรวจคือ `db0798276e3158b04131b4e910abc0a11511e94c` (M42 implementation `d42fc36a9bf238b4b14281e0961dc5e7aa55df31`) ตรงกับ local HEAD, origin/main และ anonymous remote refs/heads/main ตอนเริ่มตรวจ 2026-10-30 13:30 UTC รักษา `M AGENTS.md` เดิมและทุก dirty/untracked file ไม่มี implementation/SSH/GPU/provider execution ใน audit นี้

Owner แจ้งล่าสุดระหว่าง audit ว่า Claude UX/UI **ACTIVE** แล้ว ใช้สถานะนี้แทน paused context เดิม Branch/worktreemetadata พบ `claude/healthtech-ux-local-20261028` ที่96c63b1 ตาม path ใน Goal ไม่มีการแก้/switch/mergeUI Newstarter ระบุ **Goal ใหม่** เพราะ scope เปลี่ยนจาก M42coverage เป็น remote-vectorimplementation ไม่ resume oldsemantic gate โดยไม่เปลี่ยน objective

## ขอบเขตและแหล่งข้อกำหนด

อ่านข้อกำหนดปัจจุบันร่วมกับแชตต้นทาง [Pepo patent-to-pilot](https://chatgpt.com/c/6ae0869b-c23c-83ec-9dee-465b4e592612) ดู [SOURCE_CONTEXT_TH.md](SOURCE_CONTEXT_TH.md) แยก owner decisions จาก assistant proposals ผู้ใช้ระบุว่าไม่มี expert evaluators/organizational dataset และต้องการทั้ง Research กับ Business จึงไม่ควรสร้าง new expert-gold queue เป็น mandatory gate ของงานทั้งหมด

Inventory ครบช่วงที่ร้องขอ: **102 commits, 397 changed paths, 88 changed Python source/script/test files, 58 Luna audit folders** ดู commit/file/milestone inventories และ claim-evidence matrix ที่แนบ ความครบนี้หมายถึง inventory/receipt coverage ไม่ใช่อ้างว่าอ่านทุกบรรทัดของ 397 files หรือทำซ้ำทุก historical experiment ทำ deep review แบบแบ่งพื้นที่และ independent probes ใน integrity/budget, data/evaluator และ embedding architecture ไม่มีการใช้จำนวน tests แทน goal acceptance

## สิ่งที่ Luna ส่งมอบจริง

| กลุ่มงาน / milestone | สิ่งที่ source/receipts รองรับ | Independent audit scope / ข้อจำกัด |
|---|---|---|
| F1/F2/F3 และ M1/M15/M17/M32 | Evidence projection, frozen runtime/raw/registry checks, typed/legacy rights resolution และ adversarial tests | Focused 62 pass + 1 optional tokenizer skip; old defects แก้จริงใน routes ที่ตรวจ แต่พบ query metadata channel เพิ่ม |
| M2/M3, Stryker/Cook/Philips, family sensitivity | Acquisition/adapters, composite/family manifests, local baseline/reporting tooling | ตรวจ inventory/source/split counts; ไม่ redownload หรือ rerun neural experiments ทั้งหมด |
| M4/B4 controller/mock, R1 readiness | Strict action schema, bounded offline/provider-shaped mock, versioned8USD ledger | Source/mock tests ผ่านใน single-ledger path; ไม่มีหลักฐาน live LLM advantage และพบ multi-ledger cap gap |
| HT-T2 SciFact parity/lexical/errors | Component evaluator + deterministic dev baseline/error analysis | Re-score saved300predictions/5,183docs จาก labels จริง ได้ metrics ตรง savedscore ไม่สร้าง predictions ใหม่หรืออ้าง hidden test |
| Review packet/M23/M25/M24 | Source authorization/staging/judgment-ingest contracts | เป็น optional semantic-judgment branch มี work-order drift และ draft-stage blind spot ไม่จำเป็นก่อน embedding |
| M7–M12/M20/M21/M30–31 reports/G6 | Descriptive frontier, mock comparison, manuscript/budget artifacts | มี reuse/revalidation/docs-only commits จำนวนมาก แยกจาก new experiments; “untouched” claim ต้องจำกัด |
| M14/M19/M38/M40/M41 backend/G5 | Real source-backed dossiers, edit/history/export และ deterministic task analysis | Rebuilt aggregate จาก actual receipts 4/4 tasks,20/20 artifact hashes ตรง; engineering เท่านั้น ไม่ใช่ user study/business validation |
| DAPFAM preflight/BM25/M42 | Actual local parquets, qrel parsing, BM25 ranks และ lexical coverage | Independent file hashes/counts ตรง; evaluator duplicate weakness และ self-match policy ยังต้องจัดการ |

Current composite r4: **FULL11 / DEV8 / HOLDOUT3 queries**, 31-patent shared universe, **38/25/13** disclosed pairs และ **9/6/3** exact/family groups ทุก dev query มี reference ไม่ใช่เอา3unjudgedqueries มารวมเป็น judgeddenominator Older dev5 เป็นอีก vintage24patents ห้ามปน ส่วน G6 “Composite context8devices” ไม่ตรง full11 ปัจจุบัน ต้องแก้คำอธิบาย ไม่เปลี่ยนผลดิบ

## Independent verification

- **Headline: proper isolated clean Git checkout all-suite ที่ exactSHA =455 pass,3 fail,1 optional-tokenizer skip (459cases)**,0 network attempts/actual credential-file reads, source unchanged อีก3 failures คือ2 tests อ่าน ignored results และ1 fixture bytehash ผูก newline
- Git archive run ก่อนหน้า =454 pass,4 fail,1 skip; propercheckouttargeted4failures →1pass/3fail ก่อน rerunfullsuite Git-provenance failure หายเมื่อมี.git จึงเป็น archive-environmentartifact ไม่ใช่ productiondefect
- Focused integrity/budget suite อิสระ: **62 pass,1 optional tokenizer skip**,0 failures; mock transport/synthetic billing แยกจาก actual provider calls ซึ่งเป็น0
- Real DAPFAM parquets ทั้ง3 ไฟล์ hash ตรง pinned receipts: **45,336 corpus /1,247 queries /49,869 qrels**; positive24,929; lexical medical-screen corpus2,859/query86 และ both-screened positive pairs **836 IN /65 OUT** ทำซ้ำตรง
- Saved DAPFAM ranks:1,247uniquequeries,100ranks/query,ไม่มี duplicate IDs/nonfinite scores จึงยังไม่มีหลักฐานว่า reported scores พองจาก duplicate defect
- Local encoder/reranker ONNX/tokenizer4 ไฟล์ hash ตรง manifest; byte checks เท่านั้น ไม่รัน model
- SciFactsavedpredictions300rows re-score ตรง savedmetrics:abstract label-onlyF1=0.2037871957, sentence selectionF1=0.1070707071;gold/corpus/predictionhashes ตรง ไม่มี freshmodelinference
- Actual G5 aggregate:4passed/0failed,20artifact hashes ตรวจผ่าน ตรง savedanalysis ไม่มี participant/time-saving/paid-pilot evidence

ทั้งหมดเป็น offline tests/probes ไม่มี model/provider inference, SSH, GPU หรือ download ใหม่ Audit source-check network มีเฉพาะ Git remote metadata และ primary documentation แยกจาก inference counts เป็น0 Guard เป็น Python/process controls ไม่ใช่ OS packet capture

## Findings เรียงตามผลกระทบ

### F1 — P1 ก่อน live OpenRouter: cumulative cap ยังขึ้นกับการเลือก DBpath เดิม

`scripts/healthtech/run_b4_controller.py:313` รับ arbitrary `--budget-path`; `:156` เปิด Round1ProjectBudget; `providers/round1.py:138` ผูก policy ภายใน DB แต่ไม่ผูก authorization กับ canonicalpath ข้าม DB Independent offline probe สร้าง2DB authorization เดียว แต่ละ DB settle7USD ได้ รวม **simulated14USD** โดยไม่ breach ไม่มีการเรียก transport หรือเงินจริง นี่ไม่ใช่ข้อกล่าวหาว่า Lunaoverspend แต่ต้อง bind authorization→canonicalledger สำหรับ worker/resume ก่อน live ไม่ reset ประวัติ และไม่ใช้ปัญหานี้หยุด remote embeddings ที่ไม่พึ่ง OpenRouter

### F2 — P1 สำหรับ retrieval evaluation: DAPFAM duplicates ทำ nDCG เกิน1 และ unknownqueries ถูกมองข้าม

`scripts/healthtech/run_dapfam_bm25.py:186–214` รับ ranking `['P','P']` ต่อ referenceP หนึ่งตัว แล้วได้ **nDCG@2=1.6309297535714575** และไม่ rejectunexpectedqueryID ดู data-evaluator probes Current savedrankings ไม่มี duplicates จึงเป็น latent evaluator defect ไม่ใช่หลักฐานว่าคะแนน r3 ผิด ต้อง dedup canonical task IDs ก่อน cutoff/validateunknownqueries และ bounds โดยเฉพาะก่อน chunk→document/family vector aggregation

### F3 — P2: external field boundary ยังเหลือ query metadata

`healthtech/engine.py:297` serialize เริ่ม fullmodel แล้ว project เฉพาะ sources/evidence แต่คง `query.company_metadata.applicant` ซึ่ง adapterbind กับ company_source_id (`healthtech/abbott.py:445`) Authoredpolicyallow เฉพาะ trade_name ทำให้ source/evidence กรองถูกแล้วแต่ product_display/redistribution JSON ยังมี ABBOTT MEDICAL จาก restrictedapplicant ไม่มี realpublication เกิดขึ้น Probe แสดง generalizedfield-policy inconsistency ต้อง projectsource-derivedqueryfields ตาม origin/rights ด้วย ไม่ลบ localfacts หรือ user-authorednotes แบบเหมารวม

### F4 — P2: clean-checkout reproducibility regression/portability

`tests/test_healthtech_cross_cohort.py:22–33` อ่าน ignoredresults หลายไฟล์โดยไม่มี authoredfixture/opt-in ทำ2tests ล้มใน freshcheckout `tests/test_healthtech_integration_contract.py:17` ใช้ historicalcontract ที่ pinrawhash ของ G3journeyfile; `refresh_integration_contract.py:103` reject เมื่อ newline ต่าง Mainfile7911bytes/LF กับ checkout7987bytes/76CRLF มี text หลัง normalize เหมือนกัน แต่ hash ต่าง ต้องกำหนด fixture bytes/Git attributes หรือ testfixtures ให้ reproducible **ห้ามปิด hashvalidation หรือ resignmutatedproductiondata เพื่อทำให้ผ่าน**

### F5 — P2: work-order gate กว้างกว่าข้อกำหนดและเจตนา owner

M24 README:44/M26nextaction ให้ผ่าน M23→M25→M24 ก่อน reruncontrols ทั้งหมด ทั้งที่ GOAL:105 และ PLAN:37/580 อนุญาต existinggold/deterministicchecks โดยไม่มี newexperts M23schema แคบเฉพาะ semanticjudgment แต่ judgmentcontracts ยังรองรับ benchmark_gold จึงไม่ถูกต้องที่จะกล่าวว่าทุก row ต้องมี humanadjudicator ปัญหาคือ **ใช้ specializedsemanticbranch เป็น gate ของ known-link/component/embedding work ทั้งหมด** ให้คง validation สำหรับ claims ที่ต้องพึ่ง semanticlabels แล้วเปิด independenttracks ตาม originalgoal ไม่ fabricatesemanticgold

### F6 — P2 assurance: DRAFT authorization ยัง stage ได้

M23validator ยอม DRAFT และ M25stager เรียก validator นั้นแล้ว copyauthored12bytes สำเร็จ ดู `data-evaluator/authorization-probe-result.json` เป็น localhelperassurancegap ไม่ใช่หลักฐานว่า acquire ข้อมูลจริงโดยไม่ได้อนุญาต ควรแยก schema-validdraft จาก execution-approvedmanifest ชัด โดยไม่สร้าง ownerapprovalqueue ทุก publicdataset ที่ terms/authority มีอยู่แล้ว

### F7 — P2 scientific interpretation: “untouched final”เกินหลักฐาน

Stryker development scores ถูก commit ที่ `71c8d66` ก่อน composeholdout ที่ `dbcac2f` ปัจจุบัน `compose_multicompany_cohort.py:358/375` และหลาย reports ยังใช้ untouchedfinal อย่างกว้าง Fixed-policy descriptive transfer ยังมีประโยชน์ ไม่พบหลักฐานว่ามี tune-on-test แต่ไม่รองรับ globallyunseenfinaltest ต้องแก้ claim และใช้ newuntouchedgroups สำหรับ futureconfirmation ไม่ rename ข้อมูลที่เคยเห็นแล้ว

### F8 — ต้อง resolve ก่อน benchmark-parityclaim: self-family eligibility

พบ135query/corpusIDs ตรงกันและ title+abstract เหมือนกันทุกคู่ Savedranks มี self ทั้ง135 (134 อันดับ1,1 อันดับ2);qrels มี40positive self-pairs ข้อนี้เป็น **protocolambiguity ยังไม่ใช่ establishedofficial-evaluatorviolation** ต้อง pin official DAPFAM/MTEB self-ID policy ก่อนเทียบ score ใช้ sameeligibility กับ BM25/dense และ reportself-excludeddiagnostic โดยรักษา eligibledenominators ตาม protocol ไม่ drop ยากๆเพื่อทำ score ดี

Lower-priority libraryassurance: B4selectorconstructor ยอม pricinghash/time/provider ไม่ตรง policy แต่ CLI ปัจจุบันสร้างจาก file เดียวกัน ยังไม่ใช่ demonstratedCLIexploit รายละเอียดใน integrity-budget/FINDINGS.md ไม่ใช้เป็น gate หยุด embedding

## Remote compute ที่ owner ขอและ data sufficiency

ความหมายของ semantic ในคำขอรอบนี้คือ **embeddingcompute บน dr-train ผ่าน SSH แล้วนำ vectors กลับ Windows** ไม่ใช่ย้าย goldcreation ไป server CurrentSharedRetrieverencodeallcorpus ทีเดียว,CPUONNX256tokens/384dim,ไม่มี persistedvectorimport ส่วน productengine ใช้ FTS/lexicalapproximation อีกเส้นทาง ดังนั้นต้องต่อ shared/injectedretrievalseam ให้ทั้ง evaluation และ localdossierapp ไม่ใช่เพิ่ม standalonebenchmarkscript อย่างเดียว

DAPFAM พอเริ่มพิสูจน์ compute/vectorpipeline และ citation-familyretrieval แต่ไม่พอแทน MedicalDeviceproduct+devicepatentknown-links+evidenceverification+businessvalidation ดู [REMOTE_EMBEDDINGS_PLAN_TH.md](REMOTE_EMBEDDINGS_PLAN_TH.md) และ [DATASET_GAPS_TH.md](DATASET_GAPS_TH.md) ตอนนี้ยังไม่ต้องให้ owner โหลด bigdataset เพิ่มเพื่อเริ่ม vectorpipeline เพราะไฟล์ DAPFAM เดิมครบแล้ว

## Stopping/next action

แก้ smallconfirmedruntime/evaluator/portabilitygaps ตาม scope แล้วลงมือ remoteencoder→localvalidatedvectors→sharedretrieval/backenddemo ไม่มี newexpertgoldgate สำหรับ compute คง Bridge/semanticclaim/untouchedstudy/UI/customer/releaseblockers เฉพาะ branch ที่เกี่ยวข้อง NextGoal และ starter อยู่ run นี้ ไม่ได้ launchLuna/auditfix/deploy เอง

ข้อจำกัด audit: ไม่ rerun ทุก historicalneuralexperiment,ไม่ตรวจ privatebillingjournal/credentials,ไม่ต่อ SSH หรือ inspectGPU จริง,ไม่ได้ certifylegal/license หรือ publicationreadiness Every58auditfolder มี inventory แต่ deepreview/probes เป็น selectedscopes ตาม matrix
