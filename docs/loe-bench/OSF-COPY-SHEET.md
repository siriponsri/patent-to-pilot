# OSF copy sheet for the browser agent

**Audit status: DRAFT, NOT AUDITED.** Do not submit until this line reads `AUDITED: YES` with the main planner's commit SHA.

This sheet tells a browser agent (GPT-6.2 Sol high with the Chrome extension) exactly what to enter on OSF to register the Market Window Dossier / LOE-Bench preregistration. The owner signs in to their own OSF account; the agent never sees or types a password. Background: [submission procedure](OSF-SUBMISSION.md), [preregistration](PREREGISTRATION.md), [plan](PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026).

## 1. Rules for the agent

1. **Use only the owner's signed-in session.** If OSF asks for a login, stop and ask the owner. Never enter credentials.
2. **Copy text verbatim** from the audited files at the commit named in section 6. Do not paraphrase, shorten, translate or "improve" any text.
3. **Verify every attachment's SHA-256** against section 5 before uploading. Stop on any mismatch.
4. **Upload only the files listed in section 5.** Never upload raw data, files from `_private_artifacts`, `.env` files, protected test outputs or anything not listed.
5. **Stop before the final Register click.** Show the owner a summary: title, authors, licence, access choice, the count of filled fields and the attachment list. Click Register only after the owner types `submit` in the agent chat.
6. **After registering, do not edit or withdraw.** Download the registered PDF and report the registration URL, DOI (if shown) and timestamp to the owner.
7. **If a field has no mapping below**, enter `See attached PREREGISTRATION.pdf, section <name>` or `Not applicable`, and list that field in the summary for the owner.

## 2. Project setup

| Step | Value |
|---|---|
| Create project | Title: `Market Window Dossier: LOE-Bench preregistration`. Leave it private until registration |
| Contributors | 1. Siripon Srihangpiboon, the owner's account (admin). 2. Asst. Prof. Dr. Tuchsanai Ploysuwan, added by name and email as admin or read-write. **The owner must supply the advisor's email.** Admin contributors receive an approval email, and OSF approves the registration automatically after 48 hours if nobody acts |
| Affiliation | King Mongkut's Institute of Technology Ladkrabang (KMITL), School of Information Technology |
| Licence | CC BY 4.0 for the registration text. Source and code rights follow the repository's Apache 2.0 licence and each data source's terms |
| Subjects | Medicine and Health Sciences → Pharmacy and Pharmaceutical Sciences; Physical Sciences and Mathematics → Computer Sciences; Physical Sciences and Mathematics → Statistics and Probability |
| Tags | generic drugs; biosimilars; freedom to operate; forecasting; preregistration; Orange Book; benchmark; selective prediction |
| Access | **Public immediately** (recommended: the timestamped public claim is the strongest credibility signal). Alternative: embargo with an end date recorded in the summary |

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

Upload each file from the audited commit in section 6. The SHA-256 values are filled in at audit.

| File (repository path) | SHA-256 |
|---|---|
| `docs/loe-bench/PREREGISTRATION.pdf` (rendered from PREREGISTRATION.md at the audited commit) | *at audit* |
| `loe-bench/data/FROZEN_CONFIG.json` | *at audit* |
| `loe-bench/data/S0_INPUT_MANIFEST.json` | *at audit* |
| `loe-bench/data/L1_FROZEN_CONFIG.json` | *at audit* |
| `loe-bench/data/L1E_FROZEN_CONFIG.json` (card C2) | *at audit* |
| `loe-bench/data/C3_SPEC.json` | *at audit* |
| `loe-bench/data/C4_SPEC.json` | *at audit* |
| `loe-bench/data/C9_SPEC.json` | *at audit* |
| `docs/loe-bench/REGULATORY-RULES.md` | *at audit* |
| `docs/loe-bench/OSF-HASH-MANIFEST.txt` (every file above with its hash and commit) | *at audit* |

Hashes refer to the Git blob bytes (LF line endings), so download each file from its commit-specific GitHub URL rather than copying from a Windows working copy, where CRLF line endings would change the hash.

## 6. Audited commit and hand-back

- Audited commit: *at audit*
- Commit-specific links use the form `https://github.com/siriponsri/patent-to-pilot/blob/<commit>/<path>`.
- After registration, the owner gives the registered PDF to the main planner. The main planner records its SHA-256 in `loe-bench/data/PREREG_LOCK.json`, which is the only key that unseals the test.
