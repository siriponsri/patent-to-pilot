# Owner light-approval protocol (proposal, 2026-11-18)

The owner asked for a way to keep control without approving every step. Proposal: three lanes. The agent
classifies each action, writes the class in the receipt, and the owner sees everything in one morning digest.

| Lane | What | Owner involvement |
|---|---|---|
| **A — run, then report** | Free CPU/GPU work on dr-train inside a frozen pre-declaration (DEV/VAL/TRAIN only); code, tests, receipts; commits and pushes of the agent's own files; read-only cloud/billing reads | none; listed in the next digest |
| **B — run once declared, report** | Downloads of public data/model weights inside an approved cap (60 GB text cap, pinned HF weights); paid runs inside an already-approved envelope (e.g. the USD 10 RunPod pilot, or a later FT envelope the owner set once); freezing a manifest/pre-declaration the owner already asked to freeze | none at run time; the declaration is committed before the run, and the digest gives the cost read back from billing |
| **C — ask first (one question)** | Opening any TEST block; any spend outside an approved envelope or above its cap; changing a recorded owner decision, a primary endpoint or a confirmatory family after freeze; deleting or overwriting owner files; cloud resources that keep billing when idle | one AskUserQuestion, batched with every other open C item |

Rules that keep the burden low:
1. **One envelope per stage, not per run.** For the P1 fine-tuning stage the owner sets one GPU envelope (e.g. "P1 FT up to USD 30 of the USD 75 GPU line"); every pod inside it is lane B.
2. **Batch questions.** Lane-C items wait in a list and go out together, at most once a day unless something blocks all work.
3. **Morning digest** (Thai, about 1 page): done / numbers / spend from billing / open C items / next 24 h plan.
4. **Stop rules stay automatic:** the agent stops itself at a cap, at an unexpected TEST access attempt, or at a failed integrity assertion, and reports.

Status: PROPOSED. The owner applied it in spirit on 2026-11-18 (freeze approved "immediately, report in the morning").
