# Option A baseline development receipt

**PASS for local packet and scoring rehearsal. NOT_RUN for inference and operator timing.** The [development protocol](PROTOCOL.md) pins three already exposed PDFs and the [Thai operator prompts](OPERATOR-PACKET.md). The baseline check read retained evidence without running a D31 capture or opening the independent key. There is one observed matter family. It supplies a failure example and no estimate of model effectiveness.

## Local source and citation check

CPython 3.12 and PyMuPDF 2.0 verified all three PDF hashes and page counts (465,711 bytes, seven pages), the canonical extraction hash, and the seal digest of the retained first-pilot output. Sorted embedded-text extraction for all seven pages matched the canonical strings exactly. Both arms' identity and two literal spans mapped to the pinned source and opened pages. The local import check covers PDF/text integrity and page mapping. The product import checks remain pending.

| Retained output, same exposed issue | Action difference | Semantic reading of returned evidence |
|---|---|---|
| Lexical | Opened pp. 1, 2, 3. Returned p. 2 [2058,2418) and [1578,1938). | Correct opinion and letter. The extracts address the existing registration limits. The route under sections 80 and 82 and the subsequent requirement are absent. Incomplete. |
| Exact composite | Bound p. 1 from the shared index and opened pp. 2, 3, 4. Returned p. 2 [2058,2418) and p. 4 [360,720). | Correct opinion and letter. The p. 4 extract supports the regulatory route and the application, label and leaflet scope. It cuts off before the operative sequence explaining what the Ministry can require once that step is complete. Incomplete on the exposed semantic rubric. |

The historical receipt scored exact complete and lexical incomplete using its frozen occurrence rule. That result stands. The new reading asks whether the returned excerpts themselves convey the two-step sequence. On p. 4, follow the text beyond offset 720 through the remainder of the Council's conclusion before the signature. The continuation makes explicit that the regulation comes first and that the resulting label and leaflet requirements follow. The exact extract does more useful work but omits that continuation. This single-executor reading has not received independent Thai adjudication. [Historical results](../official-correspondence/RECEIPT.md) · [Edition and source locator](PROTOCOL.md#frozen-development-inventory)

## Scoring rehearsal

The fixtures are authored for rehearsal. Use a fictional source X. Its p. 1 gives the actual issuer and inquiry ID. Its p. 2 authorizes after-hours use of a meeting room if a steward is present and one day's notice is given. Its p. 3 restates both requirements in a signed summary. For the unknown fixture, use a different enquiry whose answer cannot be verified from the retained record. The fixture assertions below are normalized for adjudication. Reviewers would receive neutral source locators and opaque answer IDs, with system identity and timing held by a separate coordinator.

| ID | Submitted content in brief | Scoring result |
|---|---|---|
| cal-41 | Correct attribution and disposition with two paraphrased conditions and p. 2 support | Complete, both conditions supported |
| cal-92 | Same meaning grounded in the independently checkable p. 3 summary | Complete, alternative locator accepted |
| cal-56 | Same substantive conditions attributed to the requester as issuer | Incomplete, wrong attribution and unsupported issuance |
| cal-18 | Correct attribution and disposition, gives steward condition and explicitly leaves the notice condition unresolved | Partial, missing qualification, no unsupported issuance |
| cal-63 | Explicitly abstains on a fully documented issue | Incomplete, abstention |
| cal-77 | Issues an answer to the separately unjudged enquiry | Unjudged issuance, excluded from correctness |
| cal-35 | Correct issuer, claims same-day notice suffices and cites p. 2 | Incomplete, contradiction and unsupported issuance |

An offline Python assertion check over these manually coded judgments matched all seven expected outcomes. It gave 2/6 complete and 2/6 unsupported on known rows, 6/7 operational coverage (5/6 known), one explicit abstention and one unknown issued. This rehearsed the aggregate mechanics and handoff fields. Independent blind rating and agreement remain NOT_RUN. Use the following columns for a live read: opaque response ID, known/unknown, independently checked disposition, attribution, per-condition decision with witness, delivery, harm flag and rationale. Restore arm mappings after adjudication.

## Development ledger

| Step | Outcome and action change | Blocker and next checkpoint |
|---|---|---|
| Checkout and scope | PASS. Clean lane at `e5e8d61f`; one research checkout and no pre-existing A lane files. Planner had a separate main checkout. Sent the path and scope to Planner before the local checks. | Planner owns consent and independent review. |
| Local runtime preflight | NOT_RUN for direct full-context zero/few-shot and hybrid RAG. The bounded check found no Ollama, llama.cpp or LM Studio commands or processes, no weights in their checked default model stores, only dataset directories in the inspected HF cache, and no torch, transformers or llama_cpp in the current Python 3.12 interpreter. No readily usable pinned model was identified. | Admit a versioned local runtime and legally usable weights with confirmed context fit under the envelope. Run full-context checklist first. |
| Packet and retained baseline | PASS. Read existing spans only, replacing the lexical reader's header open with the exact reader's page 4 in the *comparison of recorded actions*. No live reader was run. Initial shell wrapper failed argument parsing, followed by a successful read-only Python stdin check. | Send the p. 4 omission and rubric to independent review. |
| Semantic accounting | PASS for authored adjudication fixtures and arithmetic. The rule admits equivalents and separates unknown and abstention. | Confirm rubric and rater agreement on held-out-from-training examples after a separate release. |
| Products and time | ChatGPT Pro, NotebookLM, actual transfer, product citation import and timed pilot NOT_RUN. | Planner verifies actual access and visible mode and establishes clearance and retention terms. Test page fidelity before starting the timer. |

No new OCS pagination, paid calls, GPU/pod, upload or Product changes. Numerical limits and any fresh capture remain subject to their prospective lock.
