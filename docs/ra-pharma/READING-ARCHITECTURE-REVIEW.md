# When does another read change the dossier?

Planner review opened 26 November 2026. The engineering question is whether a specialist can tell the next reader exactly which fact is still missing, which source may supply it, and which other dossier rows depend on it. The scientific question is whether that information changes reading decisions and improves independently checked outputs under the same budget. This is a design review. The [IS1 successor](RESEARCH-AUDIT-20261126.md) retains its own ranking endpoint.

## One dossier, three readers

Consider an applicant preparing a Thai registration dossier for a tablet. A dependent patent claim adds a coating limitation. The patent reader opens the referenced claim and keeps the added limitation attached to that branch. The regulatory reader receives a description of the claimed coating and a request for the applicant's own coating evidence. A patent example alone leaves the applicant row unresolved. The correspondence reader can draft a request for the missing attachment and link it to that row. The sender, document class, signature authority and template govern letter layout and emblem use. A reviewer can follow each draft sentence back to the evidence or missing item.

Each row carries the subject, evidence role, jurisdiction, edition, exact locator and the alternatives under which it holds. Reads can satisfy several rows when those fields agree. An alternative parent in a multiple-dependent claim stays separate from its siblings. A negative assertion needs evidence appropriate to that assertion. An unresolved row can become a precise request. A letter can refer to a pending item without upgrading its status. An FTO chart also needs territorial rights, legal status and product mapping before a professional opinion.

The learning unit is a decision about the next admissible read, such as opening a parent claim, another patent family, the applicable edition of a Thai requirement or the applicant's attachment. On training data only, a correction can change the priority or estimated cost of these actions. Evidence admission and professional sign-off stay fixed. The learned and fixed readers receive identical visible inputs, cache access and final verification. Log the candidate actions, chosen read, affected rows and remaining budget. This permits a reviewer to identify a real change in behavior.

## An analytical boundary worth testing first

For a request to return **all** mandatory claim passages, let U be the union of distinct passages in the required branches. Suppose each passage must be opened once to supply its versioned locator and each open costs one unit. A correct cold-cache reader must make at least |U| opens. Traversing each required branch with a shared cache makes exactly |U| opens when the dependency map is complete and locating the passages is free. Reordering these opens cannot improve that count. With incomplete dependencies, separately meter discovery, parsing and candidate inspection. This argument concerns passage opens under the stated assumptions, not total runtime.

There is an empirical question where there are genuine choices. For example, a request might accept either of two independently sufficient applicant attachments, and one of those attachments might also complete another row for the **same** product and edition. Alternatively, a reviewer with a fixed budget might ask for as many fully supported chart rows as possible, with all remaining rows explicitly open. For a list of every applicable claim branch, a reader must account for every alternative. It cannot turn that assignment into an easier existential question.

## Experimental decisions

| Stage | Minimum evidence and comparator | Decision |
|---|---|---|
| IS1 successor eligibility | Pin permitted text and date, family identity, independently recorded OUT citations, exclusions, and the eight instruction/depth cells. Use a matched reference on the same corpus. | A public endpoint with enough records warrants acquisition work. Unknown family overlap or incomplete labels block a claim about unseen families. Title and abstract alone support a separately named study. |
| Open development microscope | Use an explicitly accessible development source, a prospective budget, an external source locator and a full-read reference. Compare ordinary rank order, a cached parent walk, and, when alternatives exist, greedy valid row coverage per read. Give controls the same index features and charge their construction. | Report whether there is a choice and whether the policies take different actions. Accept a cached-parent tie as a conformance outcome. One example establishes software behavior only. |
| Natural evaluation release | Establish family separation and an independent key for the requested output. Pin one primary comparator, endpoint, minimum useful difference, resource accounting, harms and original output path before execution. Include all admitted families. | Release only at exact reviewed revision and freeze. An inconclusive or negative result closes that comparison. A new hypothesis needs independent data and another prospective decision. |

For the architecture comparison, the proposed primary output is the number of independently verified complete rows per dossier under a fixed read budget. Report paired family uncertainty, unanswered rows and wrong-scope outgoing assertions. The claim is eligible only where the evaluator can judge row completeness independently. For the retrieval study, retain the registered Generic depth contrast on strict OUT nDCG@100. Citation links are independent indicators of known family retrieval. They do not adjudicate a claim limitation or an applicant document. Keep the endpoint, denominators and disposition of each study separate.

## Where the literature already reaches

| Primary work | Consequence for this design |
|---|---|
| [CLEF-IP claims-to-passages](https://ceur-ws.org/Vol-1179/CLEF2013wn-CLEFIP-PiroiEt2013.pdf) and [Sparse Coverage](https://arxiv.org/abs/2608.16918) | Retrieving passages from claims and covering multiple technical components both have direct precedents. Include structural retrieval in the comparison. |
| [Golestan Far et al., SIGIR](https://ssanner.github.io/papers/anu/sigir15_patents.pdf) | Oracle relevance feedback can produce gains that autonomous term selection fails to reproduce. Exclude evaluator-only terms and citations from actions. |
| [Javdani et al., AISTATS](https://proceedings.mlr.press/v33/javdani14.html) | Choosing information to reach a valid decision under cost is established. The proposed contribution depends on handling actual scope, shared evidence and downstream harms better than a cost-aware policy. |
| [Leo et al., Findings of AACL](https://aclanthology.org/2026.findings-aacl.16/) and [PatentEdits](https://arxiv.org/abs/2411.13477) | Claim revision and localization already have natural comparisons. Leo et al. found small and direction-inconsistent retrieval effects. Their [corpus description](https://raw.githubusercontent.com/TeamLab/probing-rag-patent-amendment/main/docs/corpus.md) includes a published evaluation cohort and replication reserve. Verify a separately addressable development partition before accessing examples. |

Discovery used SciSpace searches on claim-aware retrieval, prosecution amendments and cost-sensitive decision-region determination, followed by review of the primary sources above. This supports comparator selection. A first-in-field claim remains unestablished.
