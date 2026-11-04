# World Patent Information venue recheck r10

Recorded: 2026-11-04 (Asia/Bangkok)

Status: `PASS_OFFICIAL_PROFILE_HTTP200_GUIDE_AND_AIMS_UNVERIFIED_NOT_SUBMITTED`

This is a source and access recheck for the existing Patent-to-Pilot goal. It
does not submit the manuscript, contact the publisher, accept terms, or change
the owner-controlled submission boundary.

## Candidate and source boundary

- Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Official publisher profile: `https://shop.elsevier.com/journals/world-patent-information/0172-2190`
- Journal Aims and Scope: `https://www.sciencedirect.com/journal/world-patent-information/about/aims-and-scope`
- Guide for Authors: `https://www.sciencedirect.com/journal/world-patent-information/publish/guide-for-authors`

## Observed results

The official Elsevier publisher profile returned HTTP 200 in a bounded
read-only request. The response was hashed locally and not stored in the
repository. The page contained the journal identity and scope markers for
intellectual-property information retrieval, AI/ML, system evaluation, and
benchmarking. This supports conditional venue fit for the current patent-
information study; it is not evidence of acceptance.

Both journal-specific ScienceDirect pages returned HTTP 403 in this Windows
environment. Their article type, word limits, abstract limits, highlights,
graphical-abstract rules, file requirements, anonymization requirements, and
declarations therefore remain unverified. No such rule is inferred from the
publisher profile, another journal, or a historical guide.

## Submission boundary

The checklist remains preparation-only and `NOT_SUBMITTED`. Owner review is
still required for the live Guide for Authors, author identities and
affiliations, funding, conflicts, ethics, data/code availability, AI-use
disclosure, article type, and final submission declarations.

## Reproduction

The machine-readable receipt records the bounded URLs, HTTP statuses, response
byte count, and publisher-profile SHA-256. It deliberately excludes raw HTML,
credentials, cookies, and private account data.
