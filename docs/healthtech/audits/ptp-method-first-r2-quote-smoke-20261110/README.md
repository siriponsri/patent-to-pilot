# SYN-SACR-002 quote-profile-v1 engineering regression
Declared before execution; actual attempt completed with invalid JSON. This is a new versioned attempt after the failure of SYN-SACR-001, not a retry/replacement of that attempt. Original output, v0 prompt and runner are unchanged.

Use the identical authored liquid-flow fixture as a regression case already seen during development; it is not an independent validation sample. New profile_quotes prompt/schema and unique exact quote alignment are fixed before output. It also explicitly discourages filling all eight blocks; attribute no change solely to offsets.

At most two model calls: quote-profile then selective only if profile structurally usable. No generic rerun, no retry, no manual/fuzzy repair. Any ambiguity/absent quote or schema failure rejects profile and skips selective. Preserve raw proposal and canonical/alignment outputs separately and privately. Structural validity does not establish semantic fidelity.

All other settings fixed from SYN-SACR-001: same fully rehashed Qwen identity and effective decoder hash, fp16/eager, batch1, greedy/nonthinking, input8192/output4096/bytes65536, EOS/pad pins, 900s soft /1200s hard deadline plus30s kill grace. One approved V100 under project lock, fresh resource check and pushed archive, verified LF/Bash and identity digest. No benchmark/label/index/query file input; no training or re-encoding.

Remote new job: mtm-20261107/r2-sacr-quote-smoke-20261110-v1. Monitor pid, logs/status.log, logs/smoke.log, out/status.log. Publish aggregates/hashes only, no generated text. Report failure or exact observed validity without promoting to R3/R1 completion. No further generation tuning is implicit in this declaration.

## Actual outcome
Code47958726a80c715eda52f76031d368b9e1fdb05c; supervisor2829467/timeout2829469/Python2829470. Started01:18:52Z, exit0 at01:20:05Z; no runner/GPU compute process remained. One profile_quotes call:681 input/344 output tokens, EOS_COMPLETE,24.533s. Full runtime71.66s, load3.746s, peak allocated16,646,121,984/reserved17,733,517,312 bytes.

Response invalid JSON: Expecting comma delimiter at character898 (line1,column899),1124 characters; not a Markdown-fenced response. No stripping, patching, parse salvage or generation retry. Quote alignment was never reached, so this attempt does not test whether v1 source alignment succeeds. Selective skipped. Process completion is not an extraction success. Aggregate result/diagnostic in result.json; raw output remains remote out/profile_quotes/generation.json.

Combined engineering ledger: SYN-SACR-001 failed exact source spans, SYN-SACR-002 failed JSON syntax. Do not keep iterating prompts until a selected passing example appears. Next assess schema-constrained output feasibility and state a bounded validation plan before any further model call; preserve both failures and report total attempts. Actual benchmark/R1 and semantic gates remain open.
