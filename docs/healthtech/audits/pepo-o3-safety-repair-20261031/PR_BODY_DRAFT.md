# Draft only — publish after applying and testing the repair candidate

The HTTP/vector/local-generation path works for the named development cases.
This repair closes unsafe R1 ledger bootstrapping and request/availability
binding gaps, preserves billing after failed output validation, and adds
adversarial offline coverage. It does not execute a paid comparison.

The existing cumulative USD8 owner authorization is already present. Paid R1
work still requires independently reconciled all-attempt history, controlled
old writers, one canonical ledger, current scoped availability and exact
route/field-rights checks. A credit observation does not prove project spend or
guarantee shared-account availability.

O4 engineering receipts remain evidence for the three-case product path.
Research is partial: the Stryker holdout table is historical reference only;
current matched fixed/adaptive comparisons and per-job provenance are still
required. Passing O3 alone does not complete the four-outcome goal.

Replace this draft's validation paragraph with the exact integrated commit and
its test receipt before publishing. Current isolated repair validation is in
docs/healthtech/audits/pepo-o3-safety-repair-20261031/verification.json.
