# Start the two executor sessions

> Historical RA Pharma record. D40 superseded this mandate on 27 November 2026. RA Pharma supplies the Thai-context demo layer for [Market Window Dossier](../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026), whose benchmark is LOE-Bench.

Open two independent checkouts from the published origin branches. Select the named model and reasoning level in the client. Paste the corresponding prompt. Each session records its own actual base and checks for later commits when it starts.

Current research startup is in the [research-first plan](RESEARCH-FIRST.md#read-only-starting-prompt). The prompts below document the earlier parallel dispatch.

## Original Research · GPT 6.2 high

> Work as Research Executor for Patent-to-Pilot on the existing research/ra-pharma branch in its own checkout, with GPT 6.2 high. Verify the checkout, base and requested runtime. Read CLAUDE.md, AGENTS.md, HANDOFF.md, INDEX-PLAN.md, docs/ra-pharma/MASTER-PLAN.md, EVIDENCE-CONTRACT.md in that directory, and research/BRIEF.md, HANDOFF.md and MEMORY.md within it. Own R1–R5 and the research paths on the board. Begin with IS1 input eligibility and a prospective depth-by-instruction and adaptive-reading protocol. Use unexposed authorized DEV only, matched controls, independent pre-run review and sealed receipts. Report a documented NOT_RUN when an input or release gate is missing. Keep the product display families out of method selection. At every task close use the repository writing skill, update affected English docs, your lane handoff and memory, commit explicit paths and push your branch. Report results, limitations, costs, verified SHA and the next decision in Thai to the Planner. Leave main and the product branch to their owners.

## Product · Claude Sonnet 5.5 medium

> Work as Product Executor for Patent-to-Pilot on the existing product/ra-pharma branch in its own checkout, with Claude Sonnet 5.5 medium. Verify the checkout, base and requested runtime. Read CLAUDE.md, AGENTS.md, HANDOFF.md, INDEX-PLAN.md, docs/ra-pharma/MASTER-PLAN.md, EVIDENCE-CONTRACT.md in that directory, and product/BRIEF.md, HANDOFF.md and MEMORY.md within it. Own P1–P5 and the product paths on the board. Build one local Thai-first RA Pharma dossier from the S4 reader with a patent/FTO chart, a jurisdiction-aware registration checklist and a sender-appropriate editable response letter. Demonstrate missing versus supplied applicant evidence, a versioned skill correction, citation replay and rendered correspondence. Use rights-cleared sources and fictional applicant data. Verify the normal Windows entrypoint and full code gate. At every task close use the repository writing skill, update affected English docs, your lane handoff and memory, commit explicit paths and push your branch. Report the demo path, checks, unresolved issues and verified SHA in Thai to the Planner. Leave main and the research branch to their owners.
