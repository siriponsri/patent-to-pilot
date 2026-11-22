# Owner decisions, 22 Nov 2026 (answered in chat)

| # | Question | Owner's decision | What it means for the work |
|---|---|---|---|
| D1 | What should the IS2 core story emphasise? (the owner had already chosen the current research as the core) | **Research + demo** | Story arc: Paper 53 → B53 (bridge) → G03 DEV experiments, honestly including the parked results → B53.0 (our pipeline matches the DAPFAM paper) → Workbench demo of selective update after a source change. Thai and English papers and slides are rebuilt on this arc. |
| D2 | If G03 amendment 2 (learned selector) also does not beat F\* | **Keep working on acquisition** | Do not pivot the headline to maintenance yet. Design and pre-declare new acquisition mechanisms that bring in *new* candidates, e.g. LLM query rewriting or obligation decomposition through OpenRouter (D7), or additional candidate sources. Each is frozen before its numbers, on allowed DEV only. |
| D3 | Download the PatenTEB train split for the PatEmbed–DAPFAM overlap audit | **Approved** | Accept the Hugging Face terms through the owner's normal account flow if a login is needed, and record the revision. Run a family-level overlap audit (DAPFAM 1,247 queries + 45,336 families vs PatenTEB train). Store only aggregates in Git. |
| D4 | Delete the read-only `b53/inputs` on dr-train | **Approved, and done 22 Nov** | See `artifacts/maintenance/20261122-b53-pull/SUMMARY.md`. |
| D5 | English byline for the advisor | **"Tuchsanai Ploysuwan"** in the author line; the title "Assistant Professor" goes only in footnote 2 | Thai edition: ผศ.ดร. ทัศนัย พลอยสุวรรณ, with "ผู้ช่วยศาสตราจารย์" in footnote 2. |
| D6 | Acknowledgments | **AI-use statement only** | Keep only the sentence declaring AI assistance (Claude) and the author's responsibility; no other thanks. |
| D7 | Paid model API | **Use the OpenRouter API, with several models chosen for relevance to the research (not just one)** | Use G02's `openai_compatible` adapter (endpoint `https://openrouter.ai/api/v1`, `allow_remote` true, key by environment-variable name, e.g. `OPENROUTER_API_KEY`). Pick 3–5 candidate models by research fit and check their live availability and price first (examples to verify: Qwen3 family, Claude Haiku/Sonnet 5.5, DeepSeek V4 Flash, which the Thai Gazette paper used for contextualisation). **The owner has not yet set a USD amount:** CLAUDE.md rule 2 needs a recorded cap (`spend_cap_usd`, `max_requests`) before the first paid request, so ask the owner for the number. Note: the `openrouter` MCP server in Claude Code needs `/mcp` authorisation by the owner. |
| D8 | Optional installs | **`pypdf` approved.** No local Ollama: GPU and local-model work goes to **dr-train (V100) and RunPod via MCP** | Install `pypdf` into `.venv` and enable the G02 PDF ingestion adapter, with tests. RunPod use still needs a per-job envelope (amount + scope) under CLAUDE.md rule 2; confirm the amount before creating any pod, and delete pods after use. |

**D7 follow-up (22 Nov):** the owner reconnected the OpenRouter MCP. Budget proposal:
[API-BUDGET-PROPOSAL-20261122.md](API-BUDGET-PROPOSAL-20261122.md).
- Envelope E1 = USD 8.00 / 35,000 requests, for G03 amendment 3 (LLM query expansion as new acquisition routes) and
  Workbench checks.
- Remaining account balance ≈ USD 8.37.
- **D9 (22 Nov 2026, owner in chat: "Approve E1 USD 8"): E1 APPROVED.**
  - Cap USD 8.00; max 35,000 requests.
  - Scope: G03 amendment 3 (LLM query expansion as new acquisition routes; pilot, then one full run) and Workbench
    profile checks (≤ USD 0.20).
  - Stop rules as in the proposal: no full run if the pilot shows no P1-DEV gain; stop and report at USD 6 spent.
  - The approval covers OpenRouter only. It does not cover E2 or RunPod.

**D10 (22 Nov 2026, owner in chat: "ใส่ใน IS2"): Paper 86 enters the IS2 story arc.** This amends D1. The arc becomes
Paper 53 → B53 (bridge) → **Paper 86 exposure ceiling** → G03 DEV (re-weighting the same routes does not help; v1/A1/A2
parked) → A3 (new candidates via LLM expansion) → B53.0 → Workbench demo.
- The owner asked whether to return to the Paper 86 line. The agent's assessment:
  - Paper 86's headline (+0.111) rests on PatEmbed, which is possibly contaminated on DAPFAM;
  - it is a diagnosis paper;
  - its historical records are incomplete.
  So it serves best as motivation for the acquisition work.
- Paper 86 stays **IS2-only** (rule 9) and is presented as the owner's own **unpublished** work (withdrawn from IEEE,
  19 Nov). arXiv:2605.24297, its ref [2], is not cited (rule 10).
- Revised outline: [docs/writing/is2/IS2-OUTLINE-v3-20261122.md](../writing/is2/IS2-OUTLINE-v3-20261122.md).

Still open:
- the Paper 53 DOI (`DOI pending` stays in the reference list);
- E2 (later);
- RunPod caps (D8).
