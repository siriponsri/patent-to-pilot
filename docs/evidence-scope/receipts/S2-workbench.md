# S2 local Workbench alpha

The owner authorized S1 and S2 together under D28. All five S2 tasks delivered a local engineering alpha on Windows. From a checkout, run `python scripts/ptp_run.py --serve --open` or double-click [Start-PTP.cmd](../../../Start-PTP.cmd). Choose **เปิดโต๊ะอ่านเอกสาร**, select a family and click **อ่านพร้อมหลักฐาน**. Select another preset in the same family to compare the previous reading. Open a source-stated edge to read the original claim and use the parent link to follow the next dependency. Open a saved run from the reading history after restarting with the same data directory.

## Public examples

| Family | Presets | One task a reader can perform |
|---|---:|---|
| Controlled-release metformin · US8323692B2 | 3 | Compare flotation, expansion and coating restrictions under separate claims depending on claim 1. The publication contains 37 claims. |
| Taste-masked formulation · US20120276199A1 | 2 | Follow claim 15 → 2 → 1 or claim 18 → 17 → 1. The publication contains 36 claims. |
| Dry-powder inhaler · US20120145150A1 | 2 | Compare outlet paths in claims 10 and 11 with a common parent 9. The publication contains 30 claims. |
| Child-resistant medicament pack · US20070289893A1 | 2 | Inspect the distinct layer structures behind two claims describing the end of a cut. The publication contains 32 claims. |
| Paper clip · US20140137391A1 | 2 | Compare wire in claim 3 and plastic in claim 4 against a common claim 1 feature. The publication contains eight claims. |
| Electronic Transactions Act | 3 | Compare section 9(1) in two historical editions. Ask who signed an absent contract and inspect the unresolved requirement. |
| Medical Devices Act | 2 | Read establishment registration and the express advertising cross-reference in the 2551 text. |
| Drug Act | 2 | Compare the restriction on exaggerated claims with the conditions for advertising through print. |
| National Health Act | 2 | Inspect health-information confidentiality or the information-before-service provision and the specified emergency condition. |
| Official Information Act | 3 | Compare budget records, public-facing staff manuals and requests for other official information. |

The 23 runs across ten families are included as [saved JSON exports](S2-example-traces.json). Each can be inspected directly as JSON or reproduced by running its `example_id` in a fresh local store. They include 22 runs with all preset requirements bound and one intentionally qualified case. These are expected behaviors under curated questions and editorial glosses. They provide no estimate of retrieval accuracy on unfamiliar user questions or documents. The local reader ships excerpts and explains their named scope; general conversation, clinical advice, present-day compliance and patent validity are outside the examples. SHA-256 for the canonical excerpt text is distinct from the upstream document digest. Historical editions may have subsequent amendments. See the [asset ledger](S2-sources.json), [source and rights decisions](S2-sources.md), [health-law locators](S2-health-law-source.md) and [patent branches](S2-pharma-source.md).

## Acceptance and replay

| Check | Evidence |
|---|---|
| S2-T01 · Source selection | Nineteen upstream files, including the USPTO terms capture, were hashed from the private artifact directory. Every preset resolves to a canonical edition and its appropriate original records. Public excerpts and project glosses run offline after checkout. |
| S2-T02 · Structure and provenance | Tests check exact Unicode source offsets, different editions with the same provision number, dates, explicit claim parents, ambiguous references, table and embodiment constraints. Tests cover an unspaced Thai reference and numeric false matches. Plans and rights cover only source-supported bindings. |
| S2-T03 · Bounded local policy | FTS5 nominates two candidates per requirement. The controller keeps, reranks, performs a scoped lookup or returns a qualified result. Each trace records the before/after list, reasons and additional action usage. Product budgets apply after the seed lookup. S3 separately includes the initial seed in its own frozen four-action ceiling. Engine fixtures exercise the three recovery states, a missing scope and a zero supplemental budget. |
| S2-T04 · Browser and graph | Chromium drove the normal launcher through all 23 preset selections and inspected their returned citations. The regression covers changed and stable wording, an unresolved signer, mouse and keyboard inspection, the two-step patent path, Thai legal references, a 37-claim publication label, export equality and browser reopen after restart. |
| S2-T05 · Persistence | The application snapshots the canonical source identity and trace transactionally in the Workbench store. A changed source needs a new version. All 23 exports were reopened through HTTP by run ID. Regression fixtures exercise actual restart, historical recovery, wrong versions and missing saved IDs. |

Code regression paths are [engine and HTTP](../../../tests/test_scope_reader.py) and [Chromium](../../../tests/test_scope_reader_browser.py). Run `python -m pytest -q tests/test_scope_reader.py tests/test_scope_reader_browser.py tests/test_s1_packet.py` with the repository dependencies and local Chromium available. The final combined run passed 17 tests, including the expanded 23-preset browser walkthrough. To check the existing comparison workflow, run `python scripts/ptp_run.py --doctor` and `python scripts/ptp_run.py --smoke`. Both passed. To audit the research packet separately, run `python scripts/research/s1_packet.py verify`.

**Project-wide code gate:** On 25 November 2026 the full pytest run with the project venv site-packages available reported 2,769 passed, 8 failed, 7 skipped and 1 expected failure in 467.94 s. All eight failures were the repository's documented SACR r2/r3 supervisor budget cases (nan, inflated, erased, insufficient in each). There were no additional failures. The run emitted two warnings.

No pod, dr-train job, paid inference or dependency installation was used in S1 or S2. No product scoring used S1 reserved DEV. No user team or independent domain professional evaluated usability or the glosses. S4 can start from this release and test installation, human tasks, redistribution and deployment readiness independently. The documented acquisition experiment belongs to S3.
