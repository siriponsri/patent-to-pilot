# RESTORE-DOI · Independent public restore

**Verdict: RESTORED.** On 28 November 2026 UTC, an executor independent of the release build retrieved Zenodo version 1.0.0 without authentication, verified the archive and all ten frozen prediction files, and ran the published scorer on Windows CPU in an isolated runtime. Both prospective horizons returned `PENDING` with zero outcome fetches. The public synthetic known-answer fixture passed. This is the execution evidence for the Planner to review against objection 1. The mature Track A readouts are **NOT_RUN**. [Joint sign-off](../JOINT-SIGNOFF.md) · [Transcript](RESTORE-DOI-transcript.txt).

## Published metadata

| Field | Observed on Zenodo | Upload-sheet comparison |
| --- | --- | --- |
| Version DOI | `10.5281/zenodo.24629100`, record 24629100 | Zenodo-minted as specified |
| Concept DOI | `10.5281/zenodo.24629099` | No concept DOI specified before deposit |
| Publication date | 2026-11-28 | Matches date of publication |
| Title | LOE-Bench Track A prediction release | Matches |
| Creators, in order | Srihangpiboon, Siripon and Ploysuwan, Tuchsanai | Both match |
| Resource type, version, visibility | Dataset, 1.0.0, open | Match |
| Licence | Apache License 2.0, API identifier `apache2.0` | Matches. The description preserves CC0 1.0 for the openFDA and NCATS GSRS fields |
| Related DOI, `isSupplementTo` | `10.17605/OSF.IO/P2SMD` | Matches |
| Related URL, `isSupplementTo` | `https://github.com/siriponsri/patent-to-pilot` | Matches |
| Related URL, `isDerivedFrom` | `https://github.com/siriponsri/patent-to-pilot/tree/loe-track-a-freeze-20261127` | Matches |
| File list and Zenodo checksum | One file, `track-a-release.zip`, 15,983,054 bytes, `md5:2599a90565e28e69019207884877a407` | File name and size match. Downloaded MD5 agrees with Zenodo |
| Keywords | LOE-Bench, loss of exclusivity, generic entry forecasting, ANDA, prospective validation, FDA, reproducibility | Match |

No deposit metadata mismatches against the [upload sheet](../ZENODO-UPLOAD-SHEET.md) at `8bb93fb7`. The version DOI resolved to the same HTML record returned by the direct record URL. The page and API were retrieved separately with HTTP 200. [Version DOI](https://doi.org/10.5281/zenodo.24629100) · [Record page](https://zenodo.org/records/24629100) · [Public API JSON](https://zenodo.org/api/records/24629100).

The archive's bundled README still shows the version DOI template, and its `CITATION` points readers to the exact version DOI of the public record. Use the DOI in the record and in the updated repository guide.

## Byte checks

| Object | Observed SHA-256 |
| --- | --- |
| `track-a-release.zip` | `acb533afb45f34f40d2ece2b97bc72b2b08fc3f6919fd73e1eb7064bf6e8049a` |
| `freeze-manifest.json` | `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d` |
| `release.json` | `879d27d9e60fb141d0e46ec2bc17aad3de61938460e678e7178841a8d2ca6d76` |
| `requirements-tracka.lock` | `afaf49125c7f0198e692412f3632ffa8e3844d35cab721c703a1eef2461789a4` |

Both the API file URL and the record's public download URL returned the expected archive SHA-256. The ZIP held 49 members. The freeze manifest matched the external OSF update 4 digest, and each prediction member matched its pin in both manifests. All ten arms were admitted. The eight non-C9 arms each cover both horizons, and both C9 arms cover 24 months. [OSF update 4 digest](../OSF-UPDATE-4-SHEET.md) · [API file](https://zenodo.org/api/records/24629100/files/track-a-release.zip/content) · [Record download](https://zenodo.org/records/24629100/files/track-a-release.zip?download=1).

| Arm | Observed and expected prediction SHA-256 |
| --- | --- |
| B1 | `03512b32026d929e8cdcce2a352bfbdafef0d90473330e7177b6e6ca36346c13` |
| B3 | `06d02ec233363b16fed5673babe7ef72e4d18a5406b2ef5725a6c038a5971ace` |
| C9-GRPO | `75ab8e09e5210fa841818b503eda1b2cc6b42576fa542130c83fff9c263d9de7` |
| C9-SFT | `cce35d54f27062e0f2eee1e6c13d1a0742a7181bfdaeed03150a8b5218936488` |
| L1 | `79c3b990ec4b6c38df4861ab51a193968cd4b532290da702d8dc1d6e612e9b41` |
| L1e | `bf910f5635a3bb3c1808387924806d344c9f61ba2e1fba9294c9fcf065e4f51d` |
| M1 | `a89086db767ba27e8c15927138c6c2eff2d0b52217679f0bee89c18b9997edd0` |
| M3 | `cee7d7a4f77dd57424b7420ccb5c7b5c48dda68a067242bebe52fee45598d410` |
| P1-RSF-OPEN | `40a44ecc1c6b9f477d16e8d638a098fc73f4801624daf4e5476ce9d614470f1f` |
| P2-COX-OPEN | `2b0eff2b76a5da5968c434965c44d649469d533f4ea31485d8fb8d34d0dda29f` |

## Execution

The archive and fresh virtual environment lived in an empty Windows temp directory outside the checkout. CPython 3.12.10 ran in isolated mode with system site-packages disabled. The only installed scorer dependency was NumPy 2.5.4, obtained from public PyPI using the archive's binary-only, hash-checked lock. The `numpy-2.5.4-cp312-cp312-win_amd64.whl` SHA-256 was `a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a`. The harness checked the interpreter paths and module origins, then invoked the published CLI entry point with socket operations denied. Runtime imports came from the extracted release, the fresh virtual environment and the standard library. There was no private artifact access.

| Check | 12 months | 24 months |
| --- | --- | --- |
| Public release with exact OSF digest passed to `--freeze-sha256` | Exit 2, `PENDING` until 2027-11-27 | Exit 2, `PENDING` until 2028-11-27 |
| Outcome access | Empty source inventory and zero socket operations | Empty source inventory and zero socket operations |
| All-zero external digest | Exit 1, external pin mismatch | Exit 1, external pin mismatch |
| One byte appended to M3 in a disposable extraction | Exit 1, M3 prediction SHA-256 mismatch | Exit 1, M3 prediction SHA-256 mismatch |
| Public synthetic known-answer test | `SCORED`, 20 drugs, 10 events, four slots. M3 recall 1/3, B1 recall 0, B3 recall 0.20, H3 descriptive | `SCORED`, 12 events. H1, H2 and H3 passed the fixture and H3 used the verified first 12-month result |

Neither negative check wrote a results directory. The known-answer fixture is a single public unit test that exercises both scoring horizons, revision handling and offline replay using synthetic FDA payloads. The fixture source was downloaded directly over anonymous HTTP (SHA-256 `178372f00e38cb23ed92ae6ec0470c236ef54a7b2c5e3720d4773e1655fd044b`), and the test imported the scorer from Zenodo. The transcript retains the two real `PENDING` results and their manifests. A separate 12-month smoke test gave the published scorer the DOI directly and reproduced exit 2, `PENDING`, with an empty outcome source inventory. [Public fixture at the starting revision](https://github.com/siriponsri/patent-to-pilot/blob/8bb93fb794ef07e77a63212ec24e78cede2e9785/loe-bench/loe_bench/tests/test_score_release.py).

The first web-tool read did not retrieve the record. Anonymous `curl.exe` requests then retrieved the page, API and ZIP successfully. The [transcript](RESTORE-DOI-transcript.txt) SHA-256 is `b144b8ac6749f8b30cfa1e85d35cd8a007c6b54002598bfcd03e7180452101c0`.

## Repository handoff

- Added the version DOI to the [scoring guide](../HOW-TO-SCORE-TRACK-A.md), [benchmark card](../BENCHMARK-CARD.md) and [upload sheet](../ZENODO-UPLOAD-SHEET.md). Replaced the DOI and digest templates in the [calendar](../reminders/track-a-readouts.ics) and [Worker configuration](../../../ops/tracka-cron/wrangler.toml), and updated the [Worker README](../../../ops/tracka-cron/README.md). The calendar kept its seven events, alerts and annual recurrence. Eight CLI examples use the published pins. The workflow already takes the DOI and digest from inputs or repository variables.
- `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` passed 2 tests. `npm test` in `ops/tracka-cron` passed 11 tests. Calendar validation confirmed CRLF, a maximum of 75 octets per physical line and identical non-description properties.
- Planner review is pending on `loe/RESTORE-DOI`, cut from `8bb93fb794ef07e77a63212ec24e78cede2e9785`. This receipt is the executor handoff and memory entry for the Planner's lane records. Obtain the scorer and freeze from the versioned archive and keep the external OSF pin in every run. Live Actions and Worker configuration remain **NOT_RUN**.
