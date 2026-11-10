# R1 curator preparation
CPU-only CLI binds preparation to the committed A14 report, validates dev query IDs/text and expected missing count, copies query bytes unchanged, projects the corpus and writes a hash/count-only completion receipt last. Existing destinations fail closed; partial failures remain. No isolation is configured and no model is loaded.

See [curator runbook](CURATOR_RUNBOOK.md) for exact commands, transfer allowlist, independent hash checks and the required curator/environment decision. Real staging remains NOT_RUN.

67 tests passed in 5.80s; Ruff passed. Six preparation cases cover unchanged CRLF bytes, receipts, existing destinations, out-of-dev IDs/labels/report/missing-count refusal and partial failure preservation. All data was synthetic. No real query/corpus/label read or GPU/paid work.

Read-only path discovery first used a nonexistent directory and unsupported Windows wildcards; corrected directory/glob search located the P-dev source in the tracked launcher. A documentation orchestration call failed JavaScript parsing before execution; apply_patch then wrote the runbook. No data/source mutation from those failures.

Next obtain curator/operator and isolated environment; independently draft SACR specification/fidelity and parity declaration while operational handoff is pending.
