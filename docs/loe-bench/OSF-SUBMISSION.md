# OSF submission procedure (owner)

Use the [OSF copy sheet](OSF-COPY-SHEET.md) to register the [Market Window Dossier preregistration](PREREGISTRATION.md) under the Secondary Data Preregistration template. The owner signs in and authorizes the final registration. The main planner audits the draft, obtains the author confirmations, and records the audited commit and hashes in the copy sheet before submission.

1. **Set up the project.** Use the title, sole OSF contributor, licence, subjects and tags in the copy sheet. Keep the project private during preparation. The registration is public immediately with no embargo.
2. **Fill the form.** Copy the mapped sections verbatim from the audited Markdown. Confirm each required string using the copy sheet.
3. **Verify and upload attachments.** Use the commit-specific files and SHA-256 values in section 5 of the copy sheet. The draft [hash manifest](OSF-HASH-MANIFEST.txt) pins the text and JSON attachments. The audited list is:
   - `docs/loe-bench/PREREGISTRATION.pdf`
   - `loe-bench/data/FROZEN_CONFIG.json`
   - `loe-bench/data/S0_INPUT_MANIFEST.json`
   - `loe-bench/data/L1_FROZEN_CONFIG.json`
   - `loe-bench/data/L1E_FROZEN_CONFIG.json`
   - `loe-bench/data/C3_SPEC.json`
   - `loe-bench/data/C4_SPEC.json`
   - `loe-bench/data/C9_SPEC.json`
   - `docs/loe-bench/REGULATORY-RULES.md`
   - `docs/loe-bench/OSF-HASH-MANIFEST.txt`
4. **Submit after approval.** Show the owner the copy-sheet checklist before the final Register action. Submit after the owner types `submit`, then record the registration URL, DOI if shown and OSF timestamp.
5. **Hand back the registered PDF.** Download the PDF issued by OSF and give those bytes to the main planner. The main planner records their SHA-256 in `loe-bench/data/PREREG_LOCK.json`. The registered PDF digest is the seal key. The attached draft PDF has a separate digest.
6. **Follow the registered sequence.** Run the blinded C′ gate and record its verdict. Score C′ only after PASS and authorized release. Complete the Track A freeze before **2027-01-31 23:59 UTC** and before any post-t0 outcome-source fetch.

Use a dated deviation record for any later protocol change.
