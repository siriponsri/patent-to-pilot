# OSF submission procedure (owner)

This is the procedure for registering [PREREGISTRATION.md](PREREGISTRATION.md) on OSF. Only the owner can submit, because submission requires the owner's OSF account. The test stays sealed until step 6.

1. **Account and project.** Sign in at https://osf.io (an institutional KMITL login also works if offered). Create a private project named "LOE-Bench".
2. **Template.** Choose *Add a registration* and then the **"Preregistration for secondary data analysis"** template, using [OSF's guide](https://help.osf.io/article/330-create-a-preregistration).
3. **Fill the form.** Copy each section of PREREGISTRATION.md into the matching template field. Complete every `[OWNER TO COMPLETE ...]` placeholder:
   - authors and affiliations (owner; advisor Asst. Prof. Dr. Tuchsanai Ploysuwan if agreed)
   - licence (suggested: CC BY 4.0 for the registration text)
   - subjects (for example Medicine and Health Sciences; Computer Sciences)
   - access (public, or embargoed until results)
   - per-author prior-knowledge disclosures, which may follow the "Knowledge of Data" section as written
4. **Attachments.** Upload these files from the repository at the commit named in the registration:
   - `loe-bench/data/FROZEN_CONFIG.json`
   - `loe-bench/data/S0_INPUT_MANIFEST.json`
   - `loe-bench/data/L1_FROZEN_CONFIG.json` (if present)
   - `docs/loe-bench/REGULATORY-RULES.md`
5. **Submit.** Choose immediate registration or an embargo. OSF timestamps the registration.
6. **Hand back.** Download the registered PDF and give it to the main planner. The main planner computes its SHA-256 and writes it to `loe-bench/data/PREREG_LOCK.json`, which is the only key that unseals the test. Then, in order:
   1. Run the blinded C′ gate.
   2. Score C′ with the frozen models.
   3. Make the Track A prediction freeze before 2027-01-31 23:59 UTC.

Do not edit the registration after submission. Any later change is recorded as a dated deviation.
