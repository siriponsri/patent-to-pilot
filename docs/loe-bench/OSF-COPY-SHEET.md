# OSF copy sheet for the browser agent

**AUDITED: YES** at commit `52908944f8d659a955e3fdc4316a4b6080691ce6` (main planner, 28 November 2026). The authors confirmed the disclosure statements on 28 November 2026.

This sheet tells a browser agent (GPT-6.2 Sol high with the Chrome extension) exactly what to enter on OSF to register the Market Window Dossier / LOE-Bench preregistration. The owner signs in to their own OSF account; the agent never sees or types a password. Background: [submission procedure](OSF-SUBMISSION.md), [preregistration](PREREGISTRATION.md), [plan](PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

## 1. Rules for the agent

1. **Use only the owner's signed-in session.** If OSF asks for a login, stop and ask the owner. Never enter credentials.
2. **Copy text verbatim** from `TEXT-SOURCE-PREREGISTRATION.md` in the upload folder (section 5), which is byte-identical to the audited commit. Do not paraphrase, shorten, translate or "improve" any text.
3. **Verify every attachment's SHA-256** against section 5 before uploading. Stop on any mismatch.
4. **Upload only the files listed in section 5.** Never upload raw data, files from `_private_artifacts`, `.env` files, protected test outputs or anything not listed.
5. **Stop before the final Register click.** Show the owner a summary: title, authors, licence, access choice, the count of filled fields and the attachment list. Click Register only after the owner types `submit` in the agent chat.
6. **After registering, do not edit or withdraw.** Download the registered PDF and report the registration URL, DOI (if shown) and timestamp to the owner.
7. **If a field has no mapping below**, enter `See attached PREREGISTRATION.pdf, section <name>` or `Not applicable`, and list that field in the summary for the owner.

## 2. Project setup

| Step | Value |
|---|---|
| Create project | Title: `Market Window Dossier: LOE-Bench preregistration`. Leave it private until registration |
| Contributors | The owner's account only (owner decision, 28 Nov). Do not add other contributors. The advisor, Asst. Prof. Dr. Tuchsanai Ploysuwan, is named as co-author in the registration text (Metadata → Authors) and appears in the attached PDF. The OSF citation line will therefore list only the owner |
| Affiliation | King Mongkut's Institute of Technology Ladkrabang (KMITL), School of Information Technology |
| Licence | CC BY 4.0 for the registration text. Source and code rights follow the repository's Apache 2.0 licence and each data source's terms |
| Subjects | Medicine and Health Sciences → Pharmacy and Pharmaceutical Sciences; Physical Sciences and Mathematics → Computer Sciences; Physical Sciences and Mathematics → Statistics and Probability |
| Tags | generic drugs; biosimilars; freedom to operate; forecasting; preregistration; Orange Book; benchmark; selective prediction |
| Access | **Public immediately** (owner decision, 28 Nov). Do not set an embargo |

## 3. Registration form

Choose **Registrations → New registration**. Pick the template named **Secondary Data Preregistration**; OSF may label it "Preregistration for Secondary Data Analysis" (Van den Akker et al. 2021, [doi:10.15626/MP.2020.2625](https://doi.org/10.15626/MP.2020.2625)). Then fill each field from the matching section of [PREREGISTRATION.md](PREREGISTRATION.md).

| OSF field (match by meaning) | Source section in PREREGISTRATION.md |
|---|---|
| Title | Document title (line 1) |
| Description or summary | Plain-language summary |
| Authors, affiliations, licence, subjects, access | Metadata, then section 2 above |
| Research questions | Study Information → Research questions and hypotheses (questions part) |
| Hypotheses | Study Information → Research questions and hypotheses (H1, H2, H3 with direction and α) |
| Name and description of dataset(s); data identifiers; access and access dates | Data Description → Datasets, availability, identifiers and access dates |
| Data source and collection procedures; codebook | Data Description → Collection procedures and codebook |
| Sample, splits, admission or gating | Data Description → Splits and blinded admission |
| Prospective component (if the form has a free field) | Data Description → Track A prospective protocol |
| Manipulated and measured variables | Variables → Manipulated and measured variables |
| Unit of analysis, missing data, outliers, weights | Variables → Unit of analysis, missing data, outliers and weights |
| Prior publication or dissemination | Knowledge of Data → Prior publication and dissemination |
| Prior knowledge of the data (per author) | Knowledge of Data → Prior knowledge of the data |
| Statistical models | Analyses → Statistical models |
| Effect size and statistical power | Analyses → Effect size and statistical power |
| Inference criteria; handling of assumption violations or failures | Analyses → Inference criteria and analysis failures |
| Reliability and robustness | Analyses → Reliability and robustness testing |
| Exploratory analyses | Analyses → Secondary and exploratory analyses (includes C2 L1e, C3 competition at launch, C4 Medicaid demand, C5 price scenario, C9 prospective RL) |
| Other, limitations, deviations | Analyses → Limitations, deviations and release |

## 4. Text to check after pasting

The agent confirms that these exact strings appear in the pasted form before showing the owner the summary:

- `H1`, `H2` and `H3`, together with `α = 0.025` (one-sided)
- `+9.80`, `+5.49` and `+13.00` (development-only results), with no `+24` anywhere
- `ingredient identity, cutoff and horizon` (the input description for the old L1 arm)
- `not an FTO or legal opinion`
- `2027-01-31 23:59 UTC` (the Track A freeze deadline)

## 5. Attachments

All files are already downloaded and hash-verified in the owner's folder **`C:/Users/User/Desktop/OSF-UPLOAD-LOE-Bench/`**. Upload these ten files from that folder. Do not upload `TEXT-SOURCE-PREREGISTRATION.md`, which is only the text source for pasting.

| File in upload folder | Repository path at the audited commit | SHA-256 |
|---|---|---|
| `PREREGISTRATION.pdf` | `docs/loe-bench/PREREGISTRATION.pdf` | `21fe6ceb0811e62f3235ea91a2b8cf1cb7a02886e8266ac870d5bc09a76be73a` |
| `FROZEN_CONFIG.json` | `loe-bench/data/FROZEN_CONFIG.json` | `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39` |
| `S0_INPUT_MANIFEST.json` | `loe-bench/data/S0_INPUT_MANIFEST.json` | `7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d` |
| `L1_FROZEN_CONFIG.json` | `loe-bench/data/L1_FROZEN_CONFIG.json` | `e5e5ade357ee5faf83efa0ce24ad25feddacdfcbf49ddd817a6b10e494a9ef16` |
| `L1E_FROZEN_CONFIG.json` | `loe-bench/data/L1E_FROZEN_CONFIG.json` | `dd1dd4ac0d592a48de081c5fc29f68e0ccc78fd7a8daad771d280c7f15901e40` |
| `C3_SPEC.json` | `loe-bench/data/C3_SPEC.json` | `8179101bb7a0adf9e8659bcb0978c73bd32ee869506a50027537741a45e3b0fd` |
| `C4_SPEC.json` | `loe-bench/data/C4_SPEC.json` | `c0644bb4c1ed9d6050e256191c85bb34dd120a73b6da78850a1faf80e2c400f0` |
| `C9_SPEC.json` | `loe-bench/data/C9_SPEC.json` | `e865e719e7fcbd8fa636164270c4c3959d007cb9357cbedb59d7802b8951f28f` |
| `REGULATORY-RULES.md` | `docs/loe-bench/REGULATORY-RULES.md` | `9e2f6d3173848636b0ba81f6509735a087f2b9f1632dbdfb58aae12f0c519331` |
| `OSF-HASH-MANIFEST.txt` | `docs/loe-bench/OSF-HASH-MANIFEST.txt` | `8806e99c3c008c586cea5e1a5efde159a7bf96a985eb2ce221531d1e45849c4a` |

If the agent can compute hashes, it checks them before uploading. If it cannot, it relies on the main planner's verification: the folder was downloaded from `https://raw.githubusercontent.com/siriponsri/patent-to-pilot/52908944f8d659a955e3fdc4316a4b6080691ce6/<path>`, and every hash matched on 28 November 2026. If any file is missing or renamed, stop and ask the owner.

## 6. Audited commit and hand-back

- Audited commit: `52908944f8d659a955e3fdc4316a4b6080691ce6`. The registered text is `docs/loe-bench/PREREGISTRATION.md` at that commit (LF SHA-256 `dc485bb748bca2645253c95aa88a030921e8cdca9bdb2fa8f3754163e957d4fc`). Commit-specific links have the form `https://github.com/siriponsri/patent-to-pilot/blob/52908944f8d659a955e3fdc4316a4b6080691ce6/<path>`.
- After registration, the owner gives the main planner the PDF that OSF generates for the registration. The main planner records its SHA-256 in `loe-bench/data/PREREG_LOCK.json`. That file is the only key that unseals the test.
