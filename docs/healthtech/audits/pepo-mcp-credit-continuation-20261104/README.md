# ทำไมยัง BLOCKED และ owner ช่วยอย่างไร — 4 พฤศจิกายน 2026

**ใช้ goal เดิมต่อ** สิ่งที่ขาดอยู่เป็นข้อมูลและเครื่องมือของ paid branch ไม่ใช่เหตุให้เริ่มงานวิจัยหรือบัญชีค่าใช้จ่ายใหม่ การเปิด session ใหม่อาจช่วยถ้าใช้ host/connectionที่มี OpenRouter MCPจริง แต่ยังไม่ได้ทดลองและรับรองไม่ได้ว่าการเปิดใหม่อย่างเดียวจะเพิ่มtoolsให้

## สถานะที่ตรวจจริง

- HEADยัง88dc404 และdirtyงานทั้งหมดรักษาไว้ ล่าสุดLunaมี `metadata-observation-v2-resume.json` เมื่อ17:57:37ไทย ยืนยันkeyเดิมUNLIMITED แต่ไม่มีaccount binding/credit observationในreceiptนั้น
- Runtimeปัจจุบันค้นtool inventoryแล้วไม่มีOpenRouter/get-creditsที่เรียกได้ และ `Get-Command codex` ไม่พบCLIบนPATHของshellนี้ เป็นavailability limitation ไม่ใช่การที่OpenRouterปฏิเสธcredentials ไม่อ่านsessionstores/configsecrets และไม่ติดตั้งtoolหรือสร้างconnectionเพิ่ม
- การค้นtaskผ่านเครื่องมือที่รองรับยังไม่ยืนยันexactLunagoal จึงไม่อ้างว่าidleหรือเปลี่ยนruntimegoalstate มีเพียงสถานะจากprojectdocuments/ownerreport ไม่มีการส่งข้อความหรือเปิดgoalใหม่
- MCPเคยget-creditsได้จริงเมื่อ06:58:56ไทย: credits10,usage0.0001464,เหลือ9.9998536ตามคำนวณ ประวัตินี้มีอยู่แล้ว แต่ใช้แทนยอดปัจจุบันไม่ได้ ไม่ขอให้ownerหาR1หรือยืนยันUNLIMITEDซ้ำ
- E2เปิดread-only integrity `ok`, attempts0,accountscope rows0,legacy4callsรวม$0.0001464; hashไม่เปลี่ยน `d0041edaf8be80cf01f77be3333bc4c5568254e5e7e2b1151d45960ef6b8c1d2` คงUSD100สะสม/E2prospectiveUSD1/unknownhistory ไม่สร้างaccountscopeในDBด้วยhelper

## แยกสาเหตุให้ตรง

| สิ่งที่พบ | หมายถึง | วิธีแก้ |
|---|---|---|
| NO_OPENROUTER_ACTION | sessionไม่มีtoolcallนั้นให้เรียก ไม่ได้แปลว่าaccountเงินหมด | ตรวจMCPบนhostที่ใช้จริง หรือใช้owner dashboard capture |
| UNLIMITED key | keyไม่มีper-key cap ไม่ได้แปลว่าcreditไม่จำกัด | คงbudgetguardเดิม ไม่ต้องสร้างkeyหรือเปลี่ยนlimit |
| account binding not reconciled | ยังไม่ได้ยืนยันว่าเครดิตที่อ่านมาจากบัญชีของdispatchkey | ownerยืนยันบัญชีจริง หรือintegrationที่มีหลักฐานscope |
| snapshot stale | เกิน300วินาทีของโครงการ | เก็บใหม่เมื่อเตรียมdispatchพร้อมแล้ว ห้ามแก้เวลาไฟล์เก่า |
| timestamp+07:00 | เวลาเดียวกับUTCแต่bridgeเดิมปฏิเสธรูปแบบ | แก้ให้แปลงawaretimezoneหลังhashcheck โดยไม่เปลี่ยนinstant/อายุ |

300วินาทีเป็นกติกาfreshnessใน`providers/credit.py` ไม่ใช่วันหมดอายุของkeyหรือข้อกำหนดให้เริ่มgoalใหม่ การมีconfigurationบนเครื่องก็ไม่พิสูจน์ว่าtoolsถูกโหลดในทุกhost/session

## ทางเลือกแรก: MCPเดิมในsessionเดิม

1. ในcomposerของsessionที่ใช้ทำงาน พิมพ์ `/mcp` ดูว่ามี`openrouter`เป็นconnectedหรือไม่
2. ถ้าเป็นlocaldesktop ให้ดูSettings → MCP servers ที่serverเดิม หากตั้งไว้แล้วใช้Restartของserverเพื่อโหลดใหม่ ไม่Addซ้ำ ไม่เปลี่ยนOAuth/securityให้เอง หากระบบขอAuthenticateให้ownerตรวจconnection/consentเองก่อน ไม่ส่งtokenมาในแชต
3. ขอให้sessionเรียก **get-creditsแบบread-only** หนึ่งครั้งเพื่อพิสูจน์toolsและบันทึกเวลาจริง อย่าใช้send-messageหรือgenerate-imageทดสอบ เพราะเป็นbillable
4. หากยังNO_OPENROUTER_ACTIONหลังตรวจhost/connection ให้หยุดลองซ้ำ ใช้ทางเลือกด้านล่าง หรือย้ายexecutionไปsessionที่พิสูจน์get-creditsได้จริง โดยรับช่วงgoal/worktree/E2เดิม

หากมีCodexCLIอยู่ในterminalของowner คำสั่งread-onlyคือ `codex mcp list` เพื่อดูserverstatus ไม่ต้องส่งconfig.toml,env,headersหรือcredentialsทั้งไฟล์ให้ใคร การที่CLIใช้ได้ไม่รับประกันว่าcloud/delegatedsessionอีกhostใช้configurationเดียวกัน

อ้างอิงทางการตรวจ4พ.ย.2026: [Codex/ChatGPT MCP configuration](https://learn.chatgpt.com/docs/extend/mcp) อธิบายconfigurationร่วมสำหรับclientsบนCodexhostเดียวกันและ`/mcp`/Settings/Restart; [OpenRouter MCP](https://openrouter.ai/docs/guides/overview/mcp-server) ระบุget-creditsและOAuthconnectionkeyแยกจากkeyอื่น หลักฐานนี้ไม่ยืนยันว่าnewgoalของownerจะได้toolsโดยอัตโนมัติ

## ทางเลือกที่ownerทำได้เลยโดยไม่ใช้MCP

เตรียมให้Lunaพร้อมทำadmission/canaryก่อน แล้วเปิดOpenRouterด้วยบัญชีที่เป็นเจ้าของkeyใน `.env` เตรียมหน้าSettings → Credits ยืนยันบัญชีจากข้อมูลการสร้างkeyที่ownerรู้ หากยืนยันไม่ได้ให้หยุด ไม่เดาจากยอดusageที่บังเอิญตรงกัน

เปิดPowerShellแล้วใช้คำสั่งนี้:

```powershell
Set-Location 'C:\Users\User\Desktop\myProject\_worktrees\patent-to-pilot-long-run-20261103'
$env:PYTHONPATH='src'
python -B -m patent_to_pilot.providers.owner_credit_capture --key-file 'C:\Users\User\Desktop\myProject\patent-to-pilot\.env'
```

คำสั่งถามสองอย่าง:

1. ยืนยันว่า.envkeyเป็นของบัญชีที่กำลังดู โดยพิมพ์ `SAME ACCOUNT` ถ้ายืนยันไม่ได้กดEnterเพื่อหยุดก่อนnetworkrequest
2. Refreshหน้าCreditsแล้วกรอก **available creditที่เหลือจริงเป็นUSD** เช่นรูปแบบ`9.12` ตัวอย่างนี้ไม่ใช่ยอดที่ระบบยืนยัน ห้ามกรอกtotalpurchased/usage/keycap/MCPcapแทนbalance และไม่ใส่key/token

helperจะเก็บเวลาจริงในUTC,อ่านเฉพาะnamedkeyผ่านcollectorเดิม,เรียกGET `/api/v1/key`หนึ่งครั้งโดยไม่retry,ตรวจkeyfingerprintกับE2แล้วสร้างcredit snapshot พร้อมownerattestation ข้อมูลบัญชีเป็น **owner-sanitized assertion** ไม่ใช่providerverifiedidentity ไม่มีการfabricatecreditหรือaccountverification ไม่มีการยิงโมเดล/จองเงิน/แก้ledger/settings/สร้างcredentials

เมื่อสำเร็จterminalจะแสดง `READY_FOR_EXISTING_ADMISSION_CHECKS; NOT_DISPATCHED` และpathไฟล์ `credit-snapshot.json` อยู่ใต้ `%LOCALAPPDATA%/PatentToPilot/healthtech/evidence/owner-credit/<timestamp-id>/` ส่งให้Lunaเฉพาะpathนั้น แล้วให้ใช้ทันทีภายใน300วินาทีจากเวลาบันทึกหน้าdashboard พร้อมfreshpricing/rights/E2checks ไฟล์บัญชี/metadata/attestationเก็บWindows ไม่ต้องcopyไปdr-trainหรือGit

หากterminalขึ้นCAPTURE_STOPPEDจะมีsafeerrorcode หากsnapshotเก่า **อย่าแก้timestamp** ให้เตรียมขั้นอื่นให้พร้อมแล้วเก็บใหม่ การรันhelperไม่ใช่การอนุมัติให้ยิงAPIซ้ำหรือข้ามpending/unknownattempts ส่วนราคาของrouteยังต้องrefreshก่อนdispatchตามrunnerเดิม

วิธีนี้เหมาะสำหรับช่วยปิดcanaryหนึ่งรอบ หากจะทำlongrunต่อเนื่องควรให้sessionที่ทำงานเรียกMCP/accountintegrationได้จริง เพื่อrefreshอัตโนมัติเมื่อจำเป็น ไม่เปลี่ยนนโยบายให้เชื่อbalanceเก่าไปตลอด

## เปลี่ยนsessionเมื่อใด

เปลี่ยนได้เมื่อมีหลักฐานว่าsession/hostปลายทางเห็นOpenRouterMCPและเรียกget-creditsสำเร็จ แต่ให้เป็น **continuationของgoalเดิม** ใช้activeworktreeและcanonicalE2เดิม ไม่resetdeadline/งบ/history ไม่เปิดgoalวิจัยใหม่ ไม่รันworkerเดิมซ้อน หากทั้งเก่าและใหม่ไม่เห็นMCP การสร้างgoalใหม่ไม่ได้เพิ่มแหล่งเครดิต

รอบนี้ไม่ได้สร้างsessionเพื่อทดลองหรือแก้MCPglobalconfiguration จึงไม่มีผลยืนยันว่าการเปิดใหม่ช่วย ใช้userfallbackได้โดยไม่ต้องพิสูจน์สมมติฐานนี้ก่อน

## Codeและverification

เพิ่ม`providers/owner_credit_capture.py`พร้อมtests ใช้canonicalledgerแบบread-only/reuseexistingaccountscope ถ้ายังไม่มีscopeใช้stableowner-assertedaliasและบอกชัดว่าไม่ใช่provideraccountID ต้องมีexplicitownerconfirmationจึงไปต่อ

แก้`credit_from_metadata.py`เฉพาะtimestampของkeyobservationที่มีtimezone แปลง+07:00เป็นUTCinstantเดียวกันหลังhashverification ยังrejectnaive/future/stale ไม่ขยาย300วินาทีและไม่เขียนreceiptเก่าทับ Testsครอบคลุมequivalentoffset/staleness/naive,wrongkey,ownerไม่ยืนยัน,invalidbalance,exhaustedbudgets,nooverwrites,noretries,read-onlyscopeและmissingledgerห้ามสร้างใหม่

Finalscopedtests **188ผ่าน/0fail/0skip** (27focusedอยู่ในชุดนี้ ห้ามบวกซ้ำ) และentrypoint`--help`ใช้ได้จริง Rawlogsอยู่taskworkspace; sanitizedJUnit/verificationอยู่ที่นี่ ไม่มีการทดลองcaptureกับdashboardจริงในรอบนี้ ไม่มีproviderGETใหม่,paidcalls,reservations,GPUjobsหรือค่าใช้จ่ายใหม่ ตัวอย่างและtestsใช้mock/syntheticเท่านั้น

ยังคงWorld Patent Information,scientificprotocolและnegativefindingsเดิม ไม่เอาcredithelperหรือtestsแทนsemanticgold/finalholdout งานofflineที่Lunaทำครบแล้วคงCOMPLETE ส่วนpaidcomparisonยังNOT_RUNจนadmissionผ่าน และsubmission/publicreleaseยังเป็นคนละdecision

## Promptต่อgoalเดิม

Resume goal เดิม อ่าน docs/healthtech/audits/pepo-mcp-credit-continuation-20261104/README.md คิวofflineเดิม COMPLETE และkey UNLIMITEDแล้ว ให้ใช้MCPเดิมที่เรียกได้จริง หรือรอowner-credit/credit-snapshot.jsonจากhelper เมื่อได้ไฟล์ให้เข้าcredit/pricing/rights/E2 admissionทันทีโดยไม่วนaudit ให้ทำbounded paired canaryตามprotocolเมื่อผ่านทุกเงื่อนไข ไม่แก้timestamp ไม่resetledgerหรือgoal คงWorld Patent Information หากไฟล์เก่าหรือbindingยังขาดให้แจ้งเหตุเดียวที่ต้องแก้ ไม่ยิงซ้ำ

