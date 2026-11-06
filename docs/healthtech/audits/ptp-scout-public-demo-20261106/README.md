# Solution Scout public demo: corpus, live search, recorded rationales and M2 screens (6 Nov 2026)

Status: `PASS` for engineering. This is a research demo, not an evaluation. No DAPFAM data and no test split were used. USD 0 paid.

Spec: [SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md](../../research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md) (§9 holds the owner decisions).

## 1. Rights and provenance ([rights.json](rights.json))

| Item | Source | Licence | Use here |
|---|---|---|---|
| Corpus | HUPD (Harvard USPTO Patent Dataset), `HUPD/hupd` on Hugging Face, `data/2017.tar.gz` | CC BY-SA 4.0 | Local demo corpus, kept out of Git. Share-alike applies to the derived subset |
| Encoder | `datalyes/patembed-large`, revision `2d5c0f92…` | **CC BY-NC-SA 4.0, non-commercial** | Research use only. A commercial deployment needs another encoder. Shown on the demo's about line |
| LLM | `Qwen/Qwen3-8B`, revision `b968826d…` | Apache-2.0 | Local V100, greedy decoding |

- PatentsView was the planned source, but its bulk files now need a USPTO.gov login with MFA, and the legacy S3 links return 403. The owner chose HUPD instead.
- Inventor and examiner names are dropped.
- Generated rationales and corpus text stay in `../_private_artifacts/healthtech/scout-public-demo/`, not in Git.

## 2. Corpus subset

Built with `scripts/healthtech/build_scout_hupd_subset.py`, seed `20261106`:

- 295,735 HUPD 2017 applications read, 0 skipped.
- Up to 8,000 kept per IPC section by sha256 order: **56,528 applications**.
  - Section D has 1,723 and E has 6,805, which is every eligible application in those sections.
- Fields kept: publication number, title, abstract, first claim, IPC3 codes, publication date, decision.

| Artifact | sha256 |
|---|---|
| `hupd-2017.tar.gz` | `688a44e3a09b2ae2e0012278d040accb3d407e87940548ae29e1eb22e39cc86a` |
| `corpus.jsonl` | `32be3c19fbc8dd53fdbd12fb3aa2649e97419f47f99e0491ac5494ffe78cea0e` |
| `family-ipc3.jsonl` | `927a0ea269424ac3…` |

## 3. Encoding (V100) and CPU/GPU parity

- `run_dapfam_dense_pool.py` (runner sha `4112c277…`), PatEmbed-large fp32, document prompt as Stage 0.
- 74,670 passages (384/64-term windows over title + abstract + first claim), encoded in 1,618 s on a Tesla V100-SXM2-32GB. Status `PASS`.
- Vectors: f32 `f53dc6525a6c74ac…`. The local f16 copy is `d51609df3d48be6c…`; its maximum absolute difference from f32 is 0.00024.
- **Parity.** The 8 authored demo briefs ([scout-demo-briefs.json](../../../../examples/healthtech/scout-demo-briefs.json)) were encoded on the V100 (rankings `2141bc0c…`) and again on CPU with `scout_live.LiveIndex` (torch 2.15.0+cpu). For all 8 briefs the top-10 is identical and the top-200 overlap is 200/200.
- CPU latency per brief: encode about 0.5–1.2 s, search about 0.14 s after the float32 in-memory change. Index start-up takes about 100 s.

## 4. Recorded rationales (Qwen3-8B, V100)

- Prompt `ptp-scout-rationale-v0` (`scripts/healthtech/run_qwen_scout_rationales.py`). It asks for JSON with `what_it_does`, `transferable_mechanism`, and 1–3 quotes copied word for word.
- Candidates: for each demo brief, the own-field top 2 and the other-field top 5, giving 56 candidates (inputs `c26c9742…`).
- Run: 56 calls, 0 failed, 0 truncated, 0 retries. 33,013 prompt and 10,169 output tokens. Mean latency 12.4 s, 695 s in total, peak GPU memory 16.8 GB. Output `f5c072de…`.
- Book: `rationale-book-v0.json` (`51bc08c6…`), bound to the corpus hash.

**Quote check.** This is the server's literal check: words in order, whitespace-tolerant, case exact.

| | Count |
|---|---|
| Quotes found in source | 120 / 158 (76%) |
| Not found | 31 |
| Too long (> 60 words) | 7 |
| Rationales with every quote found | 29 / 56 |
| "No clear transferable mechanism" | 1 |

An 8B model often edits or joins its "verbatim" quotes, so a literal check is necessary, not optional. The UI shows every unmatched quote in red. A literal match is still not semantic support.

## 5. Software

| Area | Change |
|---|---|
| Backend | `src/patent_to_pilot/healthtech/scout_live.py`: `LiveIndex` and `CpuQueryEncoder` with the weight-hash check |
| | `scout_service.py`: live mode, `RationaleBook`, `rationales_available`, short rationale file names (a 500 traced to Windows MAX_PATH was fixed) |
| | `serve_http.py`: `--scout-live-dir`, `--scout-model-dir`, `--scout-rationales` |
| Frontend (M2) | `frontend/healthtech-web/app/scout.html`, `scout.css`, `src/scout/{main,model}.js`, and `createScoutAdapter` in `adapters.js` |
| | Composer with IPC chips and the recorded demo briefs |
| | Animated field constellation, descriptive only |
| | Own-field and other-industry lanes |
| | Drawer with mechanism, quote badges, highlighted source and decisions |
| | Receipt strip; TH/EN; light and dark; reduced motion; no inline styles (CSP); no `fetch` outside the adapter |

## 6. Verification

**Browser check (in-app Chromium, 6 Nov 2026):**

- A new, unrecorded brief (hospital plastic surfaces, A61) returned other-industry coatings and packaging films. The drawer showed the source and the "no recorded idea" note.
- Demo brief "pump seal":
  - 7 rationales are available.
  - 4 drawers had all quotes found; 3 had one `not_found` badge.
  - Highlights matched the server offsets, and the decision button saved.
  - The receipt read: live, encode 1.0 s, search 136 ms, paid calls 0.
- Mobile (375 px): no horizontal overflow; lanes stack; the map scrolls inside its card.
- TH: all labels are translated.
- Screenshots were taken only while the pane was visible. Later checks read the DOM state.

**Tests:**
- Frontend `npm test`: 81 tests, 80 passed, 1 skipped (pre-existing), 0 failed. Includes 7 new Scout tests.
- Python: full suite 739 passed, 1 skipped, exit 0. The scout tests include a live-mode test with a fake encoder and no torch.
- Frontend e2e (`npm run test:e2e`, Chromium): 17 passed, 0 failed. Record in [web-e2e-2026-11-06T11-02-10-760Z](../web-e2e-2026-11-06T11-02-10-760Z/results.json).

**Run it:**

1. Backend: `C:/Users/User/.ptp-scout-venv/Scripts/python scripts/healthtech/serve_http.py --port 8787 --data-dir C:/Users/User/.ptp-scout-data --scout-live-dir ../_private_artifacts/healthtech/scout-public-demo --scout-model-dir C:/Users/User/.ptp-models/patembed-large --scout-rationales ../_private_artifacts/healthtech/scout-public-demo/rationale-book-v0.json`
2. Frontend: `cd frontend/healthtech-web && npm start`.
3. Open `http://127.0.0.1:5178/scout.html`.

## 7. Limits

- This is a demo, not evidence of retrieval quality. Frozen evaluation E1–E5 is M5.
- HUPD contains applications, not patent families. Each unit is one publication.
- Rationales are recorded for the 8 demo briefs only. A new brief gets live search but no rationale until the live LLM mode exists (M4).
- No user validation. "Useful / not useful" decisions are the developer's own labels.
