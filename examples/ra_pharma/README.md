# RA Pharma dossier walkthrough

One fictional taste-masked tablet, three document specialists and one editable Thai reply, all on the local Windows Workbench. Every step is deterministic code. No model, network service or paid call is used.

## Run it

1. Double-click `Start-PTP.cmd` in the repository root, or run `.venv\Scripts\python.exe scripts\ptp_run.py --serve --open`. The PDF extra (`pypdf`) must be installed; the repository `.venv` has pypdf 6.21.4. Use `--data-dir <folder>` for a clean store.
2. Choose **แฟ้มทะเบียนยา** in the top bar, or **เปิดแฟ้มทะเบียนยา** on the start page.
3. Follow the steps below. Each button press stores a new numbered snapshot that can be reopened from **ฉบับที่บันทึกไว้และการเทียบ**.

| Step | Action | What you should see |
|---|---|---|
| 1. Before the correction | Leave skill `1.0.0` and press **สร้างแฟ้มฉบับใหม่** | The incoming letter is read: authority sender, number `ตย ๐๓๑๒/๒๕๖๙`, emblem position and 2.99 cm height, two requests, unsigned copy and missing enclosure marked uncertain. The checklist wrongly reports the applicant's dissolution as 96%. That value comes from Example 6 of the patent |
| 2. Correct the skill | In **ทักษะการอ่าน** press **ปฏิเสธ: เป็นข้อเปิดเผยของสิทธิบัตร**, **เสนอรุ่นทักษะจากการแก้ไข**, **ทดสอบกับชุดพัฒนาแยก**, then **นำรุ่น 1.1.0 ไปใช้** | Version 1.1.0 passes all five cases, with no errors against five for 1.0.0. Three cases use the separate inhaler family, two are dossier regressions |
| 3. Applicant report missing | Build again with skill 1.1.0 | The applicant result is **ยังขาด**. The candidate table shows why the patent's 96% was rejected. The reply says the report will follow and leaves the date for the signer |
| 4. Report supplied | Tick report 1.0 and build | The result is 91% from PDF page 2 of the report. In the reply, select **หลักฐาน** next to paragraph 1, then the report button: the page text opens with the quoted line highlighted and a link to the PDF page |
| 5. Compare | Open the history panel, pick the step 3 snapshot under **เทียบกับ** and press **เทียบสองฉบับ** | Only `reg.R-P54.applicant-result` changed. The patent example and claim rows are byte-identical |
| 6. Edit and export | Fill the reference number, press **บันทึกฉบับแก้ไข**, then **ดาวน์โหลด DOCX** or **เปิดหน้าพิมพ์** | An A4 company-letterhead draft with Sarabun embedded. Edited blocks turn yellow; blocks for the signer are blue |
| 7. Conflicting editions | Tick report 1.1 as well and build; choose 1.1 under **ฉบับรายงานที่ใช้** and build again | First **ขัดกัน** with both values and a red blocking sentence, then 89% with the operator choice recorded |
| 8. Other claim branch | Switch to claim 18 and build | The branch reads "does not meet, pending review". The applicant item is unchanged. Thai FTO remains open |
| 9. Replay | Reopen snapshot 1 and press **ตรวจซ้ำแฟ้มนี้** | Every citation resolves to stored bytes and skill 1.0.0 rebuilds the same content |

Choose the licensor letter under **หนังสือที่ได้รับ** to see the company-letter branch: company sender, logo at the top left, and the company-to-company template.

## Scripted check

```powershell
.\.venv\Scripts\python.exe examples\ra_pharma\walkthrough.py <out-dir>            # API walkthrough on a fresh store
<qa-python> examples\ra_pharma\walkthrough.py <out-dir> --render                    # also print HTML (Chromium) and DOCX (LibreOffice)
```

The script starts the normal launcher, runs steps 1–9 over HTTP and writes the snapshots, comparisons, replay checks, `reply.docx`, `reply.html` and `summary.json`. It exits 0 only when the skill passes, every replay matches, the branch change leaves the applicant item unchanged and the cited sentence resolves. Rendering requires QA tools that the Workbench itself does not need.

## Boundaries

The dossier is display data for a local engineering demonstration. The letter is a draft: issue, signature and submission belong to an authorised person. The claim chart is not an infringement or FTO opinion, and no Thai patent search or legal-status check was run. ACTD is recorded as technical guidance; the binding Thai FDA instrument is not linked. Only Thailand has a demonstration profile. The authority, applicant and results are invented. The [product receipt](../../docs/ra-pharma/product/RECEIPT-P1-P5.md) records the evidence, environment and gaps.
