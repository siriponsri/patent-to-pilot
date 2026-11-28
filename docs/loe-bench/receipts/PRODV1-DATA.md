# PRODV1-DATA executor receipt

The Market Window Dossier data pipeline starts at `5861d077` on `loe/PRODV1-DATA`. It implements the offline current queue, as-of evidence adapter, maintainer snapshot command and bilingual dossier export. The [endgame requirements](../ENDGAME-PLAN.md#product-v10-claude-builds-the-product-gpt-executors-build-the-data-pipelines) govern release. This receipt is the executor handoff and memory record. The Planner owns the lane handoff and memory updates.

## Run the adapter and audit

```powershell
py -3.12 -m product.mwd.current
py -3.12 -m product.mwd.audit --data-dir product/demo/data/current
```

The default private root is `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/`. The adapter checks every entry in `trackA/SHA256SUMS`, checks the core manifest against its published digest, and verifies the prior-arm hashes against the published prior-arm manifest. It uses the Track A replay's tagged S0 files, GSRS identities and archived Orange Book, PIV and court pins to reconstruct dated evidence. It joins predictions and roster by exact active-moiety key, t0 and horizon. It recomputes the M3 cutoff weights and verifies them against the stored predictions and queue metadata. The adapter stages files, audits every dossier and publishes the directory only when all checks pass. An existing output directory is preserved. Use `--out` to generate another copy.

The Orange Book edition is 10 July 2026, captured 26 July 2026. No FDA Paragraph IV edition qualifies at t0. Court evidence is present for 23 histories and combined challenge status stays `UNKNOWN` for 628. Docket sources use the Track A filing-date availability assumption and retain the corroborating references. None of the six EVP development keys appears in the current queue. Thai and ASEAN status stays unknown. Checklist search terms use the active moiety and any linked US patent numbers, with unverified WO and priority numbers empty.

## UI handoff

Read `product/demo/data/current/index.json` beside the historical data index. Its `queues` list points to `queue-2026-11-27-12m.json` and `queue-2026-11-27-24m.json`. Its `dossiers` list indexes one `dossier-<id>.json` per moiety. The `dossier_path` on each queue row points to the same dossier from either horizon.

| Field | Consumer behavior |
| --- | --- |
| `status`, `label`, `version` | Release the current view after the Planner verifies the freeze. Display “Track A t0 forecast, outcome pending” and the version from the payload. |
| `as_of`, `horizon_months`, `queue_size` | Show 27 November 2026, the active horizon and 130 expected review slots. |
| `ranked_rows[].m3_p`, `m3_rank` | Native M3 sets rank. Tied scores share a rank, and ascending key gives a stable display order within ties. |
| `queue_inclusion_probability`, `boundary` | Use the probability for membership. `in_queue` represents certain inclusion. Between zero and one, show the fractional chance from the shared boundary slots. |
| `b1_p`, `m1_p`, `p1_p`, `p2_p` | Optional native comparison scores for B1, M1, P1-RSF-OPEN and P2-COX-OPEN. |
| `dossier.forecast`, `dossier.forecast_12m` | Select the first object for the 24-month view and the second for the 12-month view. Claims for both horizons identify their horizon. |
| `disclaimer.th`, `disclaimer.en` | Use the same strings as export. The Thai string is verbatim from ENDGAME-PLAN and the English string is its translation. |
| `checklist[]` | Display owner, agency, search terms, WO numbers, priority numbers and `state`. Empty identifier lists mean the review still needs those identifiers. `lookup_url` is an agency route for manual verification. |
| `sources[].evidence_cutoff` | Display the dated basis for a derived forecast artifact. Its `public_date` is empty while its content hash and exact locator identify the artifact. |

There are no prospective outcomes in the queues or dossiers. `TRACK_A_PENDING` and `version.freeze = "pending"` describe the local generation. The version includes the core manifest SHA-256. After external verification, the Planner supplies `--verified-freeze-tag <tag> --verified-freeze-manifest <repo-relative-json-path>` and a new output directory. The adapter reads the tagged manifest via Git, requires evidence that it binds the pinned core and prior-arm inputs, and carries the tag and exact tagged manifest SHA-256 in the rebuilt version. The Planner verifies OSF and publication rights before promoting the payload. No real freeze was available on this card's base.

## Export and refresh

```powershell
py -3.12 -m product.mwd.render --dossier U-53AXN4NNHX-2026-11-27 --horizon 12 --lang th --out deliverables/PRODV1-DATA/current.th.pdf
py -3.12 -m product.mwd.render --dossier U-53AXN4NNHX-2026-11-27 --horizon 12 --lang en --out deliverables/PRODV1-DATA/current.en.html
py -3.12 -m product.mwd.refresh --out deliverables/fda-snapshots
```

The renderer accepts the ID with or without the `dossier-` prefix, or a path to the JSON. It uses the same dossier fields as the screen. The default is 24 months for a current dossier. Chrome and its Python Playwright driver are needed for PDF, and HTML uses the standard library.

Refresh writes a new UTC-dated directory marked “unregistered forecast.” It acquires the openFDA Orange Book and Drugs@FDA partitions, the official Orange Book ZIP and the latest dated FDA Paragraph IV list. The manifest records fetch time, versions, SHA-256, source failures and row differences. The JSON partitions use openFDA `last_updated` and compare with the verified S0 files. The ZIP uses its member date and compares each table with the t0-selected FDA edition. The PIV list uses the date on FDA's link and compares with a verified same-format inventory edition. That inventory comparison does not change the t0 coverage decision. The diff treats an updated row as a removal plus an addition. A failed JSON partition is discarded, the manifest records source failures and the command returns 1 when the snapshot is incomplete. The command preserves the t0 inputs and dataset. Forecasting from a refresh is a separate maintainer step. Live refresh is **NOT_RUN**. Fixtures exercise successful feed and archive inventories, a failed partition, pagination completeness and preservation of the t0 data.

## Verification

Verification was performed with CPython 3.12.10 from the repository root unless otherwise stated.

| Check | Result |
| --- | --- |
| Private `trackA/SHA256SUMS` | PASS, 14/14 entries including both prior-arm exports. |
| `py -3.12 -m product.mwd.current` | PASS, exit 0. Two queues of 651 rows each and 651 shared dossiers. M3 boundaries at 0.05604102439469676 and 0.09549036864583896 for 12 and 24 months. Each has 129 scores above the boundary and one score at the boundary, with inclusion probability 1. |
| `py -3.12 -m product.mwd.audit --data-dir product/demo/data/current` | PASS, exit 0. 16,562/16,562 claims traceable and hash-backed, zero errors or future-dated sources. The audit checks date and locator resolution. Source verification occurs during the build. |
| TH/EN export of `U-53AXN4NNHX-2026-11-27` | PASS, exit 0 for both PDF and both HTML commands. PyMuPDF opened 59 Thai and 51 English pages, all with text. Verified matching molecule, t0 and pending version, language, and the exact Thai disclaimer in HTML. The initial inspection probe found no `pypdf`; the installed PyMuPDF was used. |
| `py -3.12 -m pytest product/mwd/tests` | PASS, exit 0. 17 passed, including schema validation of all 651 current dossiers, both queue reconciliations, ties, provenance, freeze version checks and fixture refresh. |
| `py -3.12 -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | PASS, exit 0. 253 run, 243 passed and 10 skipped. Existing Purple Book resource warnings appeared. |
| `py -3.12 -m pytest` | Exit 1. 2,760 passed, 50 skipped, one xfailed and the eight standing SACR r2/r3 supervisor budget failures permitted by the repository. |
| Live FDA refresh, registered release and UI wiring | NOT_RUN. Fixture refresh is included in the product tests. |

Sample dossier IDs are `U-53AXN4NNHX-2026-11-27` (12-month top-ranked row) and `U-DKO1W9H7M1-2026-11-27` (24-month top-ranked row).

## Next action

The Planner reviews and integrates the pipeline, then verifies the Track A freeze before publishing the current queue. Claude connects the current payload and dossier export to the UI. All generated data is ignored locally, so a Planner publication commit must opt in to tracking the audited output after the release gate.
