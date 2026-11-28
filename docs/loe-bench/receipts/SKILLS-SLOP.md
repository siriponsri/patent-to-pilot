# SKILLS-SLOP · Writing-quality skills for IS2 (owner request, 28 Nov 2026)

The owner asked that both skills be used on the IS2 writing in Thai and English. Both are installed project-locally under D29 (skills, harnesses and tools for the project) in `.agents/skills/`, and copied to `~/.claude/skills/`.

| Skill | Source and commit | Licence | SKILL.md SHA-256 | Purpose |
| --- | --- | --- | --- | --- |
| no-ai-slop | github.com/petergyang/no-ai-slop @ 000650b156983f5159695b441477f4e63b25dc85 | MIT (LICENSE copied) | `1c1abfa4e447e2e96f02832cc3d31d8b298184027aab1bb4cf5aa33179dc2f81` | Editing rules: banned words, binary contrasts, colon reveals, puffery, metadiscourse, summary endings, em dashes. Detect mode and edit mode, with eval.md as the checklist |
| zero-slop | github.com/manavmishra/ZeroSlop @ d53bfa56278d40685eeaa0ac0c3b4b633362caa4 (skill v2.12.43) | MIT (LICENSE copied) | `c5537ca8f6dd3696bd095792e3fdcfc6299ea3716d8c4dddce0c48e244962d01` | Local scorer (`scripts/slopscore.py`, standard library only), fidelity check (`--fidelity a b`), performed-register pass, eight-role editorial pipeline |

**Network.** Only `zero-slop/scripts/version_check.py` uses the network; it is never run. The npm `zero-slop deslop` command and the hosted MCP/REST endpoints send drafts to a remote service and are not used. All scoring stays local, run with `python -I`.

**Disclosure.** Zero-slop refuses to defeat AI-disclosure requirements. The IS2 AI-use acknowledgment (owner decision D6) stays verbatim.

**Smoke test (PASS).** `python -I .agents/skills/zero-slop/scripts/slopscore.py --formal` on the English IS2 prose (abstract to conclusion, 2,467 words, tables and links stripped) scored **11.2/100, clear**. It flagged 2 items: "utilization", and the share of distinct words (32%). The scorer's patterns are English, so Thai gets the manual register pass only (no-ai-slop rules adapted, plus thai-natural-writing).

**Next.** The IS2SLOP drafter card applies both skills to both editions. The planner then audits facts against the immutable originals.
