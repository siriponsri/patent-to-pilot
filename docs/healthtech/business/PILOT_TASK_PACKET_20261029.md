# Public-case pilot task packet

Status: `PREPARED / ENGINEERING_DRY_RUN_ONLY / NOT_VALIDATED`. This packet is a reversible preparation artifact for HT-G5 / HT-W16. It contains no participant data, no outreach, no participant timings, no purchase, and no customer claim.

## Purpose

Test whether an entrepreneur or investment analyst can inspect and correct a named medical-device dossier before a concrete licensing, diligence, or information-request discussion. The task measures total user burden, including correction and export review, rather than model generation time alone.

## Case and inputs

- Case: one named device from the frozen Boston Scientific, Stryker Neurovascular, or Cook Medical public cohort.
- Starting state: a versioned dossier export, source list, evidence table, retrieved candidates, disclosed links, and unresolved items.
- User decision: identify the next information request and whether the dossier is ready for that discussion.
- Data boundary: public, source-backed local artifacts only; no private company information and no provider transfer.

## Task script

1. Open the dossier and identify the source for one key product or regulatory fact.
2. Inspect one feature-evidence row and classify each patent entry as `disclosed_link`, `retrieved_candidate`, or `unresolved`.
3. Compare two candidate patents and record the source locator supporting the stronger entry.
4. List missing information needed for the next decision; do not infer clinical suitability, FTO, validity, or approval probability.
5. Correct one deliberately seeded issue in the editable dossier.
6. Export the corrected dossier and state whether it is ready for the next discussion.

Planned task duration is `30-45 minutes`; this is a target for study design, not an observed result.

## Engineering dry-run evidence

The committed local runner at `scripts/healthtech/run_pilot_task.py` completed one
Cook Zenith dissection case from the local public dossier cohort. It inspected
the FDA `pma_number` field, seeded and corrected one edit, published history
versions `1` and `2`, and exported selected version `2` in local-research JSON,
English, and Thai forms. Engineering execution time was `0.1291642999931355`
seconds with `0` provider calls, `0` network calls, and `USD 0.00` paid cost.

The product-display projection was checked separately and returned
`BLOCKED_LOCAL` for Cook marking and Google-derived patent sources without
writing an external payload. This is backend engineering evidence only; it is
not participant task time, usability evidence, commercial validation, or a
service-level promise. Canonical audit:
`docs/healthtech/audits/luna-long-run-20261029-ht-g5-pilot-task-20261029/`.

The current aggregate engineering analysis covers the Cook case plus all three
Philips dossiers. It contains `4` successful receipts, `20/20` artifact hashes
passing, total engineering execution time of `0.4829` seconds, median time of
`0.1197` seconds, `0` provider calls, `0` network calls, and `USD 0.00` paid
cost. All four external projections are `BLOCKED_LOCAL` where local-only
marking or Google-derived patent sources are present. The analysis is at
`results/healthtech/ht-g5-pilot-task-analysis-20261030-r1/` and is a
reproducible engineering summary, not participant timing or commercial
validation.

## Correction and time form

| Field | Record |
|---|---|
| Participant code | `OUTSIDE_PRIVATE_RECORD` |
| Case/device | `<named case>` |
| Task start/end UTC | `<NOT_RUN>` |
| Total elapsed time including correction | `<NOT_RUN>` |
| Time to first source locator | `<NOT_RUN>` |
| Time to corrected export | `<NOT_RUN>` |
| Incorrect, missing, or rejected items | `<NOT_RUN>` |
| Manual support time | `<NOT_RUN>` |
| Export opened after completion | `<NOT_RUN>` |
| Subsequent project started | `<NOT_RUN>` |
| User-reported next decision | `<NOT_RUN>` |

Participant identities, consent, contact details, and recordings stay outside the public repository.

## Bounded pilot-offer draft

Status: `DRAFT / NOT_SENT / PRICE_NOT_SET`.

- Input: one named medical device or comparator, permitted public source links, and one concrete diligence question.
- Deliverable: one versioned evidence dossier in English or Thai, source/locator table, retrieved-candidate section, unresolved-items list, and next-information request list.
- Turnaround: proposed `5 business days` after source access and scope confirmation; not an observed service level.
- Support: one bounded clarification round and one export correction round; additional research is separately scoped.
- Exclusions: clinical advice, complete FTO, legal opinion, patent-validity conclusion, regulatory advice, investment recommendation, and unlicensed/private-source ingestion.
- Price: `<OWNER TO SET BEFORE ANY OUTREACH OR OFFER>`.

No offer has been sent, accepted, purchased, or validated. Manual delivery effort and compute cost must be recorded separately in any future authorized pilot.

## Acceptance boundary

This packet is ready for owner review and an authorized usability/commercial study. It does not establish usability, willingness to pay, repeat use, ROI, product-market fit, or commercial demand.
