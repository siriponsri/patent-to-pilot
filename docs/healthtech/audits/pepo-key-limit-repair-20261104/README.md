# แก้ key-limit blocker และส่งต่อ goal เดิม — 4 พฤศจิกายน 2026

## ผลที่ได้จริง

พบข้อผิดพลาดใน collector ไม่ใช่เหตุให้ล้างบัญชี API: `sanitize_key()` ใช้ `.get()` จึงทำให้ absent field กับ explicit nullเหลือรูปเดียวกัน หลังแก้ให้เก็บ field presence และตีความตามเอกสาร provider ได้ตรวจ `/api/v1/key`จริง **หนึ่งครั้ง** เมื่อ `2026-11-04T10:26:20.665295+00:00` (17:26:20ไทย) HTTP200, key scopeตรงE2, `limit`และ`limit_remaining`มีอยู่จริงและเป็นnull จึงเป็น **UNLIMITED** รายการbudgetsว่างและeffective_budgetเป็นnullอย่างexplicit

raw response SHA256ตรงกับR13ทุกตัว (`e84b6015e81e54607537040502062eb3a7b5b5f704bdf7565adac8ac99775521`) จึงมีหลักฐานเพิ่มเติมว่าข้อสรุป KEY_LIMIT_UNAVAILABLE ในR13/R21ไม่ใช่ความหมายที่ถูกต้องของคำตอบนั้น เก็บreceiptเก่าไว้ตามเดิมและแก้การตีความที่entrypointปัจจุบัน ไม่เขียนประวัติทับ

มีการ refresh key metadata แบบ read-only อีกครั้งเมื่อ `2026-11-04T17:57:37.583397+07:00` ถึง `17:57:38.080978+07:00` (10:57:37–10:57:38 UTC) จาก `.env` เดิม ผล HTTP200, key scope และ raw response hash ตรงเดิม, `UNLIMITED` ยืนยันซ้ำ และเก็บ receipt sanitized ไว้ที่ `metadata-observation-v2-resume.json` การ refresh นี้ไม่ใช่ account-credit observation: `account_scope_binding` ยัง `NOT_RECONCILED`, `live_admission_enabled=false`, ไม่มี reservation หรือ paid call

UNLIMITEDหมายถึงไม่มีper-key credit cap ไม่ใช่เงินไม่จำกัด ไม่ใช่เครดิตบัญชีคงเหลือ และไม่แทนE2/guardrail/account rights การที่.envไม่แก้ตั้งแต่26ตุลาคมไม่พิสูจน์หรือหักล้างสิทธิ์providerฝั่งserver ส่วนวงเงินMCP$30เป็นคนละkey/configurationจากdispatch.env จึงไม่ใช้แทนผลสดของkeyนี้

แหล่งทางการที่ตรวจ4พ.ย.2026: [OpenRouter limits](https://openrouter.ai/docs/api/reference/limits) และ [current-key API](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) ระบุnullสำหรับunlimited และแยกaccount balance/per-key cap/applicable budgets ไม่ตีความis_free_tier=falseเป็นยอดเงิน

## แก้โค้ดและตรวจอย่างไร

1. `providers/metadata_observation.py`: receiptv2เพิ่มfield_presence; แยกUNLIMITED/LIMITED/EXHAUSTED/INCONSISTENT/UNAVAILABLE_FIELD_PRESENCE เก็บnegative remainingตามจริง และแสดงaccount/budget prerequisiteแยกกัน legacyv1ที่ไม่มีpresenceไม่ถูกยกระดับเป็นunlimitedโดยเดา
2. `providers/credit_from_metadata.py`: ฟังก์ชันและCLIออฟไลน์เชื่อมaccount observationที่ผูกกับkeyจริงเข้ากับmetadatav2 ตรวจreceipt hash,HTTPsuccess,provider/currency,scope,อายุไม่เกิน300วินาที,applicable budgets และเลือกtimestampเก่ากว่าเพื่อให้reservationguardนับexposureอย่างระมัดระวัง สร้างcredit snapshotv2ที่runnerเดิมใช้ได้ ไม่มีnetwork/key/ledger access ไม่มีauto-admit
3. เพิ่มtestsสองไฟล์ ตรวจexplicitnull/absent/finite/zero/negative/inconsistent,exhaustedworkspacebudget,stale/future/hashmismatch/wrongkey/legacy และCLIexclusivewrite/fieldallowlist

Final scoped regressions **172ผ่าน/0fail/0error/0skip** ครอบคลุมmetadata/credit join/APIgeneration/privatecasejournal/E2/ledgerbinding/provideradapter/recovery/adversarial admission คำสั่ง: `python -B -m pytest <selected-test-files> -q -p no:cacheprovider --tb=short --basetemp <fresh-private-test-dir> --junitxml <receipt>` ใช้isolatedLOCALAPPDATAและmockprovider ไม่มีการใช้เงินจริงในtests

ก่อนfinal: collector tests36ผ่าน, bridge11ผ่าน และชุดadmissionก่อนเพิ่มbridge161ผ่าน จำนวนเหล่านี้ซ้อนกัน ห้ามรวมเป็นจำนวนtestsทั้งหมด ประวัติfullsuite655ผ่าน/2skipเป็นผลLunaก่อนpatchนี้ ไม่อ้างเป็นcurrentfullsuite

## บัญชีและต้นทุน

SQLiteเปิดread-only: integrity `ok`, operationalattempts0,contexts0, legacy4callsรวม$0.0001464 ตรวจcanonicalepoch/legacyhashesผ่านและhashDBก่อนหลังตรงเดิม `d0041edaf8be80cf01f77be3333bc4c5568254e5e7e2b1151d45960ef6b8c1d2` ไม่มีreservation/retry/reset/newledger

คงprojectceiling$100สะสม,E2prospective$1 และunknownhistoryตามowner-acceptedcutover ไม่อ้างlifetimecapguaranteed ไม่มีGPU/modelgenerationใหม่ ค่าpaidAPIใหม่$0 มีเพียงread-onlymetadataGETหนึ่งครั้ง ไม่ขอmanagementkeyหรือแก้security/.env

## สิ่งที่มีแล้วและสิ่งที่ยังขาด

- MCPget-creditsมีหลักฐานเดิมจริง: totalcredits$10,usage$0.0001464,ผลต่าง$9.9998536 เมื่อ4พ.ย.06:58:56ไทย ไม่ต้องให้ownerค้นหลักฐานเก่าซ้ำ แต่ตอนdispatchต้องrefreshเพราะเกิน300วินาทีแล้ว
- Exactdispatchkeylimitปิดแล้ว: UNLIMITED ไม่ขอให้ownerเปลี่ยนlimitหรือสร้างkeyเพื่อแก้ปัญหานี้
- ที่ยังไม่ครบคือaccountobservationที่ผูกกับdispatchkeyและสดพอ Usageที่ตรงกันเป็นreconciliationcheck ไม่พิสูจน์ว่าMCPaccountกับ.envaccountเดียวกันด้วยตัวมันเอง ตัวobserverจงใจไม่สร้างaccountbindingจากความบังเอิญนี้
- Runtimeนี้ไม่มีOpenRouterMCPactionที่เรียกได้จากtoolinventory จึงยังrefreshget-creditsไม่ได้ เป็นcapabilityunavailable ไม่ใช่providerdenial ไม่สร้างhelperagent/credential/connectionใหม่เพื่ออ้อมข้อจำกัด
- หลังมีaccountscopebinding ให้refreshkeymetadata/routepricingเฉพาะตอนพร้อมdispatchภายในหน้าต่าง300วินาที แล้วผ่านexistingE2/rights/attemptrecoveryทั้งหมดก่อนcanary ห้ามหยิบreceiptเก่ามาเปลี่ยนtimestamp

**สิ่งที่ownerต้องทำเฉพาะถ้าLunaใช้MCPเดิมไม่ได้:** เปิดOpenRouterบัญชีที่ถือdispatchkeyใน.env แล้วให้ยอดcreditremainingพร้อมเวลาที่เห็นและยืนยันว่าเป็นบัญชีเดียวกับkeyนี้ ไม่ส่งkey/token/.env และไม่ต้องอนุมัติ$100/UUID/resetอีก ถ้าgoalเดิมเรียกMCPและพิสูจน์bindingจากconnectionที่มีได้ ก็ทำผ่านเครื่องมือนั้นได้เลย

## คำสั่งเชื่อมข้อมูลและรันต่อ

Account observationต้องมีข้อมูลจริง: `format=ptp-openrouter-credit-snapshot-v2`, `provider=openrouter`, `source=approved_integration`หรือ`owner_sanitized_snapshot`, UTC`as_of_utc`, `currency=USD`, `remaining_credits_usd`, `authorization_id=PTP-HT-OR-E2-20261103-USD100`, account_scopeที่แหล่งข้อมูลผูกจริง, และkey_scopeจากmetadata/E2 อย่าคัดลอกยอดเก่าหรือคิดaccountscopeจากmatchingusage ไม่ต้องกรอกkey_limitด้วยมือ

```powershell
$env:PYTHONPATH='src'
python -B -m patent_to_pilot.providers.credit_from_metadata --key-observation <fresh-key-v2.json> --account-observation <fresh-bound-account.json> --output <new-credit-v2.json>
```

CLIไม่เรียกproviderและไม่reserveเงิน Outputเป็นinputของ`run_openrouter_generation_evidence_pack.py --credit-snapshot`เดิม จังหวะdispatchยังต้องrefreshpricingและตรวจfrozenpack/sourceoutboundrights,exactroute/nonthinking,sharedinputs,finitebudget/totalreserveและno-duplicateattempts เก็บgeneratedoutputs/receiptsWindowsตามprivatejournalที่แก้ไว้แล้ว ห้ามรันunpairedAPIบนคนละevidenceแล้วอ้างcomparison

## Scientific และ journal boundary

เป้าหมายยังเป็นWorld Patent Information ตรวจmanuscriptปัจจุบันพบว่าคงnegativefindingB0b.662242เทียบB4.498802,realizedbudgetต่างกัน,development-only3cases/unjudgedlinksและไม่มีsemanticgold/finalholdoutไว้ ไม่relabelresultsหรือrerunmetricsที่ปิดแล้วเพื่อเพิ่มprogress Medicalscreen96queries/3061patentsและdenominator1920=983+937ยังยึดindependentauditเดิม

G0/G3และO1/O2engineeringมีหลักฐาน; G1/G2/G4ยังpartialscientific; G5operationalpotential; G6draftไม่submitted; G7offlinecandidateไม่publicrelease; G8future ไม่ปิดgoalเพราะtestsผ่าน คิวclaimtable/operationaltable/installที่Lunaทำแล้วคงCOMPLETEทั้งหมด ไม่สร้างREADYงานเดิมซ้ำ

WPIofficialpublisherprofileมีread-onlyreviewr12แล้ว ส่วนjournal-specificGuide/Aimsยังunverified ไม่ลองหลบ403หรือเดาข้อกำหนด ยังต้องownerreviewdeclarations/submissionขั้นสุดท้าย งานนี้ไม่เปลี่ยนเป้าหมายหรือผ่อนmeaningfulevaluation

## สถานะส่งต่อ

Resumegoalเดิม เงื่อนไขpaidbranchเปลี่ยนจากKEY_LIMIT_UNAVAILABLEเป็นPENDING_FRESH_BOUND_ACCOUNT_CREDIT ส่วนscientificholdout/publicationเป็นคนละdependencyจริง เปลี่ยนเฉพาะprojectdocuments ไม่ได้เปลี่ยนplatformgoalstateหรือส่งข้อความไปLuna Sessionruntimeยังunknown

Sourcechanges4ไฟล์และเอกสารที่เกี่ยวข้องเท่านั้น ไม่มีcommit/merge/push/delete เก็บdirtyงานอื่นทั้งหมด สำเนาpatchก่อนแก้และrawtestoutputsอยู่taskworkspace; sanitizedreceiptsและhashesอยู่โฟลเดอร์นี้ Privatefreshmetadataอยู่ `%LOCALAPPDATA%/PatentToPilot/healthtech/evidence/pepo-key-semantics-20261104/metadata-observation-v2.json`

## Promptสั้น

Resume goal เดิม อ่าน docs/healthtech/audits/pepo-key-limit-repair-20261104/README.md ก่อน R13/R21: keyใน.envยืนยันUNLIMITEDแล้ว ไม่ขอวงเงินkeyซ้ำ คิวofflineเดิม COMPLETE ให้refreshยอดเครดิตผ่านMCPเดิมและผูกบัญชีกับdispatch keyจากหลักฐานจริง ใช้ credit_from_metadata สร้างv2snapshot แล้วrefreshราคา/ตรวจrights/E2ก่อนcanaryแบบboundedและpairedตามprotocol เก็บผลWindows ไม่resetledger/งบ ไม่ยิงซ้ำ ไม่เปิดgoalใหม่ คงWorld Patent Informationและข้อจำกัดวิจัย หากbindingหรือเครื่องมือยังขาด ให้รายงานเฉพาะinputนั้นครั้งเดียว ไม่วนauditเดิม

