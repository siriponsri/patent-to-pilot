# HealthTech local web frontend: runbook, acceptance and evidence

Status: **READY_FOR_REVIEW (local frontend slice)**. This is engineering evidence for a local, no-code TH/EN frontend. It does not complete HT-G3 or HT-G7, and no frontend PASS here implies scientific, user or market validation. Not merged, deployed or pushed. No live API, provider, paid inference or network fetch was used.

## สรุปสำหรับเจ้าของโครงการ

หน้าเว็บนี้รันในเครื่องได้ทันที รอบล่าสุดเปลี่ยนหน้าแฟ้มหลักฐานเป็นพื้นที่ทำงานแบบ node canvas คล้าย n8n หรือ Make แต่ละโหนดคือขั้นตอนที่รันจริงในเบราว์เซอร์ ตั้งแต่โหลดแฟ้ม ตรวจโครงสร้าง ตรวจ hash ไปจนถึงตรวจตำแหน่งอ้างอิง โหนดสว่างทีละขั้นตามงานที่ทำเสร็จจริง ไม่ใช่ภาพเคลื่อนไหวที่เขียนบทไว้ แผงทุกแผงปรับขนาด ย้าย หรือแยกเป็นหน้าต่างลอยได้ ลากการ์ดหลักฐานไปวางบนโหนดเพื่อจดบันทึกหรือร่างคำขอได้ และทุกการลากมีปุ่มหรือคีย์บอร์ดที่ทำแบบเดียวกัน

ด้านการนำทาง มีแถบห้าขั้น (โหลด ตรวจ ทบทวน ถามต่อ ส่งออก) ที่ขึ้นเครื่องหมายถูกเมื่องานเสร็จจริง มี breadcrumb ทัวร์แนะนำทีละจุด และวิดีโอสอนใช้ 56 วินาทีทั้งภาษาไทยและอังกฤษ สร้างด้วย HyperFrames จากภาพหน้าจอจริงของแอป แบ่งเป็นบทตามขั้นตอน วิดีโอยังไม่มีเสียง เพราะในเครื่องนี้ไม่มีแหล่งเพลงที่มีสิทธิ์ใช้ แต่เตรียมช่องใส่เพลงไว้แล้ว

ส่วนที่ยังเหมือนเดิม: บันทึกในเบราว์เซอร์ ปิดแล้วเปิดใหม่ข้อความยังอยู่ สองแท็บแก้พร้อมกันก็ไม่มีข้อความหาย และส่งออกรายงานไทยหรืออังกฤษที่รวมข้อความที่แก้ไว้ ผลทดสอบล่าสุดดูได้ที่ [ตารางผลทดสอบ](#test-commands-and-actual-outcomes) ส่วนการค้นข้อมูลจริง เอเจนต์ AI การแชร์กับทีม และบริการ backend ยังไม่มีในรุ่นนี้ โหนดและปุ่มที่เกี่ยวข้องจึงแสดงว่ายังไม่เชื่อมต่อ

## Branch, base and paths

| Item | Value |
|---|---|
| Branch | `claude/healthtech-ux-local-20261028` (isolated worktree `../_worktrees/patent-to-pilot-claude-ux-20261028`) |
| Base | `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3` (= `origin/main` when the worktree was created) |
| Candidate | the branch head; the evidence receipt records the commit it ran against in `candidate.head` |
| Owned new paths | `frontend/healthtech-web/**`, `docs/healthtech/ux/implementation/**` |
| UX pack | `docs/healthtech/ux/*` copied **unchanged** from the untracked pack in the shared checkout; combined sha256 of the sorted per-file hash list `5dda5ca6…749e` identical before/after copy |
| Read-only, served not copied | `schemas/healthtech/{DossierVersion,RunManifest,AcquisitionEvent}.schema.json`, `docs/healthtech/ux/fixtures/ui-fixtures.json` (explicit server allowlist) |
| Not touched | `src/**`, `scripts/**`, root config/tooling, provider/budget journals, `GOAL.md`, `PLAN.md`, `docs/healthtech/progress.json`, `memory/next-actions.md` (control plane owns status updates) |

No frontend existed at the base, so `frontend/healthtech-web` was free; no path remapping was needed.

## Stack decision

A no-build static app: vanilla ES modules, no runtime or dev npm dependencies, no root `package.json` change. Node ≥ 22 runs the loopback-only static server and the `node:test` suite. Browser acceptance drives a locally installed Chrome/Edge over the DevTools protocol, using Node's built-in WebSocket. This needs no new tool installs and no network.

## Runbook

```bash
cd frontend/healthtech-web
npm start              # http://127.0.0.1:5178/  (PORT overrides; binds 127.0.0.1 only)
npm test               # unit/contract tests (node:test)
npm run test:e2e       # real headless Chrome scenarios; writes ../../docs/healthtech/ux/implementation/evidence/e2e/
```

| Variable | Use |
|---|---|
| `PORT` | static server port (default 5178) |
| `CHROME_PATH` | browser for `test:e2e` (default: Chrome, then Edge) |
| `HEALTHTECH_PUBLIC_RUN_DIR` | optional read-only CLI run folder (default: shared checkout `results/healthtech/public-dossiers-20261027-r3/K190167`); tests are skipped with `NOT_AVAILABLE` when absent |

Using the app:

- **Demo:** Home → *Explore a synthetic demo* (FX-01) or the empty-corpus demo (FX-02).
- **Import a completed CLI run:** Import → select `dossier.json` with, optionally, `manifest.json` and `acquisition_events.jsonl` from the same `run_dossier.py` output folder. Nothing is uploaded or executed.
- **Restore:** Import → select a recovery file exported by this app; it becomes a new local copy.
- **Labelled fault simulation (tests/demo only):** `?simulate=storage-denied` (FX-07) or `?simulate=quota` (FX-09), shown with a persistent banner.

Storage: projects live in this browser profile's IndexedDB (`p2p-healthtech-ux`). There is no cloud backup or sync. Clearing site data removes them, so download a recovery file to keep a copy.

## Architecture

| Module | Responsibility |
|---|---|
| [core/pyjson.js](../../../../frontend/healthtech-web/app/src/core/pyjson.js) | Lossless JSON (keeps `1.0` vs `1`, big ints), Python-identical canonical dumps and `content_hash` |
| [core/validate.js](../../../../frontend/healthtech-web/app/src/core/validate.js) | JSON-Schema subset over the generated closed schemas, plus `contracts.py` validators, `provenance.check_evidence` and the pack's extra domain checks |
| [core/locator.js](../../../../frontend/healthtech-web/app/src/core/locator.js) | Python code-point `chars:a:b` spans and nested `field:a.b` paths (nested paths are implemented here; the CLI viewer supports top-level only) |
| [core/store.js](../../../../frontend/healthtech-web/app/src/core/store.js) | `IdbDraftStore`: one readwrite transaction does the expected-parent check and the snapshot+head+op write; `saved` only from `oncomplete` with strict durability; idempotent op IDs. `MemoryDraftStore` handles denied storage |
| [core/overlay.js](../../../../frontend/healthtech-web/app/src/core/overlay.js) | User notes, local feature links and request drafts kept apart from the dossier; diff/reapply keeps both sides on conflict |
| [core/export.js](../../../../frontend/healthtech-web/app/src/core/export.js) | `healthtech-web-markdown 1.0.0` TH/EN edited report (inert text) and the `healthtech-web-recovery 1.0.0` lossless envelope plus its validating parser |
| [core/run.js](../../../../frontend/healthtech-web/app/src/core/run.js) | Receipt counters from events/manifest, `KnownValue` unknowns, cost view, empty-corpus detection (`corpus_hash == sha256("[]")`) |
| [adapters.js](../../../../frontend/healthtech-web/app/src/adapters.js) | Static capability manifest (run start/control, backend history, PDF, collaboration and analytics all unavailable), local catalog |
| [ui/](../../../../frontend/healthtech-web/app/src/ui/screens.js) | SCR-01…SCR-11, built only through text nodes (no `innerHTML`) |
| [serve.mjs](../../../../frontend/healthtech-web/serve.mjs) | Loopback static server, file allowlist, CSP `connect-src 'self'`, `script-src 'self'` |

Local snapshot IDs (`snap-…`) are a separate namespace from backend `DossierVersion.version`, which the frontend never changes.

## Workspace redesign (owner request 2026-10-30/31)

The owner asked for a drag-and-drop, n8n/Make/Zapier-style workspace that shows the agent's work step by step, with HyperFrames motion, freely resizable and movable panels, navigation and step-by-step tutorial video. Decisions the owner chose (recommended options): HyperFrames renders the tutorial **video**, with in-app motion done in Web Animations/CSS; the canvas shows **real local steps plus replays** of recorded runs, never a scripted fake agent; the canvas is a fixed pipeline with **meaningful drops**; panels form a **dockable workspace**; the video follows **one demo case start to finish** with **music and clicks** (see the sound limitation below).

| Piece | What it does | Where |
|---|---|---|
| Real pipeline stages | `validateDossier` split into `DOSSIER_STAGES` (schema → query → sources → evidence → candidates); each stage emits start/end with its own errors, per-item results and measured ms. Display pacing sits *between* start and work, so it never changes results or measured time | [core/validate.js](../../../../frontend/healthtech-web/app/src/core/validate.js), [core/pipeline.js](../../../../frontend/healthtech-web/app/src/core/pipeline.js) |
| Node canvas | 12 nodes (input, 5 checks, run receipt, AI agent = always *not connected*, review, requests, history, export). Pan, wheel zoom, fit, reset; drag nodes (Alt+Arrow from the keyboard); nodes are links in an ordered `<nav>` list; flowing edges and particles only while a step runs | [ui/canvas.js](../../../../frontend/healthtech-web/app/src/ui/canvas.js) |
| Dockable panels | Library / Inspector / Timeline in left, right and bottom zones; tabbed when shared; splitters resize by pointer or arrow keys (Enter collapses); grip-drag onto dock targets or float as a movable, resizable window; every move also in the ⋯ menu; layout saved per browser with safe fallback | [ui/workspace.js](../../../../frontend/healthtech-web/app/src/ui/workspace.js), [core/layout.js](../../../../frontend/healthtech-web/app/src/core/layout.js) |
| Drag and drop | Evidence → Review node (new note) or Requests node (new draft); open issue → Requests; evidence → feature slot (user link); request cards reorder; OS files → import drop zone. Handles, valid targets lit, ghost, landing highlight, bounce, fly-back on Esc, live announcements; each drag has a button alternative | [ui/dnd.js](../../../../frontend/healthtech-web/app/src/ui/dnd.js) |
| Timeline + replay | What ran, in order, with measured ms; "Replay recorded run" walks a CLI run's events with their recorded timestamps, labelled *replay* | [ui/screens.js](../../../../frontend/healthtech-web/app/src/ui/screens.js) |
| Navigation | Breadcrumb; 5-step journey stepper whose ✓ comes only from real state (passed checks, a non-blank note, a request draft, a started export); "Next" button; 9-stop guided tour (non-modal, ←/→, Esc, focus returns) | [core/journey.js](../../../../frontend/healthtech-web/app/src/core/journey.js), [ui/tour.js](../../../../frontend/healthtech-web/app/src/ui/tour.js) |
| Tutorial video | 56 s, TH and EN, 1920×1080, rendered with HyperFrames 0.8.221 from **real screenshots of this app** (demo dossier, real drags) with push-ins, highlight rings, cursor and captions; 5 chapters; dialog with chapter buttons that seek, transcript and WebVTT chapter track | [tutorial-video/build.mjs](../../../../frontend/healthtech-web/tutorial-video/build.mjs), [ui/tutorial.js](../../../../frontend/healthtech-web/app/src/ui/tutorial.js), `app/media/` |
| Motion | Web Animations API only; stops under OS reduced-motion or the in-app *Reduced motion* setting; state is always also text | [ui/motion.js](../../../../frontend/healthtech-web/app/src/ui/motion.js) |
| Text/density audit | No mid-word breaks (`overflow-wrap: break-word`, `text-wrap: balance/pretty`), shorter Thai labels, 2-line clamps with full-text tooltips, stacked layout under 900 px; an automated e2e audit fails on clipped buttons/tabs/badges, cut node text or over-long labels | [styles.css](../../../../frontend/healthtech-web/app/styles.css), `textAudit` in [run-e2e.mjs](../../../../frontend/healthtech-web/tests/e2e/run-e2e.mjs) |

Before/after captures of the page layout versus the workspace: [before](evidence/workspace-redesign/before/), [after](evidence/workspace-redesign/after/) (including the guided tour and the tutorial dialog). These are screenshots from the e2e runs, not mock-ups.

Rebuild the tutorial: `node tutorial-video/build.mjs --render` (`TUTORIAL_LOCALES=en` renders one language) (from `frontend/healthtech-web`). It captures the screens in headless Chrome, writes the HyperFrames projects to the ignored `tutorial-video/out/`, fetches a pinned render-time GSAP 3.13.0 into the ignored `tutorial-video/.cache/` (GSAP standard no-charge licence; not shipped in the app), and renders `app/media/tutorial-{th,en}.mp4`.

**Sound limitation:** the owner chose soft music and click sounds, but this machine has no licensed music or effects source (HyperFrames reports no signed-in catalog), and the HyperFrames guidance forbids synthesising tones. The videos are therefore **silent**; each project's `index.html` has a commented `<audio id="bgm">` slot. Supply a licensed track (and click effects) and re-render.

## Test commands and actual outcomes

Final run on 2026-10-31 after the workspace redesign, Windows 11, Node v24.19.0, Python 3.12.10, Chrome 156.0.8078.74 (headless, fresh temporary profile deleted after the run). The receipt's `candidate.head` names the commit it ran against.

| Command | Result | Evidence |
|---|---|---|
| `npm test` | 69 tests, 69 pass, 0 fail, 0 skipped. Adds staged-validation equivalence (stage errors sum to `validateDossier`), layout model, journey state and HTTP byte-range tests to the earlier set (Python `json.dumps` cross-check, K190167 read in place, doc links) | console output |
| `npm run test:e2e` | 17 scenarios, 17 PASS, 0 FAIL, 0 page errors. Every audited screen also passes the text-fit audit. E17 covers journey stepper, real pointer drag and Esc-cancel, keyboard splitter resize, float/re-dock, guided tour and video chapter seeking | [results.json](evidence/e2e/results.json), [screenshots](evidence/e2e/screenshots/), [synthetic downloads](evidence/e2e/downloads/) |
| `npx hyperframes@0.8.221 lint` / `check --json` (TH project) | 0 errors, 0 warnings / `ok: true`; remaining notes: `film_silent`, `audio_none` (see sound limitation), 2 `panel_out_of_canvas` infos from the push-in | generated project under the ignored `tutorial-video/out/` |
| `node tutorial-video/build.mjs --render` | TH and EN: H.264 1920×1080, 30 fps, 56.0 s each (ffprobe); web encodes about 7 MB each | `app/media/` |

Downloads in the evidence folder are synthetic-fixture exports only. The public K190167 import was checked in the UI, but no file derived from it is stored.

## Verification matrix (from 05_CLAUDE_HANDOFF.md)

| Check | Result | Mode / fixture | Evidence |
|---|---|---|---|
| Import identity/integrity | PASS. Positive accepted; hash mismatch, dangling/FX-06 comparator source, missing disclosure, late source, synthetic-as-public (mixed), wrong-mode recovery, unsupported schema, `.txt` and >5 MB all rejected; project count and head unchanged | authored fixture + controlled patches | E09; `validate.test.mjs` (19 negatives incl. all `validate_docs.py` mutations) |
| Evidence meaning | PASS. Candidate and disclosed link shown separately; the disclosed link opens separate `independent_disclosure` evidence; "reviewed by me" leaves `association_status` unchanged; empty pool reads as unknown coverage | FX-01, FX-02 | E02, E03, E04, E14 |
| Locator | PASS. `chars:1:2` → `🙂` by code point (UTF-16 slice differs); `1.0` vs `1` typed-field mismatch as in Python; FX-12 bad locator withholds the badge and keeps the raw locator | FX-12 | E03; `locator.test.mjs` |
| Persistence | PASS. Note → acknowledged save → **browser process closed and relaunched on the same profile** → note, snapshot ID, dossier hash and backend version 1 retained | real IndexedDB | E04 |
| Concurrent writers | PASS. Two tabs from one base: one saved, one conflict, exactly one new snapshot; base/theirs/yours retained; reapply keeps both texts. A simultaneous-commit race also yields exactly one success | real IndexedDB, 2 tabs | E05 |
| Storage/error recovery | PASS (**SIMULATED fault**). Denied → memory-only label, recovery file contains the text, source viewer still works; quota → text kept, nothing falsely committed, recovery file contains it; corrupt chain → read-only quarantine, no repair | FX-07, FX-09, FX-13 | E15, E16, E14 |
| Edited TH/EN export | PASS. TH and EN Markdown both contain the edited notes, request drafts, IDs, quotes, unknowns and mode label; recovery JSON → reimport → TH export still contains the notes; backend omission stated | real downloads | E07 (`downloads/E07-*`); `export.test.mjs` |
| Budget/run honesty | PASS. Imported K190167 manifest and events agree; `$0` shown only with its offline scope; FX-11 cost stays "pending reconciliation"; no start/cancel/resume controls on real runs; FX-10 cancel pending → acknowledged, labelled | public run (read in place), FX-10, FX-11 | E09, E11; `run-brief.test.mjs` |
| UI security/privacy | PASS. Note with `<img onerror>`/`<script>`/`javascript:` stays inert in the app and in Markdown; no innerHTML/eval/remote URL/telemetry in source; CSP forbids cross-origin fetch; no credential/email fields | static + runtime | E08, E01; `ui-contract.test.mjs` |
| Accessibility | PASS for automated checks: one keyboard-only path home → evidence → source → note → save → back (focus restored to the row) → export; ARIA tabs with arrow keys; labelled controls, single h1, unique IDs, no animations, every used colour pair ≥ WCAG minimum in all 4 themes. **NOT_RUN:** real screen-reader session, manual 200% zoom | automated | E12, E03, E13; `ui-contract.test.mjs` |
| Responsive/bilingual | PASS. 320/768/1280 px with no page overflow on overview/evidence/source/history/export; both locales × 4 themes captured; locale/theme switches keep unsaved text and focus; quotes and notes are not translated | real rendering | E06, E13 (`screenshots/E13-*`) |
| Local operation | PASS. `npm start`/`npm test`/`npm run test:e2e` work as listed; no key, account or remote server needed | Windows 11 | this table |

## Story acceptance (US-01 … US-28)

IMPLEMENTED means the behaviour works in this local build. SIMULATED means a labelled scenario exercises the UI, with no real service behind it. PROPOSED means a seam or idea only. NOT_RUN means no evidence was gathered.

| Story | Status | Evidence / limitation |
|---|---|---|
| US-01 Start without registration | IMPLEMENTED | E01. Storage explained; no email wall; import works when the catalog fails |
| US-02 Select comparator | IMPLEMENTED | E10. Similar names separated by ID/applicant/date/hash; raw input kept; no-match keeps text. Catalog is local only (authored synthetic + imported projects), no global search |
| US-03 Idea-only brief | IMPLEMENTED | E10; unit `missing_comparator` |
| US-04 Plain-language brief | IMPLEMENTED | E10. Cutoff conflict inline, blank lines rejected, offline count limits shown. Imported runs are immutable; a new brief is always a separate draft |
| US-05 Safe import | IMPLEMENTED | E09; unit negatives |
| US-06 Usable sources | IMPLEMENTED + SIMULATED | Rights note + "unresolved" in source viewer; mixed merge refused (E09); one-unavailable-source shown via FX-04 (SIMULATED) |
| US-07 Supported acquisition only | IMPLEMENTED (gating) / PROPOSED (service) | No real search button anywhere (E09, E11); `api.py` described as dry-run/mock seam |
| US-08 Progress and truthful costs | IMPLEMENTED | E09 public receipt; unit counters (2 calls, 3 occurrences, 2 unique) |
| US-09 Partial/source failure | SIMULATED | FX-04 (E11). Retry unsupported → import alternative; supported retry PROPOSED |
| US-10 Cancel/resume | SIMULATED | FX-10 pending → acknowledged (E11); service behaviour PROPOSED |
| US-11 Overview honesty | IMPLEMENTED | E02, E09 (public empty corpus), E14 (FX-02) |
| US-12 Compare candidates | IMPLEMENTED | E03. ≤3 compare, hidden-by-filter retained, named sort; no invented family merge |
| US-13 Features ↔ evidence | IMPLEMENTED | E03. Unlinked = unresolved; local links labelled "linked by you"; evidence can also be dropped on a feature slot |
| US-14 Exact provenance | IMPLEMENTED | E03; unit locator tests |
| US-15 Relationship vs integrity | IMPLEMENTED | E02, E03; unit `missing_disclosure`, `disclosure_not_independent` |
| US-16 Record ambiguity | IMPLEMENTED | E04 (marker does not promote), note → request draft available. Note-to-request click path is not separately automated |
| US-17 Truthful autosave | IMPLEMENTED | E04 (unsaved before ack), E15 memory label |
| US-18 Conflicts | IMPLEMENTED | E05 (sequential + simultaneous) |
| US-19 Reopen/restore | IMPLEMENTED | E04 reopen after browser restart; E14 corrupt history. Restore-as-new-snapshot is implemented but **not covered by an automated test** |
| US-20 Facts immutable | IMPLEMENTED | E04 hash/version unchanged; E06 locale switch does not translate notes |
| US-21 Edited TH/EN export | IMPLEMENTED | E07; unit export |
| US-22 Export failure recovery | IMPLEMENTED | E07 "Download started" wording; E08 inert. Forced renderer failure path NOT_RUN |
| US-23 Information requests | IMPLEMENTED | E06 draft; E07 included in both exports; copy only, nothing sent; drafts can be created by dropping evidence or an open issue on the Requests node and reordered by drag or ↑ ↓ |
| US-24 Local handoff | IMPLEMENTED (local) / PROPOSED (team) | Download/copy only; no invite or share UI |
| US-25 Errors preserve work | IMPLEMENTED | E09 field/code errors with diagnostic IDs; E08 inert source/notes; repeated saves are idempotent per op ID (unit) |
| US-26 Capabilities and modes | IMPLEMENTED | E01 capability panel; mode label persists into exports (E07); canvas shows the AI agent node as not connected and real runs as receipts only |
| US-27 TH/EN, 4 themes, a11y | IMPLEMENTED (automated) | E06, E12, E13, E17 (journey stepper, tour, tutorial dialog). Text-fit audit on every audited screen. Screen-reader, touch drag and manual zoom NOT_RUN |
| US-28 Storage limits/privacy | IMPLEMENTED + SIMULATED | E14 delete targets one project; E15/E16 simulated faults; no telemetry/auth |

Definition-of-completion reading: all P0 behaviours that a local build can deliver pass with real browser state or labelled simulation. Service-backed run control and team collaboration stay unavailable by design.

## Readability pass (owner feedback 2026-10-30)

The owner found the first build hard to read. Changes made after reviewing the real screenshots, with patterns taken from the owner-supplied [web app UI patterns article](https://www.designstudiouiux.com/blog/web-app-ui-design-patterns/):

| Problem in first build | Change | Pattern |
|---|---|---|
| Two long badges on every fact | One short "✓ matches source" badge; the limitation is stated once per section | Progressive disclosure, without hiding medico-legal limits |
| Raw snapshot IDs and hashes in the header | Device name, cutoff and "last saved 30 Oct 2026 20:56" (Gregorian in both locales); IDs moved to *Technical details* | Progressive disclosure |
| No overview of what is in the dossier | Summary tiles (counts as navigation, not scores) and "suggested next steps" | Cards |
| Three stacked regions on the evidence page | Accessible tabs (one tab stop, arrow keys, `aria-selected`, labelled panels) | Tabbed navigation |
| 7-column table cut off on phones | 4 columns; rows become cards under 600 px | Data table + cards |
| Conflict panel dumped technical text | Each version lists only the user's notes/questions; IDs in a disclosure | Progressive disclosure |
| Download/copy confirmation easy to miss | Dismissible `role=status` toast, bottom-right, 5 s, max 2 | Notifications/toasts |
| Filter changes silent | "Showing N of M" in a live region | Search and filter |

Not adopted: skeleton screens (loads are near-instant, and they need motion), infinite scroll (small lists), modals for routine actions. Before/after captures: [before](evidence/readability-pass/before/), [after](evidence/readability-pass/after/). The readability pass has not been tested with real users.

## Backend and source mismatches (kept visible, not masked)

| Item | Frontend handling | Next owner/action |
|---|---|---|
| F2 history race (`history.py` check-then-write) | Backend history unused; capability shows "unavailable" | Backend owner: exclusive expected-version commit + two-writer regression |
| F4 backend Markdown omits `user_edits` | Own renderer + recovery JSON; export screen states the omission | Backend owner: include edits in `export_markdown` + round-trip test |
| No HTTP job/history service; `api.py` is dry-run/mock | Run start/cancel/resume absent; receipts imported; simulations labelled | Backend owner: separately scoped service package |
| CLI `view_dossier_source.py` supports top-level `--field` only | Frontend implements dot-path fields per `check_evidence` | None required for the UI |
| `ui-fixtures.json` `capabilities` lists `localDrafts=false`, `editedMarkdown=false` | Treated as the *fixture adapter's* scenario data; this app derives its own manifest | Docs owner may relabel if confusing |
| No rights-cleared patent corpus; public cases have `patents=[]` | Empty pool shown as "no patent corpus in this run; coverage unknown" | Research/data owner (HT-W05/W12) |

## Remaining blockers and next action

- **BLOCKED_LOCAL (not this package):** real device–patent evidence, service endpoints, team collaboration and user studies all need separate owners or authorisation.
- **NOT_RUN:** real screen-reader session (NVDA/VoiceOver), including on the canvas and drag targets; manual 200%/400% browser zoom (approximated by the 320 px viewport); touch drag on a real phone/tablet (pointer events are exercised only with mouse input in headless Chrome); usability sessions with entrepreneurs/investor analysts; Firefox/Safari.
- **Owner-chosen but not delivered:** music and click sounds in the tutorial video (no licensed source here; silent render, audio slot prepared).
- **By design, not connected:** the AI research agent node. It needs a run service, explicit authorisation, a cost ledger and its own tests before it can turn on.
- **Next action:** owner reviews the branch diff and evidence. If accepted, the control plane decides integration and updates `progress.json`/`next-actions.md`. Next frontend step: run a short usability session with the HT-W16 task script using the demo and the K190167 import.
