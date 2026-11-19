# Venue shortlist for Papers 1–3 (v2, 19 Nov 2026): KMITL ICT journal list only

Source: the owner's audit `KMITL_ICT_Journal_Audit_2026-11-19.csv` of the faculty list https://erp.it.kmitl.ac.th/journal_conf_list.
- 589 entries; 506 are Scopus Active (Oct 2026), and SJR 2025 is joined where available.
- The CSV is owner-local and not committed; this file keeps only the derived shortlist with KMITL ids.
- Paper 1–3 manuscripts are written for these venues only (owner rule: venues accepted by the faculty, no fee preferred).

**Fee rule.** "Hybrid" journals (Elsevier, IEEE, Springer, ACM non-OA) let authors choose the subscription route, which costs
the author nothing. The APC listed below is the price of the optional open-access route only.
"Diamond" = fully open access with no APC (SJR diamond flag / DOAJ).

**Before choosing, check per venue:**
- the faculty erp detail page (`erp.it.kmitl.ac.th/JC-xxxxx`) for "Use for PG Graduation". The CSV read this field for only
  2 entries; IT Journal KMUTNB = Yes;
- the publisher's current author page for fees;
- ACM's 2026 open-access model for ACM TOIS.

## Shortlist

| KMITL id | Journal | Quartile (SJR 2025) | Fee to author | Fit |
|---|---|---|---|---|
| JC-00465 / JC-01179 | Information Processing & Management (Elsevier) | Q1 (1.845) | none via subscription (OA option USD 3,670) | **P1 primary**; P2 option |
| JC-01081 | ACM Transactions on Information Systems | Q1 (1.932) | check ACM Open 2026 | P1 / P2 (IR methods) |
| JC-00278 | Expert Systems with Applications (Elsevier) | Q1 (1.939) | none via subscription | P2 primary (agentic acquisition, applied) |
| JC-00866 | Knowledge-Based Systems (Elsevier) | Q1 (1.753) | none via subscription | P3 primary; P2 option |
| JC-00246 | Engineering Applications of AI (Elsevier) | Q1 (1.782) | none via subscription | P2 / P3 option |
| JC-00468 | Information Sciences (Elsevier) | Q1 (1.507) | none via subscription | P2 option |
| JC-01321 | IEEE Transactions on Artificial Intelligence | Q1 (1.196) | none via subscription | P3 option |
| JC-00820 | Journal of Information Science (SAGE) | Q1 (0.782) | none via subscription | P1 / IS2-extension (information-science framing) |
| JC-00862 | Knowledge and Information Systems (Springer) | Q1 (0.869) | none via subscription | backup |
| JC-01371 | Transactions on Machine Learning Research | Q2 (0.744) | **diamond, no fee** | P3 (or P2) if the contribution is methodological |
| JC-00235 / JC-01163 | ECTI Transactions on Computer and Information Technology (Thailand) | Q3 (0.213) | **diamond, no fee** | **IS2 / B53 extended version**; P1 backup |
| JC-00849 | Journal of Universal Computer Science | Q3 (0.308) | **diamond, no fee** | backup for any paper |
| JC-01235 | วารสารเทคโนโลยีสารสนเทศ (IT Journal, KMUTNB) | TCI group 1 (2568–2572); not in Scopus | free per OpenAlex OA record; graduation use = Yes (erp read) | Thai-language IS2 short version |
| JC-00859 | KMITL Science and Technology Journal → Current Applied Science and Technology (CAST) | TCI group 1 (successor) | check | backup (scope broader than IR) |

Excluded:
- World Patent Information, JASIST, Scientometrics and Array are not on the faculty list.
- Information Retrieval Journal is Inactive (it became Discover Computing with an APC).
- IEEE Access and PeerJ CS are fully OA with an APC.

## Proposed mapping (owner to confirm)
| Paper | First choice | Free fallback |
|---|---|---|
| P1 BridgeRet | IP&M (Q1) | ECTI-CIT (Q3, diamond) |
| P2 CEDS | Expert Systems with Applications (Q1) | TMLR (Q2, diamond) |
| P3 EG-SHE | Knowledge-Based Systems (Q1) | TMLR (Q2, diamond) |
| IS2 / B53 extension | ECTI-CIT (diamond) | IT Journal KMUTNB (TCI 1, Thai) |
