# Checkpoint, resume และ report ที่ตรวจต่อได้

## Canonical storage และ single writer

แผนอยู่ folder นี้ แต่ทุก execution/audit ของ goal ใหม่เก็บ sanitizedreceipts/report/manifest/continuation ใน `docs/healthtech/audits/<new-run-id>/` ตาม [audit convention](../../audits/README.md) Testtemp ได้ แต่ keyevidence ต้องกลับ repo ไม่ใช้ Codex/temp เป็น sole copy Largeweights/rawrestrictedtext/qrels/privateledgers/vectorbundles อยู่ permittedstorage พร้อม paths+hashes ไม่ publicGit

หนึ่ง controlplane ownsgoal/ledger/jobwriter ตรวจ existingcheckpoint/process-owned lock/leaseidentity ก่อน resume ไม่ตั้ง runID เพื่อ resetmoney/deadline Cachehit รายงาน originalgeneration/config/hash/cost จริง ไม่เรียก cachedoutput ว่ารันใหม่หรือคิดค่าใช้จ่ายจริงเป็นศูนย์ของประวัติ

## CHECKPOINT.json ขั้นต่ำ

บันทึก format/runID/parentGoal+parentaudit, start/currentcommit+working diffhash, branch/worktree/ownership, input/model/protocol/licensehashes, outcomes แต่ละตัว, authorizations พร้อม source/status, canonicalledgeridentity, settled/reserved/unknown billing, first_runtime_job_utc/deadline_utc, allocationUUID+quotas, ownedjobidentity/heartbeat/status, completedshards/failedrows, resourcebytes/tokens/calls/time, lastfailure/retrycount และ nextactualcommand

Checkpoint ต้อง atomic และ appenddurableattempts ก่อน sideeffect จัด raw+summaryversions ไม่ overwritehistoricalreceipts ก่อน retry ที่ outcomeuncertain ให้ดู providergeneration/jobstate ก่อน กรณี unknown billing คง reservation; cancelack ไม่แปลว่าค่าใช้จ่ายหาย

Status ต่อ outcome ใช้ READY/ACTIVE/PARTIAL/COMPLETE/BLOCKED_LOCAL/NOT_RUN พร้อม evidence ไม่ rollupCOMPLETE เพราะ unit tests สีเขียวหรือ runtime ครบ 24h Modelchange/newcontext เป็น condition ใหม่มี parenthash ไม่ mixshards/output; deadline และ budget ของ goal เดิมยังคงเดิม

## Meaningful checks / resumability

- Localjobs: idempotentduplicate-submit, durableprogress, crash/restart, cancellationack, no-lost-history, expectedversionconflict และ selected-versionexports
- Budget: ledgerpathsubstitution, concurrentreservation, token/retryupper bounds, unknown billing/cancel/timeouts, price/providerchange, stalepricing, budget exhaustion และ UIclientbypass failclosed ไม่ใช้ realAPI ทดสอบ boundary
- Vector: actualremoteencoding+namedtransfer/localimport, partial/finalcommitcrash, lockcontention/crashrelease, source/model/config/orderhashes, duplicate/missing/swap/nonfinite, interruptedresume/no-reencodingproof และ compatiblelocalqueries
- Scientific: declaredeligibledenominator/unjudgedpolicy/grouping/frozen protocol, correctedrawrankmetrics/per groupresults, actualresourcecosts ไม่มี forcedadaptivewin
- Realbrowsercases: startbackendjob จนเห็นจริง, inspectsource, edit/reloadhistory, JSON/TH/ENexport และ controlled cancel ของ ownedjob ไม่ใช้ simulationstand-in

รัน checks ตาม changes และ requirements เลือก explicitfreshbasetemp ไม่เปลี่ยน ACL/globalconfig ไม่เพิ่ม testcounts เพื่อให้ดู complete Finalcommittedcandidate ต้องตรวจ source hash สัมพันธ์กับ measuredrun ส่วน docs-onlycommit ภายหลังบันทึก relation ไม่ต้อง paidrerun

## REPORT_TH.md template

1. Executive outcome: O1/O2/O3/O4 statuses, exactscope/base/finaltestedcommit, changedpaths, actualvsplannedvsNOT_RUN และ remainingblockers
2. Product walkthrough: nameddevice→HTTPjob→retrieval/evidence→generation→source/edit/history/export; provider selection/status/costs; captures และ artifactreferences แยก functionalengineering จาก usability/businessvalidation
3. Data/model: immutableIDs/revisions/hashes/rights/actualcounts/bytes, cohort/groups/splits/selfpolicy, model/prefix/pooling/projection/chunking และ trainingoverlaplimits
4. Research: primaryendpoint/fixed budgetdefinition/freeze, fixed/multiquery/heuristic/controller comparisons, generationpairedfrozen evidence, per query/grouprawresults, intervals/effective N/failures/negative findings; no model-onlyleaderboardclaim
5. Resources: preparationvsfirst runtime/deadline, GPUUUID/minutes/peakVRAM, CPU/RAM/time, Windows+remote+transferstoragecopies, retries/OOM/cancel/cachelineage
6. Money: originalcumulativeUSD8, historicalsettled, thisrunsettled, reserved/unknown, reconciledremaining, price/routecataloghash/time, generationIDs และ reservationevidence ที่ sanitize แล้ว ไม่เปิด privatejournal หรือ secret
7. Quality/policy: schema/locator/spans, unresolved/abstention, provider outbound rights, NCcommercialexclusion, actualtestcommands/outcomes/skipreasons, failuresrecovered และ uncertainoutcomes
8. Git: branch/pushedSHA/PR/checks, currentmergeauthority, concurrentworkpreserved, stagedlicense/secret checks; nomergeclaim ถ้ายัง pending
9. Nextactions: exactnext command/inputs, blockedaction+target+reason+completedindependentwork และ denied/pending/uncertainstate ไม่ขอ owner เลือก naming หรือ batch ทุกครั้ง

## BUDGET_EXPANSION_REQUEST_TH.md template

เขียนเมื่อ paidcap/remaining ไม่พอหรือ variance บอกว่าต้องเพิ่ม ไม่ใช้เป็น automaticexecution:

| Field | ต้องกรอกด้วย actual หรือระบุ UNKNOWN |
|---|---|
| Current authority | oldround1USD8, settledtotal, reserved/pending, remaining และ reconciliationtimestamp |
| Evidence gained | exactdataset/groups/method/model/pilotresults/failures/cost/latency/uncertaintylimits |
| Proposed added study | hypotheses, independentnew groups/conditions, proposedN/endpoint, frozen protocolchange และเหตุผลที่ไม่ใช่ repetitivegrid |
| Value/power | usefuldecision ที่ผลจะเปลี่ยน, MDE/pairedvariance/power เมื่อข้อมูลพอ; ถ้า n เล็กให้ descriptivefeasibility แทน inventpower |
| Maximum added cost | exactprovider/rate/tokens/retries/callcounts+margin, worst-caseUSD และ resourcehours/storage ไม่ใช่เฉพาะ average |
| Alternatives | smallerlocal/offlineanalysis, sample/condition ลดลง และ information ที่เสีย |
| Decision required | requestedadditionalcap/conditions/stoprule; PENDING_OWNER_APPROVAL จนมีคำตอบ ไม่ topup/ซื้อเอง |

## Final closeout / stop

เมื่อ 24h หรือ allocationwindow หมดให้หยุด ownedcompute อย่างปลอดภัย checkpoint แล้วส่งสิ่งที่ครบ ไม่ reset เวลา ส่วน offlineanalysis/docs ที่ได้รับอนุญาตทำต่อได้ Paidcap หมดให้หยุด paidcalls ก่อนเกิน ดำเนิน localbranch ต่อ ไม่แก้ globalpermissions เพื่อผ่าน

ส่งหนึ่ง canonicalsummary พร้อม linkedrawreceipts ไม่สร้าง receipt-onlyloops หากยังทำ actualoutcome อิสระได้ให้ทำก่อนขอ approval การทำ goal รอบนี้ไม่ใช่การประกาศ publication/clinical/FTO/commercial readiness และไม่ให้สิทธิ์ติดต่อ participants/deploy
