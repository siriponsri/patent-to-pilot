# LOE-Bench memory

- **27 Nov 2026, D40 start.** Decision: LOE-Bench replaces RA Pharma as the active program, and RA Pharma becomes the Thai-context demo layer. Evidence: owner answers in chat and the package hashes in [owner-source](owner-source/SOURCE-SHA256.txt). Limitation: the package smoke run already scored B0–B2 on the Track C test split, so that split is baseline-exposed and never selects a method. Next: Wave 1 handbacks.
- The package docs claim an openFDA `orangebook` endpoint and record that Purple Book downloads failed with plain curl (bot page). E1 and E3 must verify both claims instead of trusting them.
- Executors use Claude Sonnet 5.5 (low or medium) for token economy. GPT-6.2 Sol medium co-plans and reviews. Owner set this split on 27 Nov 2026.
- **27 Nov, Wave 1 closed.**
  - Decision: merge E1–E5 and adopt CP1.
  - Evidence: merge commits on `research/loe-bench`, 34 tests passing, and receipts in [receipts/](receipts/).
  - Limitations:
    - The E1 sha256 values differ from the package manifest while the record counts match. The cause is unknown and the data was not repaired.
    - dr-train was offline.
    - Thai sites (NDI, DIP) were unreachable or returned 403 to scripts.
    - The E2 edition date is the maximum ZIP member modification date. That date bounds the information content, so it is a valid as-of key.
  - Lessons: the package claim that Purple Book is "blocked" was wrong, because the accessdata CSVs download directly. The openFDA `orangebook` endpoint exists.
  - Next: owner confirms the GPT executor models, then FIX1.
- **27 Nov, role change (owner).** Claude is the main planner and the only reviewer. ChatGPT is co-planner and, from Wave 2, executor. In the OpenAI tiers, Astra is the flagship, Sol is the mid tier and Luna is the cheapest. An earlier Orchestrator guess that Astra was a light tier was wrong.
- **27 Nov, T7 attempt 1 failed (GPT-6 Luna high).**
  - What happened: the executor stopped after one record lookup. It wrote no output and made no commit. Its shell hash helper (`rtk` with Get-FileHash) also failed.
  - Decision: retry T7 on GPT-6.2 Sol high with a stepwise card. The card uses local openFDA UNII and substance fields as locators, and Python hashlib for hashes.
  - Lesson: Luna is not reliable for open-ended adjudication cards. Reserve it for fully scripted, mechanical cards.
