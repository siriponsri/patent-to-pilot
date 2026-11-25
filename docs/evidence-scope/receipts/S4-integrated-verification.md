# S4 integrated verification

The S4 writer handed back `2989cdb9d8064c71e85ebd81b9dc2c5b9a7b6fd6`. Integration used its nine named paths together with the research code and fresh evaluation packet. All 21 production-candidate file hashes match the [release manifest](S4-release-manifest.json) and reproduce candidate digest `47e3286fc92e39bbad7e572b3b0a8174b5327d58924109a38cc9fcbfb55a3fc3`. The S4 [release receipt](S4-product-release.md) attributes the clean environment, Chromium UI work and source-specific rights checks to the solo validation operator. The release remains a Windows local alpha and local demonstration with public inputs. External usability and public distribution remain NOT_RUN.

## Integrated launcher and recovery

From the integrated workspace, run the following with the existing S4 validation environment. Use a fresh output directory.

```powershell
$q = (Resolve-Path '../_private_artifacts/ptp-s4-20261125').Path
$env:PYTHONPATH = Join-Path $q 'airgap'
$env:S4_REQUIRE_GUARD = '1'
$env:PTP_NO_BROWSER = '1'
rtk proxy (Join-Path $q 'validation-venv/Scripts/python.exe') docs/evidence-scope/receipts/S4_verify_local.py (Join-Path $q 'integrated-launcher-r1') --originals ../_private_artifacts/evidence-scope-s2
```

**PASS, exit 0.** The launcher retained the original occupied listener and selected the next port. It checked the exact citations from the two focal journeys, partial signer evidence, unknown commencement and rejection of a missing export. All 19 S2 upstream file digests matched. The integrated store backed up online and replayed six saved traces after restart and restore. A separate read-only SQLite integrity check returned `ok`. The retained-source rebuild preserved R1 and changed the withdrawn-source-dependent R2 to unknown. D3 in-place withdrawal remains unsupported. The profile used loopback-only access under the existing socket and browser guards. Physical-network disconnection was NOT_RUN.

Raw evidence is in `../_private_artifacts/ptp-s4-20261125/integrated-launcher-r1/`.

| File | SHA-256 |
|---|---|
| `report.json` | `bc6b3eedd945ffcc751d45e5880be91bf33895c273dd9bb4f3a136c35fcde843` |
| `traces.json` | `48111025148b7c1c2130f0153b0e58b2b9cb44f1dddef0e804af3eaa82112718` |
| Backup at creation | `80e07634322d288ccc1a7c24f557c7e28e11e9bb7cc85f0b44e0720f3309f24b` |

## Full repository QA

The integrated run used CPython 3.12, the S4 validation venv, the existing QA overlay including NumPy, SciPy and rank-bm25, pypdf and PyThaiNLP, and the pinned Chromium executable. The first attempt used a long private `--basetemp` path. It ran 2,793 passed, nine failed, seven skipped, one expected failure. Eight failures matched the standing SACR budget cases. The additional `test_hf_cache_snapshot_revision_is_recorded` failed while creating a synthetic cache directory with Windows error 206. The original full log and exit record are retained in `../_private_artifacts/ptp-s4-20261125/integrated-option-a-r1/`. The exact final candidate rerun uses the same dependencies and a fresh short temporary directory.

**Final-candidate full gate satisfied the repository's standing exception policy.** The final v2/S4 integrated run finished in 254.11 seconds with 2,795 passed, 8 failed, 7 skipped, 1 expected failure and 2 warnings. All eight failing IDs are the previously documented SACR r2/r3 budget cases, four per supervisor. The formerly failing synthetic cache test passed in the short temporary directory. Pytest's raw exit was 1. No new failure remained. The command was `python -m pytest -o addopts= -q --tb=short --basetemp <fresh-short-path>` in the same integrated workspace, using the dependency overlay above. The complete evidence is under `../_private_artifacts/ptp-s4-20261125/integrated-option-a-r2/`. The `pytest.log` SHA-256 is `3d76d15957de34d5b06a01e76d2721c6fbfdaea3d911f6592142f0ff58a7aed4`. The recorded dependencies log SHA-256 is `fe6b9edf58174023fb756f303ee680b8118401a2cba634dd3d2b38f5a265c56a`.

S4-T01 through S4-T05 close as **Windows local alpha and local public-data demo READY_FOR_REVIEW**. Release availability is a pinned source checkout and loopback launcher. The product status is independent of the Option A measurement.
