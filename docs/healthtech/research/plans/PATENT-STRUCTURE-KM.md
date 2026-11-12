# Patent structure KM v0.1

Status: source-grounded design seed; NOT model-validated. Access date: 12 November 2026. Purpose: guide SACR query marking and Graph corpus extraction, not provide legal conclusions or independent semantic gold.

## Source registry

- WIPO Patent Drafting Manual, second edition,2023: https://www.wipo.int/publications/en/details.jsp?id=4706&plang=EN . Manual https://www.wipo.int/edocs/pubdocs/en/wipo-pub-867-23-en-wipo-patent-drafting-manual.pdf . Claims and description must be consistent and supported; source supports preserving claim/description provenance, not equating all embodiment details with claim requirements.
- EPO Guidelines2025,F-IV2.1, https://www.epo.org/en/legal/guidelines-epc/2025/f_iv_2_1.html . Technical features may be functional as well as structural. This edition is explicitly superseded on its website; use as a dated research reference, not current legal guidance.
- UK IPO claims factsheet, https://www.gov.uk/guidance/patent-factsheet-claims . Dependent claims refer to prior claims and add subsidiary features. Preserve dependency identity; a claim-reference edge is not a technical causal edge.

## Project annotation rules (design inferences, not quoted office requirements)

1. Keep immutable original text, field identity, document/family ID and hash. Offsets use exact Unicode string indexing; no normalization before binding.
2. Mark entity, action, object, quantity/unit, comparator, negation, condition, exception, modality and explicit reference. Preserve full enclosing sentence/context and unresolved attachments.
3. Separate title/abstract/claim/description and embodiment/prior-art contexts where provided. Do not invent unavailable sections. SACR may read only authorized query fields.
4. Every relation references source-bound spans and a typed predicate. Direction and conditions are explicit. Missing antecedents remain unresolved.
5. Alias candidates retain two separate contexts. Similar wording or functional purpose does not establish interchangeability, synonymy or transitive equivalence.
6. Masking means annotation, not removal of words or requirements. Any transformed SACR representation keeps links to the complete original requirements.

## Automatic execution contract

Mechanical validation checks schema, IDs, offsets/quotes, allowed fields and endpoint existence. It cannot establish semantic completeness. A KM-guided reviewer may label flagged/uncertain/screened but is not an independent expert. A failed reviewer must not be described as calibrated. Deterministic checks and model screening findings are reported separately.

Before retrieval freeze: output schema, prompt/KM hashes, reviewer use, acceptance and abstention rules, fixed sample IDs, fallback and ranking ties. Invalid or rejected SACR output falls back to original-query retrieval; graph relations flagged or uncertain are excluded under the frozen policy. Report accepted coverage, rejected/uncertain counts, fallback share, and all-query performance as well as coverage diagnostics. Human review is optional under the new owner-approved study.

Illustrative authored checks, not independent gold: reversing pump/valve roles must be detectable; removing 'except during cleaning' is not faithful; 'below40C' differs from 'above40C'; dependency on claim1 is not evidence that one device causes another. Preserve historical critic failures as counterexamples, not a tunable hidden test.

## Limits and next implementation

No model or corpus extraction run for this KM version. Source guidance does not validate extraction accuracy. Same-model extraction/review can share errors. Retrieval improvement cannot alone prove semantic fidelity. Next bind this design to executable schemas and existing scoring interfaces, with explicit throughput and cumulative resource accounting before dispatch.
