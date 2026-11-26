# Thai inquiry attribution pilot

Under [D31](../maintenance/OWNER-DECISIONS-20261122.md), the task is to return the historical Council of State opinion and the passage that answers a specific incoming question. An issue is correct only if the source, incoming identity, opinion identity and required answer passages all match. One opinion can answer several issues. An official decision declining to address a question can be the correct answer.

## Independent preparation before execution

The first page of the official Thai Drug Act search supplied ten title records. The enrollment rule excluded a drafting matter and a reconsideration in an already represented family. Of eight selected records, seven returned verified PDFs (22 pages). One HTTP 200 response contained no usable PDF. The exposed medical-device example 344/2532 was outside the pilot. [Issuer search](https://comment.ocs.go.th/main/search?q=%E0%B8%9E%E0%B8%A3%E0%B8%B0%E0%B8%A3%E0%B8%B2%E0%B8%8A%E0%B8%9A%E0%B8%B1%E0%B8%8D%E0%B8%8D%E0%B8%B1%E0%B8%95%E0%B8%B4%E0%B8%A2%E0%B8%B2).

Three AI-assisted source readers, separate from the Executor, read disjoint groups of official PDFs before any policy output. They checked the page image and text for the incoming agency, letter reference and operative answer. They distinguished the requesting party's suggestion from the Council's own conclusion. The resulting 11 questions derive from material recited in the opinions. No separate original incoming letter was acquired. The source key includes a procedural disposition and separately attributable issues from the same matter.

The Planner verified all seven PDF checksums, the enrollment and corpus pins, and the locations of the 30 required short fragments. Each fragment is unique on its specified page. The necessary fragments for each issue fit in at most two windows of 360 normalized characters each. The runtime query fields are an opaque ID, requesting body, incoming reference and question. No query includes a required answer fragment verbatim or names its target opinion ID. The randomized order is fixed. The adjudication is source transcription by AI reviewers. It does not measure lawyer agreement or establish general legal correctness.

| Private artifact | SHA-256 |
|---|---|
| Enrollment | `1aa21ba3c8716da8b71b7d69074fff9efbc9b4548df2350a39f95500591c214d` |
| Source inventory | `c1f5911d7e13da36783e65b81bd39e4783a3c98c11ae095a72a4c49381ca601e` |
| Opaque runtime corpus | `f67208e38a8653dee9a8766e9033741bc00aaf98a69c553941d685283ad15e63` |
| Canonical pages | `b8377df7d38941ff8617c2ec8f69800e1e05dbfcfeb9578f8be39a35f47369a5` |
| Independent queries | `7564b6d65c4da0d45ef77e05cb950f0adb2a8bd6647780ad483e39ff290ecace` |
| Independent key | `4ae8e66db55ce2c30e5b561922bec6db9ff5c6f32d685b7eaab9f3c0f5ea8981` |

The Research lane owns the protocol, policies, original output and scorer. The Planner owns the separate reference key and exact pre-run release. Frozen IS1 measurements remain parked. Public case attribution and natural applicant-file completeness have separate evidence requirements.

## Diagnostic registered before scoring

After sealing the original, the Planner will test whether changing page order could repair a miss, using the independent key solely for diagnosis. Grant the diagnostic the correct opinion. Enumerate the common index's permitted answer windows and ask whether one or two non-overlapping windows could cover all required occurrences within the page budget. Then restrict that enumeration to the pages actually opened by the adaptive reader. Classify each issue in this order: complete under the primary rule, no covering set anywhere in the common window inventory, correct identity unavailable in its trace, covering set only outside the opened pages, or covering set already open but not selected. The first missing condition has priority if several apply. The ceiling is an optimistic bound. It may overestimate what three charged reads could establish when a separate header verification is required. Use it to decide which component deserves a fresh experiment. The primary endpoint and denominator are unchanged.
