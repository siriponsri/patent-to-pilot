# Synthetic named-device example

Every identifier, device name, patent text and decision value in `input.json` is authored for engineering checks. K000001 and US000001A1–US000003A1 are synthetic placeholders, not claims about actual records. The 510(k) schema shape is demonstrated; no FDA request was made.

The fixed HT-B2 schedule searches “balloon catheter” and then “pressure sensor”. Two authored candidates should be returned within the declared 3-call/20-result cap. Every candidate remains `retrieved_candidate`; no independently sourced device–patent disclosure exists. Evidence checks compare supplied field values only.

Run from the repository root with a fresh output path as described in [runbook](../../../docs/healthtech/RUNBOOK.md). Do not use this fixture as scientific gold or present it as a public device case.
