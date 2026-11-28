# TRACKA-READOUT8 executor receipt

29 November 2026. Branch `loe/TRACKA-READOUT8` starts at `ed1928a9c035862f28febd2508f4367f85c59b1b` on `origin/research/loe-bench`. Protocol `07f04f70eb1abb98074b1d5eb7f0ccfc2cab9b1c` was committed and verified on origin before implementation `fbfb053ca7b4d8fc468414acc3eb4e1f2268cf84`. [Protocol](TRACKA-READOUT8-PROTOCOL.md) · [Round 7 finding R7-A](../reviews/EXTERNAL-REVIEW-R7.md#new-findings-table).

## R7-A

**PASS in executor verification.** Before the fix, ordinary and recovery invocations against the public kit stopped at `score_release.py` with exit 1. After restoring its registered bytes, both invocations reached `PENDING` with exit 0 through the DOI. The observed UTC date was 28 November 2026 and 12-month maturity is 27 November 2027. Both runs had empty outcome source inventories, and their report digests matched the run manifests. The bundled `score_release` control independently returned `PENDING` with exit 2. Exit 0 for pending status applies to the integrated CLI as specified by this card. Consumers of that CLI distinguish pending from completion using the status line or `results.json`. [Guide](../HOW-TO-SCORE-TRACK-A.md) · [Version DOI](https://doi.org/10.5281/zenodo.24629100).

The integrated readout renders the base report and adds the publication-time formal status and current witness discussion before writing the run manifest and promoting the directory. Failed recovery reasons flow from the same `missing` list into JSON and the base report. The ordinary and recovery probes matched the three witness dispositions, the report digests and the five archived result assets. [Readout](../../../loe-bench/loe_bench/tracka_readout.py) · [Regression tests](../../../loe-bench/loe_bench/tests/test_tracka_readout.py).

## Published source comparison

Anonymous `curl.exe` retrieved `track-a-release.zip` from the Zenodo API after the web reader could not open the record. The 15,983,054-byte ZIP matched SHA-256 `acb533afb45f34f40d2ece2b97bc72b2b08fc3f6919fd73e1eb7064bf6e8049a`. The ZIP's `scorer-version.json` member had raw SHA-256 `470d62ee13f27cdc80ef1cfddff4c12e87553c444a243895d837fa2e3f9bc2d4`. The source pins below use the release reader's LF-normalized SHA-256 rule. All 25 released Windows source files also matched the restored Windows checkout byte for byte. The only starting mismatch was `score_release.py` at `bf16e6bdc1792ad72d15027f843c72e70398e3c9fe4897d5319349a544753730`. The restored Git blob comes from parent `6118665af260417a1a6f263f652a1a81c3be3067` of the READOUT7 implementation. [ZIP](https://zenodo.org/api/records/24629100/files/track-a-release.zip/content) · [Release licence and provenance](RESTORE-DOI.md) · [Published metadata fixture](../../../loe-bench/loe_bench/tests/fixtures/zenodo-24629100-scorer-version.json).

| Installed file | Published SHA-256 | Base | Final |
| --- | --- | --- | --- |
| `__init__.py` | `f2bef6ac7d9ba671959533dfa496b3c8b1a141106b1bd3e3a1dcf14906dca24f` | MATCH | MATCH |
| `baselines.py` | `369113e84faa3e1dc4fbb908daa0caaa3bae82721cd18484ee9185b483f6ffe1` | MATCH | MATCH |
| `challenge.py` | `c4c029bdc93087c15eb043b2b920ed76e357064e7f7b9df114a095c33f8b9200` | MATCH | MATCH |
| `common.py` | `bbd1073b973df87458d81df36a82ec16aec639e28ef1ca247b1e0e00cacb5d00` | MATCH | MATCH |
| `dataset.py` | `8dbd5d34b54ddc525cc7c1b629fab995dbe9844846084ce73128acb12b1d52b5` | MATCH | MATCH |
| `evidence_graph.py` | `efdd626b292973f394a30f2884593592d0d3c8be69e98b6584fb40e21f244e01` | MATCH | MATCH |
| `kleene.py` | `0dce39219c7606734fa734725c4d65abb8b3e186eed157a235ec9fc49c5b01fb` | MATCH | MATCH |
| `llm_arm.py` | `a0f3681e0ceba5d6128900f7fc2cf4243d5522821b7118b49bcddd0216d4dca6` | MATCH | MATCH |
| `metrics.py` | `702c14dc518ae713b5b89bba7f3443e17839167a20579d00cf71b99815451514` | MATCH | MATCH |
| `moiety.py` | `1354642be228a9605e6dc20ccacd3b0915ed8b315b715e7ee572cf30a849e474` | MATCH | MATCH |
| `moiety_linkage.py` | `78a4110cf5fa36d1837300e8ac585ae708c206a5ad061d49b1981d77b9384c57` | MATCH | MATCH |
| `ob_history.py` | `6469224921626b98838d90df60a595d896d4626fc1ae668f6b28a3d8f4f35821` | MATCH | MATCH |
| `piv_history.py` | `4ae29c2e3c215c9105687007731a3db66d3c6dbe2206039e5b62bde309cf727e` | MATCH | MATCH |
| `priorarms.py` | `0f2b05b7e2dc63c9377805304b4980e3d9408abcf1d1a000e8a152ddc0685bf2` | MATCH | MATCH |
| `regulatory_graph.py` | `dbf13d1d641efd776c7849bc025f9a74dca1d413cbfab785c028fe797ab19e5b` | MATCH | MATCH |
| `review_metrics.py` | `e524216bc58673852f92991f7d90f1c92d9f6f8221545c50704232ddbd98830a` | MATCH | MATCH |
| `score_release.py` | `53ac9231db2834c3d00e6d060e02fd34633e40bd699123f1c18887db36f7adf2` | MISMATCH | MATCH |
| `seal.py` | `14ae46da72307f91d1430ba98db0a082cd58037e878b21678bba3a260dd557a6` | MATCH | MATCH |
| `t1v3.py` | `05ce42caf01c440589ab015d1f0911851ae91ef50884a174012eaad05a41d3e2` | MATCH | MATCH |
| `t2.py` | `91f643e4dc636da600aca2ae4a94a7fa5fc2aef2174af61130f01456478ab988` | MATCH | MATCH |
| `t2_features.py` | `fde22235cc04d71b648f8ce019c1613a290570fbd09c6cccebdaf44cb13846f7` | MATCH | MATCH |
| `tracka_outcomes.py` | `cdae165343fd62145be01bcbbd0cc84ec18e99716c4621aae35ae68320bbe6d4` | MATCH | MATCH |
| `tracka_release.py` | `01996716ae42bce8ced21b6b31999aa013f6d1bf335941e25ede465f85f53f44` | MATCH | MATCH |
| `tracka_statistics.py` | `e6c97d72651bb513168a58ad632100ad1d46d09b2293b27154d8c458721ee137` | MATCH | MATCH |
| `voi.py` | `ed0534981c920ac3fe1ca59c8e7a6f338f9d1fd366cb72bde667e312444b87ac` | MATCH | MATCH |

## Verification

Local runs used Windows CPython 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, NumPy 2.5.4, pytest 8.4.2, Node v24.19.0 and npm 12.1.0. Commands below omit the local `rtk proxy` prefix.

From `loe-bench/`, run the DOI smoke with a fresh output directory for each invocation. The same command using the verified unpacked kit for `--release` also passed in recovery mode.

```sh
python -m loe_bench.tracka_readout --release 10.5281/zenodo.24629100 --horizon 12 --freeze-sha256 8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d --out <fresh-output-directory>
python -m loe_bench.tracka_readout --release 10.5281/zenodo.24629100 --horizon 12 --freeze-sha256 8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d --out <fresh-recovery-directory> --recover
```

| Check | Result |
| --- | --- |
| `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | **PASS.** 302 ran, 292 passed and 10 skipped in 93.672 seconds, exit 0. Existing Purple Book file-handle warnings appeared. |
| Six targeted `ReadoutTest` methods via `python -m unittest -v` from `loe-bench/` | **PASS.** Six passed in 17.792 seconds, exit 0. The pin guard accepted the checkout and rejected each of 25 isolated mutations. Ordinary replay and recovery each covered matching, disputed and missing witnesses. The other probes covered a replaced 12-month result, disputed result pins with a verified first capture, and missing capture versus missing result. |
| `npm test` from `ops/tracka-cron/` | **PASS.** 18 passed, exit 0. |
| `python -m pytest -o addopts= -q --tb=short --basetemp "$env:LOCALAPPDATA/Temp/pt-r8-07f04f7"` from the repository root | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed and 2 warnings in 370.13 seconds, raw exit 1. The eight failures were the SACR r2/r3 supervisor budget cases for `nan`, `inflated`, `erased` and `insufficient` in each supervisor. |
| `gh workflow run score-track-a.yml --repo siriponsri/patent-to-pilot --ref loe/TRACKA-READOUT8 -f synthetic=true` and `gh run watch 46176191476 --exit-status` | **PASS.** Dispatch and watch exited 0. At `fbfb053c`, Ubuntu CPython 3.12.10 with NumPy 2.5.4 ran `python -m unittest -v loe_bench.tests.test_tracka_readout loe_bench.tests.test_tracka_secondary`. All 33 passed in 14.937 seconds. Both synthetic subjects passed attestation verification. The `select` and `readout` jobs were skipped. [Synthetic run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46176191476). |
| Automatic source-pin workflow on branch push and `gh run watch 46176176150 --exit-status` | **PASS.** At `fbfb053c`, the Ubuntu job used CPython 3.12.10 and NumPy 2.5.4. Both tests in the workflow command passed in 0.037 seconds, watch exit 0. [Source-pin run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46176176150). |
| `git diff --check`, workflow YAML and relative Markdown links | **PASS.** Rechecked the workflow after a static parse found an unquoted `--only-binary=:all:` in a plain YAML scalar. The corrected workflow parsed and all 17 relative Markdown links resolved. |

## Handoff

The installed-source gate and frozen forecast paths have no diff from the branch base. The packaged, tagged and checked-out freeze manifest all match SHA-256 `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d`. The local and remote freeze tag object `cb551bbc3031e7df10cfd676df5cd1de10317def` peels to `6712f32cdfb1252d66e192d770deaa867808a375`. Production readout and deployment are `NOT_RUN`. No protected TEST, sealed or private files were opened. The card made no OSF or Zenodo writes and used no paid APIs or GPU.

Published scorer pins also apply to report-only edits. Place integrated behavior in unpinned files, exercise the published pin fixture locally, and check the read-only pin workflow when a scorer path changes. Use this receipt for the Planner's lane handoff and memory update and the next external review. [Pin workflow](../../../.github/workflows/tracka-source-pins.yml).
