# DAPFAM พอสำหรับอะไร และต้องเพิ่มอะไรจริง

**DAPFAM อย่างเดียวไม่พอสำหรับเป้าหมายทั้ง Research+Business ของ Patent-to-Pilot แต่ไฟล์เดิมพอเริ่ม remoteembedding→localvectors ได้แล้ว** การขาด semanticexpertlabels ไม่ใช่เหตุหยุด compute pipeline

## Existing inventory ที่ตรวจ

| Resource | Actual/local evidence | Role และข้อจำกัด |
|---|---|---|
| DAPFAM | 3parquets รวม1,213,423,744bytes;45,336corpus/1,247queries/49,869qrels;all3SHA ตรง pinnedreceipt | Citation-derivedfamilyretrieval ไม่ใช่ nameddevice→patentsemanticgold;NC/SAresearch-only boundary |
| Currentdevicecomposite r4 | FULL11/DEV8/HOLDOUT3;31patents;38/25/13disclosedpairs;9/6/3groups | Known-linkrecovery/engineering ไม่ exhaustiverecall;small/previouslyobservedholdoutlimits |
| OtherAbbott/Boston/Stryker/Cook/Philips snapshots | Inventory/manifests/adapters มีจริง ดู cohort-inventory.json | Facts+marking/disclosurelinks;local/display/provider/redistributionrights ต่างกัน ไม่รับรอง component/claimscope |
| SciFact | Pinnedlocalrelease/evaluator/devbaseline มีใน repo;300devclaims/5,183docs ตาม receipts | Separateevidenceverification component;claimsannotationsCCBY4,abstractODCBy1,codeApache2 ตาม license;ไม่ใช่ devicepatentgold |
| Localmodels | 4ONNX/tokenizerfilesbytehashverified;encoder384dim | Baselinecompute พร้อม local ไม่พิสูจน์ GPUavailability หรือ modeladequacy |
| Bridge | Existingrepo ยัง BLOCKED_LOCALrights/cohort/split | ไม่แนะนำให้ retryaccess/ดาวน์โหลดซ้ำเพื่อเลี่ยง restriction |

## DAPFAM label semantics

Primary [author card](https://huggingface.co/datasets/datalyes/DAPFAM_patent/blob/main/README.md) และ [paper](https://arxiv.org/html/2506.22141v2) ระบุ family-levelcitation-derivedpositives และ IN/OUT ตาม IPC3overlap ไม่ใช่ medical/nonmedicallabels หรือ semanticentailment Samplednon-cited0 ไม่ใช่ exhaustiveirrelevance ทั้ง49,869qrels รวม positive และ sampled0 ห้ามรายงานทั้งหมดว่า positive gold

M42case-insensitivesubstringoverTA มี2,859corpus/86queryhits;836IN/65OUT เป็น positivepairs ที่ทั้งสองฝั่งผ่าน lexicalscreen ไม่ใช่901semanticdevice-patentpairs Generic คำเช่น valve/cell มี falsepositive/negative ได้

135query/corpusself-ID+identicalTA และ40positive self-qrels ต้อง resolveeligibility กับ pinnedofficialevaluationpolicy ก่อน parityclaims เริ่ม reportas-released กับ self-excludeddiagnostic แยกตาม protocol ห้าม dropnegatives/queries โดยเงียบ

Cardlicense **CC-BY-NC-SA-4.0** ต้องรักษา attribution/noncommercial/sharealikeconditions ตาม use จริง ไม่ให้ commercialproduct/release ใช้ rawdata หรือ derivedvectors โดยอัตโนมัติ [Files listing](https://huggingface.co/datasets/datalyes/DAPFAM_patent/tree/main) มีประมาณ1.21GB และ localcopy ครบแล้ว ไม่ต้องโหลดซ้ำ

## Complementary shortlist ไม่ใช่ shoppinglist ให้โหลดทั้งหมด

| Priority / source | Role ที่เพิ่มจาก DAPFAM | Size ที่รู้/ไม่รู้ | Rights/use/owneraction |
|---|---|---|---|
| **Now: existingFDAfacts+manufacturerdisclosures** | Nameddeviceidentity,facts,citations,dossierapplication,known-linkdiagnostic | Localsmallcohorts มีแล้ว;newsubsetbytes ขึ้นกับ inclusion | ตรวจ source-specificfields/clauses;publicpage ไม่ license;reuse ก่อน ไม่ต้องให้ owner โหลดเพิ่มเพื่อเริ่ม |
| **Now: existingSciFact** [officiallicense](https://github.com/allenai/scifact/blob/master/LICENSE.md) | Evidence/rationale/labelcomponent แยกจาก retrievalfamilytask | 5,183abstracts/ประมาณ1.4Kclaims;localreceipt มี | ใช้ pinnedlocalcopy officialtestlabels ไม่เปิด ไม่อ้าง hiddentestscore ไม่ต้องโหลดซ้ำ |
| **Conditional: PatentMatch** [authorproject](https://hpi.de/en/database-group/projects/data-integration-projects/web-science/paar-patent-analysis-and-retrieval/patentmatch/) / [paper](https://arxiv.org/html/2012.13919) | Claim↔prior-artpassagecorrespondence;เหมาะ testpassage/rerankerrepresentation ไม่ใช่ devicegold | Authorpage ประมาณ1.9GB;paper6Mpairsscale ไม่ใช่6Mdevices | Verifydatasetterms/version/downloadhash ก่อน;codeMIT ไม่ใช่ datalicense ExaminerXvsA(background)ไม่แปล unrelatedsemanticnegative หาก manualdownload จำเป็นให้ขอเฉพาะ verifieddatasetfiles+terms ไม่ส่ง owner ไปโหลดก่อนรู้สิทธิ์ |
| **Later: CLEF-IP edition-specific** [officialdownload](https://ifs.tuwien.ac.at/~clef-ip/download-central.shtml) | Standardpatentprior-art/passageretrievalevaluation | 2011 ประมาณ2.5MEPO+400KWIPOdocs;actualdownloadbytesUNKNOWN ให้ inspecteditionmanifest ก่อน | CC-BY-NC-SA-3.0researchboundary;large ห้าม downloadwholecollection เพื่อ audit/45Kpipelinepilot เริ่ม task-specificqueries/qrels/limitedpermittedcorpus ถ้า terms รองรับ |
| **Conditional: Bridge-MedDevKG** [authorrepo](https://github.com/myqqhub/Bridge-MedDevKG) / [paper](https://aclanthology.org/2026.acl-long.1611.pdf) | Closerdevice↔patentknownassociationtask | Released50Kbaselinevs698Kpaperuniverse;exports672/79vscompleteness585/74 ต้อง reconcile | Datasetlicense ยัง unresolved paper/headline“expert-verified”ต้องอ่าน appendixdisclosurederived/errorcaveats ไม่ promote เป็น semanticgold ห้าม bypass/retrydeniedsource |
| OptionalFiNE-Patents/otherpassagebenchmarks | Feature-to-patentevidencecloserrepresentationstudy | ยังไม่ verifynewpayloadbytes/rights ใน audit นี้ | มี related-paperpointer ใน repo ไม่สั่ง owner โหลดหรืออ้าง admissibility ก่อน sourcecheck ไม่ใช่ preconditionremoteembeddings |

PatentMatch และ CLEF-IP เป็น complement ด้าน patentretrieval/claim-passages ไม่ได้แก้ devicecoverage/real-userbusinessvalidation ด้วยตัวเอง ไม่ต้องหา“dataset เดียวที่แทนทุก goal”

## คำตอบว่าตอนนี้ต้องให้ owner ช่วยโหลดอะไร

**เพื่อ remoteembedding รอบแรก:ยังไม่ต้องโหลด dataset เพิ่ม** ใช้ DAPFAM3files ที่ hash ผ่านแล้วกับ localdevicecorpus และ models เดิม สิ่งที่ต้องระบุเพิ่มจริงคือ dr-trainhost/jobworkspace และ allocatedresourcewindow/GPUUUID หรือ CPUquota ที่ไม่ชน Podi พร้อม source-specificcontrolledremoteprocessingbasis

หากจะเพิ่ม passagererankerdiagnostic ค่อยให้ Luna ตรวจ PatentMatchterms+exactfiles/expectedbytes+checksum+role ก่อน ถ้าต้อง manualdownload จริงส่ง owner เป็นรายการเล็กหนึ่งชุดพร้อม URL/file/revision/destination/license ไม่ขอโหลดทุก benchmark หรือหา experts โดยไม่มี boundedresult ให้ตรวจ

Source-checknetwork ใน audit นี้เป็น publicprimarydocumentation เท่านั้น ไม่ดาวน์โหลด corpora หรือรัน inference Datasetrecommendations ต้องคง task/license/sizeunknowns เหล่านี้ ไม่ใช่ publication หรือ legalreadinesscertification
