# SYN-SACR-002 quote-profile-v1 engineering regression
DECLARED_NOT_RUN at prelaunch checkpoint. This is a new versioned attempt after the failure of SYN-SACR-001, not a retry/replacement of that attempt. Original output, v0 prompt and runner are unchanged.

Use the identical authored liquid-flow fixture as a regression case already seen during development; it is not an independent validation sample. New profile_quotes prompt/schema and unique exact quote alignment are fixed before output. It also explicitly discourages filling all eight blocks; attribute no change solely to offsets.

At most two model calls: quote-profile then selective only if profile structurally usable. No generic rerun, no retry, no manual/fuzzy repair. Any ambiguity/absent quote or schema failure rejects profile and skips selective. Preserve raw proposal and canonical/alignment outputs separately and privately. Structural validity does not establish semantic fidelity.

All other settings fixed from SYN-SACR-001: same fully rehashed Qwen identity and effective decoder hash, fp16/eager, batch1, greedy/nonthinking, input8192/output4096/bytes65536, EOS/pad pins, 900s soft /1200s hard deadline plus30s kill grace. One approved V100 under project lock, fresh resource check and pushed archive, verified LF/Bash and identity digest. No benchmark/label/index/query file input; no training or re-encoding.

Remote new job: mtm-20261107/r2-sacr-quote-smoke-20261110-v1. Monitor pid, logs/status.log, logs/smoke.log, out/status.log. Publish aggregates/hashes only, no generated text. Report failure or exact observed validity without promoting to R3/R1 completion. No further generation tuning is implicit in this declaration.
