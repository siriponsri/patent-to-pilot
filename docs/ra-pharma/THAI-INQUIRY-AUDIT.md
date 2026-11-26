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

## Original and independent result

The Planner held v1 because the scorer conflated the number of required qualifiers with the number of output spans, and the adaptive ranker inspected raw text in unopened windows. V2 validated packed qualifiers and moved the static evidence cues into the shared charged index. Release was bound to Research commit `6fa6fb4d1b254b7a2c96ea7d21cce79a90fa33d0`, freeze `46cf4105be76671749530885fe6774044b6c9235affdd40f84211b4ae9b209f3` and a new, exclusive output path. The [frozen protocol and implementation](https://github.com/siriponsri/patent-to-pilot/tree/6fa6fb4d1b254b7a2c96ea7d21cce79a90fa33d0/docs/ra-pharma/research/official-correspondence) are public project records. The original was sealed before scoring at SHA-256 `af251a6d9862ae7c1e987fba6f9b40caf2539561738c8929afc3ef4ef27e2191`. The separate outcomes file is `858d25e5326fc255d95ac79d233e8b2647f46466007b9e1ecc0323bf41f96765`.

| Original measure | Adaptive pages | Exact reference with conflict check | Lexical |
|---|---:|---:|---:|
| Linked to correct source, requester and letter | 10/11 | 10/11 | 10/11 |
| Complete answer including every required qualifier | 3/11 | 3/11 | 2/11 |
| Issued with incomplete evidence | 5 | 5 | 6 |
| Abstained | 3 | 3 | 3 |
| Logical page opens after shared indexing | 22 | 22 | 26 |
| Indexed windows ranked | 230 | 228 | 187 |

The Planner independently reconstructed reference matches, permitted opens and all answer offsets directly from the sealed original and the separate key. The primary difference is zero. Each issue had the same correctness under adaptive and exact reference, with identical page actions and returned extracts on ten of eleven. All 22 source pages and 1,338,319 PDF bytes were processed by common indexing. No runtime page rendering, model, paid service or GPU was used. The 2,803-pass suite retained eight known SACR failures, ten skips and one expected failure. Two earlier unmodified runs also had a wait-free asynchronous HTTP test failure. A test-only change replaced its 100 busy polls with a bounded wait and preserved its assertions. An incomplete scheduling diagnostic was retained. The final suite log SHA-256 is `4ae9a8b6a8b739fda2abc48848cb4a0d08358aa55e28edea83fafebf0ce43d33`.

The registered diagnostic found three complete issues, two for which no pair of indexed windows could cover the key, one with unavailable identity, one requiring a different open page and four with a covering pair already on open pages. This assigns all eleven issues once. A bounded public search for each incoming reference found the official opinions or unrelated files. It did not verify an independently archived original incoming letter.

The Planner dispatched one follow-up on a prospectively enrolled second index page. Use the closed first page only for development, keep the same primary endpoint, compare an issue-conditioned pair of extracts against a matched diversity-aware selector, and lock both before the new answers are evaluated. Repeat opinions and reconsiderations from training are ineligible. The third index page is outside the follow-up.
