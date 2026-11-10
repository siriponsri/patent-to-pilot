# Specification reconciliation

Documentation-only package; no experiment, new protocol adoption or runtime change.
Base: 20e5fcaa106d11fbbc58be7f4dedbda87a86a631.

Current SACR-v0 specification and generated-view policy proposal contained obsolete
implementation statements. The spec said acquisition and orchestration were pending
despite later appended checkpoints; the policy said the controller received only raw
bytes/metrics despite typed generation adapters. These have been replaced with current
implementation boundaries and linked audit records.

The spec now distinguishes individual mechanical proposal rejection inside a valid
envelope from malformed-family rejection. The former exists; the latter remains an
owner proposal. Inspection of sacr_generated_view.py confirms non-EOS and invalid
view envelopes raise GenerationEvidenceFailure; sacr_journal.py preserves FAILED
evidence and costs. No GENERATION_REJECTED continuation has been implemented.
Controller generated adapters and replay entry points were inspected; this was not
a new runtime test of their behavior.

The spec retains all candidate arithmetic, cohort/denominator, matched-control and
fidelity requirements. It records failed CPU-003 and locally verified packaging without
claiming callback success. CPU-004 owner approval remains pending. R1 actual isolation,
eligibility and baseline/native parity, actual generation/fidelity/resources and R3–R6
remain incomplete. No benchmark data, remote process or model was accessed this round.

Validation: local Markdown target existence and JSON syntax checked; git diff --check
passed. No tests were rerun because no runtime behavior changed. Prior historical
audits/declarations are preserved. The readiness snapshot remains a dated historical
snapshot rather than a current execution certificate.
