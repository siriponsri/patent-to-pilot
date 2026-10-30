# HealthTech evidence dossier — edited export

**Synthetic engineering example**

> Evidence preparation for further review; no medical, legal or investment conclusion is provided.

| Field | Value |
|---|---|
| Device (raw / canonical) | UX-DEMO-001 (synthetic) / UX-DEMO-001 |
| Dossier ID / backend version | ux-synthetic-dossier / 1 |
| Local snapshot | snap-mvv1mujt-uvvwef3jl2v4 (acknowledged save in this browser) |
| Mode | synthetic_demo — Synthetic engineering example |
| Evidence cutoff | 2026-10-27 |
| Jurisdiction | US |
| Run | ux-simulated-run |
| Dossier SHA-256 (canonical) | 287757968b8d3b879cb64ecd62ec5a9ed28fd2bbdb08d86905cc6aebdd375e50 |
| Exporter | healthtech-web-markdown 1.0.0 (frontend renderer; not the backend dossier.md exporter) |

## Source evidence

| Evidence ID | Statement | Kind / basis | Source / revision | Locator | Quote or field value | Integrity check |
|---|---|---|---|---|---|---|
| ux-e-device | SYNTHETIC source field: SYNTHETIC demonstration comparator | Source fact / Source-reported fact | ux-synthetic-device / ux-authored-v1 | field:device_name | device_name = &quot;SYNTHETIC demonstration comparator&quot; | Source field and value matched — This check does not verify the conclusion |
| ux-e-disclosure | SYNTHETIC authored span demonstration. | Patent disclosure / Reported association | ux-synthetic-independent-disclosure / ux-authored-v1 | chars:0:125 | SYNTHETIC ONLY: the fictional UX-DEMO-001 record reports US99000002B2 as an association. This is authored demonstration text. | Exact source text matched — This check does not verify the conclusion |
| ux-e-unicode | SYNTHETIC authored span demonstration. | Source fact / Source-reported fact | ux-synthetic-unicode / ux-authored-v1 | chars:1:2 | 🙂 | Exact source text matched — This check does not verify the conclusion |

## Patent candidates

| Raw ID | Canonical ID | Association status | Source / revision | Disclosure evidence | Named scores |
|---|---|---|---|---|---|
| US 99000001 A1 | US99000001A1 | retrieved_candidate — Retrieved candidate | ux-synthetic-patent-a / ux-authored-v1 | Not supplied | authored_demo_rank=1 |
| US 99000002 B2 | US99000002B2 | disclosed_link — Source-backed disclosed link | ux-synthetic-patent-b / ux-authored-v1 | ux-e-disclosure | authored_demo_rank=1 |

_Not a freedom-to-operate, validity, clinical or investment conclusion._

## Unresolved items

- SYNTHETIC example only; real evidence and coverage are unknown.

## Next information requests (from the dossier)

- Request an independently sourced, dated real device-patent disclosure.

## Local request drafts (user-authored)

| Question | References | Intended role | Priority | Status |
|---|---|---|---|---|
| What dated source supports this association? | ux-e-disclosure | technology reviewer | Normal | Draft |
| ขอเอกสารเปิดเผยที่ลงวันที่ / Request a dated disclosure | Not supplied | Not supplied | Normal | Draft |

## Feature links (user-authored, not machine-verified)

- SYNTHETIC sensor: ux-e-device

## Edits stored inside the imported dossier (user_edits)

- review_note: ข้อความทดสอบการส่งออก / User note must survive export

## User notes (user-authored; source facts unchanged)

### ux-note-1 — about ux-e-device (review marker: Needs clarification)

> ยังต้องขอหลักฐานเพิ่มเติม / Request more evidence

### note-mvv1mmkv-178asv3ghzv1d — about dossier (review marker: Reviewed by me (user review only))

> RACE_B

### note-mvv1msjf-6zoz6n50mmxm — about dossier (review marker: Reviewed by me (user review only))

> EDIT_FROM_TAB_B

### note-mvv1mtil-upnt3w1qlri8a — about dossier (review marker: Reviewed by me (user review only))

> RACE_A

## Source manifest

- ux-synthetic-device: urn:synthetic:ux-synthetic-device; revision ux-authored-v1; US; 2026-10-27; sha256 65ae11daa06998a6b2daba3aeff3f74b062052ec0aa38cb380a9221bad2839f9; synthetic; rights note: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-patent-a: urn:synthetic:ux-synthetic-patent-a; revision ux-authored-v1; US; 2026-10-27; sha256 17c5d17d46fb16a8885af7bf0e566fbdce17137911e83e1c796c6f3a09270031; synthetic; rights note: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-patent-b: urn:synthetic:ux-synthetic-patent-b; revision ux-authored-v1; US; 2026-10-27; sha256 4f2042bba28f5fca61bf4a01aeca568293199207348aafb80341c5ffc4fffc2e; synthetic; rights note: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-independent-disclosure: urn:synthetic:ux-synthetic-independent-disclosure; revision ux-authored-v1; US; 2026-10-27; sha256 4bdf5ac7134e2257eb5242d4bcf4fdd2f45e75d7319ec383a400a0629e76afad; synthetic; rights note: Project-authored synthetic fixture; no real device, patent or disclosure.
- ux-synthetic-unicode: urn:synthetic:ux-synthetic-unicode; revision ux-authored-v1; US; 2026-10-27; sha256 dfdf39721a3e57d17bb6ed6503cfc8e6f1fef718c58e184d1ac1c903cbc20d39; synthetic; rights note: Project-authored synthetic fixture; no real device, patent or disclosure.

## Export scope

- Included: source facts with locators, candidates and status, unresolved items, dossier requests, local request drafts, feature links, imported user_edits and local user notes.
- Omitted: full source payloads and run events (use the recovery JSON for a lossless copy).
