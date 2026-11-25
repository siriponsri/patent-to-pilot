# Writing corrections register (22 Nov 2026)

**25 November update to W3.** [PDF identities, page locators and denominators](../evidence-scope/00-organization.md#original-source-corrections) resolve the original Paper 53 statistic. Older generated figures and drafts still require a deliberate S5 revision; keep the 692, 725 and 905 cohorts separate.

**Source:** owner note 22112026, `01_OWNER_DIRECTION_AND_DECISIONS.md` § "Corrections to carry into writing" and
`audit/CURRENT_REPOSITORY_AUDIT.md` § "Corrections needed in source documents" (owner-local, read-only).
**Method:** each correction is a dated note or a struck-through phrase next to the original text. No history is rewritten and
no frozen protocol file is edited.

| # | Over-claim | Correction | Where applied |
|---|---|---|---|
| W1 | A1's missing filing-date/own-unit masks "can only have hurt" T and C, so the T/C numbers "understate" a masked route | Direction not established: masks change eligibility, ranking and window contents, so the effect can go either way. PARK stands with the defect disclosed; size and sign unknown | `docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md` §4a (correction note; also supersedes the same sentence in frozen amendment 3 §2), `docs/maintenance/AGENT-LESSONS.md`, `docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md` ("cannot have helped A1") |
| W2 | PatenTEB 80/10/10 split makes a DAPFAM family "about eight times more likely" to be in train; public-test overlap read as a training audit | Withdrawn odds. Public-test overlap shows a shared family pool only; training overlap, its size and direction are unmeasured. Consequence kept: PatEmbed reported separately with caveat | `docs/healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md` §3 (correction note), `AGENT-LESSONS.md`, `NEXT-ACCOUNT-HANDOFF-20261122b.md` |
| W3 | Paper 53's "37.1%" reused (and in outline v3 turned into "37.1% of relevant items are not in the Top-100") | Marked **denominator to be recovered; do not reuse** at each occurrence, plus a banner per file. B53's own π@100 = 0.371 (905 queries) is a separate number | `docs/writing/is2/IS2-OUTLINE-v3-20261122.md`, `IS2-SHORT-PAPER-DRAFT.md`, `IS2-DELIVERABLES.md`, `COMMITTEE-RESPONSE-DRAFT.md`, `PAPER86-AND-P1DAPFAM-SELECTION.md`, `SLIDES-OUTLINE.md`, `results/B53-STAGE1-RESULTS.md` |
| W4 | A3 four-model mix implied as diverse; smoke read as "OK on 4 models" | Panel is one Claude, two Qwen, one DeepSeek (three families, not four independent lineages); smoke = format feasibility only (Haiku truncated, keywords missing); A3 is one hypothesis, not decisive for all acquisition | memo §4b correction note, `docs/maintenance/API-BUDGET-PROPOSAL-20261122.md`, `NEXT-ACCOUNT-HANDOFF-20261122b.md`, `AGENT-LESSONS.md`, outline v3 note |
| W5 | Outline v3 §4: PatEmbed caveat makes the exposure ceiling "if anything, conservative" | Direction not established; state the overlap uncertainty | `docs/writing/is2/IS2-OUTLINE-v3-20261122.md` §4 (struck phrase plus note) |
| W6 | Memo §4: if acquisition stays null, "the headline can rest on the maintenance contribution" | Superseded by owner N03: no automatic maintenance headline; an unmet retrieval objective is reported as unmet | memo §4 (inline correction) |

## Not edited (flagged for the owner or a later build)

- **Frozen files:** `G03-DEV-PROTOCOL.md`, `G03-DEV-AMENDMENT-1/2/3-*.md` are unchanged. Amendment 3 §2 still contains
  "which can only have hurt T and C"; the memo §4a correction note supersedes it.
- **Built IS2 paper sources and outputs:** `docs/writing/is2/paper/content_en.py`, `content_th.py`, the figure SVG/PDF files
  in `figs_en/` and `figs_th/`, `IS2-paper-*.docx/.pdf` and `IS2-short-paper-draft.docx` still print Paper 53's 37.1%. They
  are code-generated outputs and were not changed in this documents-only pass; fix them at the next rebuild (outline v3 build
  plan), after the Paper 53 denominator is recovered.
- **Coordinator-owned files:** `HANDOFF.md`, `CLAUDE.md`, `INDEX-PLAN.md`, `README.md` were not edited. `HANDOFF.md` repeats
  "smoke on 4 models done" without the format caveat.
