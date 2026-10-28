# HT-G3 Minimal No-Code Journey / เส้นทางใช้งานแบบไม่ต้องเขียนโค้ด

Status: `BACKEND_INTEGRATION_READY / UI_PENDING`  
Scope: local file-backed dossier inspection, annotation, history, and truthful export.  
This document is a bilingual integration contract, not evidence that the paused Claude frontend is complete.

## 1. Promise / คำมั่นของแพ็กเกจ

**EN** — An entrepreneur or investor analyst can start from a named public device/comparator, inspect source-backed facts, see candidate versus `disclosed_link` status, record uncertainty and next requests, save a local version, reopen it, detect a stale parent, and export a truthful dossier. No server, credential, provider, clinical conclusion, FTO conclusion, or automatic outreach is part of this local journey.

**TH** — ผู้ประกอบการหรือนักวิเคราะห์การลงทุนเริ่มจากอุปกรณ์หรือ comparator สาธารณะที่ระบุชื่อได้ ตรวจข้อเท็จจริงพร้อมแหล่งที่มา แยก candidate ออกจาก `disclosed_link` บันทึกความไม่แน่นอนและคำขอข้อมูลถัดไป บันทึกแฟ้มฉบับท้องถิ่น เปิดกลับ ตรวจ parent ที่ล้าสมัย และส่งออกแฟ้มหลักฐานตามจริงได้ โดยเส้นทางนี้ไม่ใช้เซิร์ฟเวอร์ ไม่ใช้ credential/provider ไม่สรุปผลทางคลินิกหรือ FTO และไม่ส่งข้อความอัตโนมัติ

## 2. Six-step journey / เส้นทางหกขั้น

| Step | English action | การกระทำภาษาไทย | Backend basis | Honest unavailable state |
|---|---|---|---|---|
| 1 | Choose a named public case | เลือกกรณีสาธารณะที่มีชื่อ | `DossierVersion.query`, public dossier JSON | No idea-to-comparator discovery; user must supply a named case |
| 2 | Inspect overview and mode | ตรวจภาพรวมและโหมดข้อมูล | `query`, `sources`, `evidence`, `RunManifest` | Public facts are not approval, validity, FTO, or investment merit |
| 3 | Open exact source/field basis | เปิดแหล่งที่มา/ฟิลด์และ locator | `source_view(dossier, source_id, field)` | Missing or late source remains unresolved; no silent rebinding |
| 4 | Add a note or next request | เพิ่มบันทึกหรือคำขอข้อมูล | `append_user_edits(..., expected_parent_version=...)` | Source facts stay immutable; user text is separate |
| 5 | Save, reopen, handle conflict | บันทึก เปิดกลับ และจัดการ conflict | `save_version`, `load_versions`, `history_manifest` | Stale parent raises a conflict; never last-writer-wins |
| 6 | Export JSON / EN / TH Markdown | ส่งออก JSON / Markdown อังกฤษ / ไทย | history CLI `export`, `export_markdown` | Export is local/download-only; no email, PDF, DOCX, or service dispatch |

## 3. Current public cases / กรณีสาธารณะที่มีอยู่

The current local public package contains three facts-only dossiers. Their patent pools are empty, so the journey must show an explicit empty/unknown scope rather than fabricate candidates.

แพ็กเกจสาธารณะในเครื่องมีแฟ้มข้อเท็จจริง 3 กรณี โดยไม่มี patent pool ในแฟ้มเหล่านี้ จึงต้องแสดงขอบเขตที่ว่างหรือยังไม่ทราบอย่างชัดเจน และห้ามสร้าง candidate ขึ้นเอง

| Case | Sources | Evidence items | Candidates | Unresolved | Next requests |
|---|---:|---:|---:|---:|---:|
| K121849 / PleurX | 1 | 7 | 0 | 3 | 3 |
| K163345 / TVC Imaging System | 1 | 7 | 0 | 3 | 3 |
| K190167 / MitraClip G4 Steerable Guide Catheter | 1 | 7 | 0 | 3 | 3 |

Source basis is preserved in each JSON dossier and the corresponding English/Thai Markdown exports under `results/healthtech/public-dossiers-20261027-r3/`. These packages do not establish patent coverage because their patent inputs are empty.

ฐานแหล่งข้อมูลถูกเก็บไว้ใน JSON และ Markdown ภาษาอังกฤษ/ไทยของแต่ละแฟ้มที่ `results/healthtech/public-dossiers-20261027-r3/` แต่แพ็กเกจนี้ยังไม่พิสูจน์ coverage ของสิทธิบัตร เพราะไม่มี patent input

## 4. Data separation / การแยกชนิดข้อมูล

- **Source facts / ข้อเท็จจริงจากต้นทาง:** `sources`, `evidence`, immutable source hashes, revisions, jurisdictions, dates, and locators.
- **Candidate / candidate:** `PatentCandidate.association_status="retrieved_candidate"`; retrieval is not disclosure.
- **Disclosed link / disclosed_link:** requires a separate source-backed `patent_disclosure` evidence item; evaluator gold cannot promote a candidate.
- **User edits / ข้อความผู้ใช้:** `DossierVersion.user_edits`; exported separately under “User edits / การแก้ไขของผู้ใช้”.
- **Unknown/unresolved / ยังไม่ทราบ:** `unresolved_items` and `next_information_requests`; never converted to negatives.

## 5. Integration examples / จุดเชื่อมต่อ

```text
source_view(dossier, "<source-id>", "<field>")
append_user_edits(history_dir, {"audit-note": "..."}, expected_parent_version=2)
select_version(history_dir, 3)
export_markdown(selected, language="en")
export_markdown(selected, language="th")
```

The CLI path is:

```text
python -B scripts/healthtech/manage_dossier_history.py export <history-dir> <fresh-output-dir> --version <n>
```

The exporter writes `dossier.json`, `dossier.md`, `dossier.en.md`, and `dossier.th.md`. The output directory must be fresh, and the selected version is explicit or defaults to the latest.

## 6. Acceptance boundary / ขอบเขตการรับรอง

**PASS now / ผ่านแล้ว:** backend source viewer, facts-only public dossier inventory, editable user-edit storage, atomic exclusive version creation, expected-parent detection, simultaneous-writer regression, JSON/EN/TH export, unresolved items, next requests, and local synthetic smoke.

**PENDING / ยังรอ:** responsive browser UI, keyboard and screen-reader checks, 320 px/400% review, four themes, browser persistence/recovery, frontend acceptance screenshots, and Claude branch integration. These remain outside this Luna backend package because the owner paused Claude UX/UI and did not authorize a competing frontend.

**BLOCKED_LOCAL / ติดข้อจำกัด:** complete public-case patent coverage, Bridge rights/cohort/split, live HTTP job/history service, live provider calls, clinical/FTO analysis, deployment, and user/commercial validation.

## 7. Truthful handoff / การส่งต่องานตามจริง

This artifact is safe to hand to a frontend worker as a no-code local journey contract. It must not be relabelled as a completed frontend, service integration, scientific result, or investment/clinical conclusion. The current receipt remains `BACKEND_COMPLETE_UI_PENDING`.
