# Solution Scout: committee demo storyboard (60–90 s; slide 8 of the IS2 deck)

Purpose: show K2b (what a patent searcher or R&D engineer gets) as a working translation layer. It is **not** evidence of
user benefit; that remains NOT_MEASURED.

## Run (local only, no network calls)
`.claude/launch.json`:
- `scout-backend` → `scripts/healthtech/serve_http.py` on port 8787, with the public-demo bundle and rationale book;
- `scout-frontend` → `frontend/healthtech-web/serve.mjs` on port 5178;
- open `http://localhost:5178/scout.html`.

Set-up, rights and limits: `docs/healthtech/audits/ptp-scout-public-demo-20261106/README.md`.

Licence note: the live demo encoder is patembed-large (CC BY-NC-SA 4.0), and the corpus is the public-demo HUPD-derived
bundle (CC BY-SA 4.0, personal names removed). This is acceptable for an academic, non-commercial committee demo. Any
commercial product build must swap to a commercially licensed encoder (roadmap §2).

## Script (60–90 s)
| t | Screen | Speech (Thai, short) | Label on screen |
|---|---|---|---|
| 0–10 s | Scout landing; click the recorded example "A small pump seal starts to leak …" (own field F04, F16 pre-filled; a free brief needs at least one own-field IPC class) | "เริ่มจากปัญหาทางเทคนิค ไม่ใช่ชื่อสิทธิบัตร" | REAL PUBLIC SOURCE – NOT TECHNICALLY VERIFIED |
| 10–30 s | Two lanes: own field vs other industries | "ระบบแยกผลในสาขาเดียวกับผลจากอุตสาหกรรมอื่น — ตรงกับโจทย์ OUT ใน B53" | same |
| 30–50 s | Open one cross-industry candidate: publication date, family, exact source passage | "ทุกข้อเสนอชี้กลับไปที่ข้อความต้นฉบับ ตรวจย้อนได้" | same |
| 50–70 s | Transfer rationale (quote-checked) and what is not covered | "เหตุผลการถ่ายทอดเทคโนโลยีผ่านการตรวจ quote; ส่วนที่ยังไม่ครอบคลุมแสดงชัด" | same |
| 70–90 s | Export the dossier with replay id and the human-review placeholder | "ผู้ใช้ตัดสินใจเอง ระบบไม่ใช่ legal/FTO" | HUMAN REVIEW: placeholder (no reviewer record yet) |

Fallback if the backend fails on the day: the synthetic replay bundle (`--scout-replay`), labelled SYNTHETIC DEMO, or a
screen recording made from the same build.

## Measured before the presentation (to be filled)
- [x] Backend and frontend start from `.claude/launch.json` on this PC. Checked 19 Nov 2026 with the recorded pump-seal example: Mode live, corpus 56,528, encode 760 ms, search 80 ms, paid calls 0; both lanes rendered (own field 10 / other industries 10), with transfer ideas and dossier download
- [ ] One full walk-through recorded (screen capture) as the fallback
- [ ] Every number shown on screen traced to the demo audit
