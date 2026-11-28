# PREREG2 | Market Window Dossier preregistration v2

**Draft ready for main-planner audit.** Branch `loe/PREREG2` follows the fetched `research/loe-bench` at `8f8e0568469e71cfce1c2d8e9b018429f122066e`. This receipt is the executor handoff and project-memory entry. The main planner owns lane memory, lane handoff and the copy-sheet audit.

## Changes by section

| Section | Change |
| --- | --- |
| Title, Plain-language summary and Metadata | Aligned the title and product scope with D41. Defined the US FDA approval capture endpoint and its limits. Filled author order, roles, affiliations, licence, subjects and access. |
| Study Information | Reconciled the frozen configuration's pending-alpha entry with T4c's one-sided 0.025 decision. Kept H1 → H2 → H3 and the +10 pp usefulness threshold. |
| Data Description | Preserved the full blinded C′ gate and its stop and retry conditions. Specified the core and optional Track A arms. Kept the 31 January 2027 23:59 UTC freeze deadline and the November 2027 and 2028 maturities. |
| Variables | Preserved the FDA approval endpoint, active-moiety eligibility and missing-data rules. |
| Knowledge of Data | Kept the B0–B2 smoke, E1 profile, T4 decoding, NDA-only simulation counts and development search disclosures. Marked the T1v3 estimates as superseded by the post-REG FREEZE replay and added the L1/C2, C3/C3b and C4/C4b exposure. The headline development contrasts are H1 +9.80 [+0.14, +19.65], H2 +5.49 [−2.00, +11.25] and H3 +13.00 [+3.27, +23.17] pp. The draft includes per-author confirmations. |
| Analyses | Preserved the primary model, bootstrap and stopping rule. Pinned L1, L1e, C3, C4 and C9. Added the C2 and C3b development results, the vintage-uncontrolled C4 findings, the FDA AMP scenario, descriptive C6–C8 checks and the C10 ethics gate. Mirrored the C9 protocol with the v2 pin. |
| Limitations, deviations and release | Directed the owner and main planner to the audited copy sheet and distinguished the draft PDF from the OSF-issued seal artifact. |

[Registration draft](../PREREGISTRATION.md) · [Submission procedure](../OSF-SUBMISSION.md) · [C9 protocol](../C9-PROTOCOL.md) · [Copy sheet](../OSF-COPY-SHEET.md)

## Attachment identities

The text and JSON hashes are SHA-256 of the exact UTF-8, LF Git blob bytes at the corresponding commit. The [attachment manifest](../OSF-HASH-MANIFEST.txt) supplies full commit IDs. The draft PDF hash is for its binary bytes. It will change if re-rendered after an audit edit.

| Attachment | Commit for the blob | SHA-256 |
| --- | --- | --- |
| `loe-bench/data/FROZEN_CONFIG.json` | `8f8e0568` | `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39` |
| `loe-bench/data/S0_INPUT_MANIFEST.json` | `8f8e0568` | `7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d` |
| `loe-bench/data/L1_FROZEN_CONFIG.json` | `8f8e0568` | `e5e5ade357ee5faf83efa0ce24ad25feddacdfcbf49ddd817a6b10e494a9ef16` |
| `loe-bench/data/L1E_FROZEN_CONFIG.json` | `8f8e0568` | `dd1dd4ac0d592a48de081c5fc29f68e0ccc78fd7a8daad771d280c7f15901e40` |
| `loe-bench/data/C3_SPEC.json` | `8f8e0568` | `8179101bb7a0adf9e8659bcb0978c73bd32ee869506a50027537741a45e3b0fd` |
| `loe-bench/data/C4_SPEC.json` | `8f8e0568` | `c0644bb4c1ed9d6050e256191c85bb34dd120a73b6da78850a1faf80e2c400f0` |
| `loe-bench/data/C9_SPEC.json` | `519d0a94` | `e865e719e7fcbd8fa636164270c4c3959d007cb9357cbedb59d7802b8951f28f` |
| `docs/loe-bench/REGULATORY-RULES.md` | `8f8e0568` | `9e2f6d3173848636b0ba81f6509735a087f2b9f1632dbdfb58aae12f0c519331` |
| `docs/loe-bench/OSF-HASH-MANIFEST.txt` | `511adfbd` | `f944099845348ce488e5765cf7ebeefe038b7777b960a05f02b8138c721db156` |
| `docs/loe-bench/PREREGISTRATION.pdf` | PREREG2 PDF and receipt commit | `b2a511ac2202c205b180e8b047a8f42da995d8e150777dc0995558db49b0181a` |

- Markdown source revision `511adfbd2988668286fe986386fee0c609f8dfb8`, LF SHA-256 `ee1a2596384fb28bafd6a20874b6c413b13267be16412f165867dd200fe6a931`.
- C9 v2 pins `loe-bench/data/L1E_FROZEN_CONFIG.json` at the attachment digest above and `loe-bench/loe_bench/l1e_prompt.py` at LF SHA-256 `07e43988f7aeecacf9a8078b2cf1f519608eaf5828666110def92fd380f9f1e9`, both from `8f8e0568469e71cfce1c2d8e9b018429f122066e`.
- C9 v1 predecessor LF SHA-256 `2dc467fa014755ffd562d646cb47dcf252226d48010f9b786221d601a1569604`. The v2 change pins the prompt contract. The training, scoring and budget rules are carried forward.

## Verification

- **PASS**, `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` on CPython 3.12.10, 220 tests in 7.142 s, exit 0. The existing Purple Book fixture emitted non-failing file-handle `ResourceWarning` messages.
- **PASS**, checked Markdown heading equality below the title, byte equality for the blinded admission and inference sections, required OSF strings, the absence of email addresses, and the registered development values. Verified all ten attachment paths against copy-sheet section 5 and recomputed all eight manifest digests from their commit-pinned bytes. Checked 69 repository link targets by revision and path.
- **PASS**, compared the six frozen configuration and specification blobs, the copy sheet and `seal.py` to the fetched base. Every comparison matched. The C9 specification is the sole updated machine specification.
- **PASS**, rendered the committed Markdown through markdown-it-py with table support and headless Chrome using A4 print CSS. The first visual pass found the L1e opening attached to the preceding list. Corrected the Markdown boundary and re-rendered. Kept the two-row recall table together in the final PDF. Raster-checked the 17-page layout, verified page numbers and text bounds, and checked extracted headings, dates, values and author markers.
- **NOT_RUN**, C′ gate, protected test scoring, prospective predictions, C9 training and C10 reader testing. No protected results were accessed. The registration lock was absent. This card set no release variable and used no GPU or paid API. The root project suite was outside this documentation and specification-pin check.

## Main-planner audit

1. Obtain both authors' confirmation of the two access statements and the statements on dissemination, additional access and competing interests. Four occurrences of `[AUTHOR CONFIRMS]` are the only remaining field markers in the Markdown and PDF.
2. Check how the L1/L1e prospective and authorized C′ execution will satisfy the full-roster and first-200 gates with their development-era pins. The draft treats development roster hashes as provenance and requires new run manifests plus authorization.
3. Confirm the C4 coverage wording. The requested 14–26% description fits the first four origins (14.3–26.0%, over fit, annual and Q4 windows). The C4b table shows 14.3–35.7% over all seven origins. Both ranges appear with their scope. [C4b coverage](C4b.md#coverage-and-linkage)
4. Verify the C9 v2 match and carry forward the January runner, roster and budget admission. The C2 renderer is pinned. C9 prompt-length, throughput and matched training feasibility remain unmeasured.
5. Resolve the author markers, regenerate the PDF if the text changes, and record the audited commit and exact upload digests in copy-sheet sections 5 and 6. The copy sheet still carries its draft audit markers. Use the OSF-issued PDF for the seal process after the owner's submission.
