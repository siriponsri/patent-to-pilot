# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML/CSS/vanilla JS web app (no build step; works from file:// and a static host), packaged as a Windows desktop GUI app with Tauri. The same code serves the web app, the landing page and the desktop app. Data pipelines behind it are Python (`product/mwd/`, `loe-bench/`).

## Users

- **Primary: generic and biosimilar developers in Thailand and the region.** Business-development and R&D leads decide which molecules to develop before committing to bioequivalence or comparative trials. FTO evaluators, who are scarce, receive the cases that need patent review.
- **Secondary: academic reviewers.** The KMITL IS2 committee and journal reviewers evaluate the research and benchmark behind the product (LOE-Bench).

## Product Purpose

Market Window Dossier forecasts whether a market window will still exist at a planned launch date. It ranks which molecules deserve scarce FTO review and produces a dated, claim-traceable dossier that FTO evaluators and BD/R&D teams can act on. Success means the right cases reach review first, and every statement in the dossier can be traced to a dated public source.

## Positioning

- Every forecast uses only evidence that was demonstrably public on its date (as-of), and every claim carries its source, date, version and hash.
- Accuracy is tested on a code-sealed historical test set, and prospective forecasts are timestamped before outcomes exist. The OSF preregistration is doi:10.17605/OSF.IO/P2SMD.
- The product says "unknown: verify" instead of guessing.
- It is decision support, never an FTO or legal opinion.

## Operating Context

The user enters a molecule, dosage form, jurisdiction, decision date and planned launch date. The app returns:

- a review queue at fixed capacity ("review 1 in 5")
- a seven-part dossier: decision page, market window, competition, patents and exclusivity, Thailand and ASEAN, FTO hand-off checklist, and references
- a "time machine" replay that shows what the system said on a past date, then reveals what actually happened

The dossier is Thai first, with an English version. It exports to PDF and is handed from BD/R&D to an FTO evaluator.

## Capabilities and Constraints

- **Data.** Open US sources: historical Orange Book editions, Drugs@FDA, Purple Book, Paragraph IV lists, court records and CMS Medicaid. Thai and ASEAN registry and patent status mostly requires manual verification, and the product shows it as unknown when unverified.
- **Results so far.** Development results only. The sealed-test scoring is in progress, and Track A outcomes mature in November 2027 and November 2028.
- **Demo content.** Six development-period molecules: four catches, one false alarm and one miss. Fixture data must stay labelled FIXTURE until real data replaces it.
- **Language.** Thai and English throughout. Thai uses TH Sarabun New/Sarabun-compatible fonts.

## Brand Commitments

None binding. The owner left both the name ("Market Window Dossier", a working name) and the logo open to change (28 November 2026).

## Evidence on Hand

- `product/demo/data/` (PRD1, in progress) and `docs/product/evidence/` (C6/C7 evidence for the 6 demo molecules).
- The OSF registration p2smd, and the receipts under `docs/loe-bench/receipts/`.
- Development results in `docs/loe-bench/receipts/FREEZE.md`, `C2.md`, `C3b.md` and `C4b.md`.

There are no customers, testimonials, pricing or deployment claims. Do not fabricate any.

## Product Principles

1. Evidence before opinion: every claim traces to a dated source; unknowns stay visible.
2. Decision support, not legal advice: the qualified evaluator decides.
3. Honest track record: show misses and false alarms alongside catches, and label development data.
4. Scarce attention is the constraint: rank, summarize and hand off, rather than overwhelm.
5. Thai-first for the people who act on it, English for the reviewers who audit it.

## Accessibility & Inclusion

WCAG 2.2 AA contrast, full keyboard operation, `lang` switching between Thai and English, reduced-motion support, and a print layout for dossiers.
