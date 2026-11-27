# D31 bounded source intake

**Seven public OCS opinion PDFs retained out of eight title-selected attempts.** The [protocol](PROTOCOL.md) defines historical request-to-opinion-to-disposition linkage. The private intake artifacts are under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ocs-a-20261126/`. The independent query and key are stored separately under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ocs-planner-20261126/`.

The [official Thai Drug Act search](https://comment.ocs.go.th/main/search?q=%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%8A%E0%B8%9A%E0%B8%B1%E0%B8%8D%E0%B8%8D%E0%B8%B1%E0%B8%95%E0%B8%B4%E0%B8%A2%E0%B8%B2) returned 10 titled opinion rows after skipping duplicate icon anchors and filename links. The RIA/draft entry 1443/2565 and reconsideration entry 47/2534 were excluded on title/filename metadata. The latter concerns the same products as 242/2531. No replacement was sampled after intake. Earlier surfaced materials including 344/2532 stayed outside the set. The excluded known exposures are explicitly listed in the private roster. This is a first-page pilot, not a complete cross-domain inventory or a claim of zero prior exposure outside the project.

| Opinion | Opaque folio | Intake |
|---|---|---|
| 166/2519 | 08 | Retained, 2 pages |
| 43/2532 | 04 | Retained, 1 page |
| 255/2517 | 01 | Retained, 3 pages |
| 202/2518 | 05 | Retained, 3 pages |
| 1585/2565 | 06 | HTTP 200 PDF response exceeded the 1 MiB admission cap. The bounded client read 1,048,577 bytes, then stopped and retained no source bytes. No full size, page count or issue count inferred. |
| 469/2525 | 02 | Retained, 4 pages |
| 253/2540 | 03 | Retained, 4 pages |
| 242/2531 | 07 | Retained, 5 pages |

Seven retained PDFs sum to 1,338,319 bytes and 22 pages. The alternate live medical-device index returned zero results. The healthcare-facility index returned two title rows excluded from this primary. The ordinary law search page was a successful index access check and contributed no pilot cases. Official direct download worked for each retained record. Retained PDFs are examined locally within the limited official-source basis in the protocol.

| Identity record | SHA-256 |
|---|---|
| Official search page, `medicine.html` | `770e9453717aecf88c9bc48c776d8b6f0bc041602200107dfd8b5f2468c6102c` |
| Title-only pre-acquisition `enrollment.json` | `1aa21ba3c8716da8b71b7d69074fff9efbc9b4548df2350a39f95500591c214d` |
| Full per-item attempts and PDF digests, `sources.json` | `c1f5911d7e13da36783e65b81bd39e4783a3c98c11ae095a72a4c49381ca601e` |
| Opaque runtime metadata with no titles, `runtime-corpus.json` | `f67208e38a8653dee9a8766e9033741bc00aaf98a69c553941d685283ad15e63` |
| Canonical sorted embedded page text, `canonical-pages.json` | `b8377df7d38941ff8617c2ec8f69800e1e05dbfcfeb9578f8be39a35f47369a5` |

Three independent AI-assisted source readers who did not write the reader visually checked disjoint source assignments and prepared 11 issue rows and 30 necessary answer fragments. Their work provides source binding and placement evidence, with no expert legal-adjudication claim. A separate incoming original was verified for zero issues. All 11 requests are recited in or cited by their OCS opinions. A separate public exact-reference search reported opinions or unrelated records only. One issue had a procedural disposition. The source key retains it as the actual issuer response rather than substituting a guessed answer on the merits. The scoped results should retain distinct acquisition and issue denominators.

The Planner held [v1](freeze-v1-hold.json) before any original because semantic requirements had been capped at two fragments and adaptive ranking inspected uncharged unopened-window text. In [v2](freeze.json), the scorer enforces two returned nonoverlapping spans and accepts multiple short requirements when they fit. The shared index stores cue counts and trigram descriptors. Query-time operations inspect descriptors until a page is opened. The independent query/key bytes and ranking rules were kept. The Planner's key-only pre-audit confirmed every requirement fits the revised validation and the original path was absent.

## Pre-release code gate

Four focused fixture tests passed on v2. The full Windows gate uses the existing S4 CPython 3.12.10 validation environment, `qa-sites` dependency overlay, `PTP_NO_BROWSER=1` and a fresh short pytest temporary directory. The following logs are retained in the private intake directory.

| Attempt | Result | Log and SHA-256 |
|---|---|---|
| Provisional full suite | 2,801 passed, 8 known SACR failures, 10 skipped, 1 xfailed. This preceded the final corrective fixtures. | `pytest.log` · `378d63b80116bba4b1b24405465c356ae1d9f34b9a7e1c9eee9348c5e7400884` |
| First v2 full suite | 2,802 passed, 9 failed, 10 skipped, 1 xfailed. The unchanged HealthTech vector HTTP test reached its fixed polling limit while the worker was still running. | `pytest-v2.log` · `18fa92711501b11ee630d423913c02d8503960cd31777f2112ddd6778225492c` |
| Second v2 full suite | 2,802 passed, 9 failed, 10 skipped, 1 xfailed. Same test and failure state. The test fixture's saved job later reached `succeeded`. | `pytest-v2-retry.log` · `698f91fd3f1da24ee92e1cf37871445506983346d7d3d2befe03cd65465295e4` |
| Scheduling diagnostic | Interrupted at the Planner's direction. No gate result. | `pytest-v2-thread-scheduling.log` · `220581affeb0729621263ad25cabddb0380d62cb45fbbf4b77a4d4552c9d32c2` |
| Corrected focused run | 6 passed. Both vector HTTP tests and all four D31 fixtures. | `pytest-v2-polling-focused.log` · `07782c9d83f4945f196e3920c833b0bb6011481913416bc1eb2442f3b6e3dccc` |
| Corrected ordinary full suite | 2,803 passed, 8 known SACR failures, 10 skipped, 1 xfailed, 2 warnings, 244.46 s. The eight failure IDs match the standing exceptions. | `pytest-v2-polling-full.log` · `4ae9a8b6a8b739fda2abc48848cb4a0d08358aa55e28edea83fafebf0ce43d33` |

The Planner assigned temporary ownership of `tests/test_healthtech_vector_http.py` for this test-only repair. It now uses a three-second monotonic deadline with up to 10 ms between polls and reports the last state on timeout. All terminal, provider and result assertions are retained. The corrected full gate ran with ordinary interpreter scheduling. No research-policy or v2 freeze bytes changed.
