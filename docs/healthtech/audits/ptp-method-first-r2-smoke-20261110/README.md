# SYN-SACR-001: bounded synthetic engineering smoke

DECLARED BEFORE EXECUTION; NOT_RUN at this checkpoint. One authored input only: “Reduce reverse flow of liquid at low pressure without external electrical power.” It is not a benchmark example. No query/corpus/label/ranking input path exists in the runner. This is an engineering smoke, not R3 pilot or evidence of SACR effectiveness/fidelity.

At most three calls in fixed order: profile, generic, then selective only if profile is structurally usable. No output repair, retry or replacement query. A failed/invalid profile skips selective; generic still tests its independent response contract. Invalid outputs are preserved privately and reported, not treated as success because the process exits normally. No manual edits based on output.

Reuse the pinned local Qwen3-8B weights after full identity recheck. fp16/eager attention, local_files_only/offline, batch one, greedy/nonthinking, max input 8192 tokens, output 4096, byte cap 65536, explicit EOS [151645,151643], pad 151643. Bind the actual effective configuration hash from the CPU observation. No quantization, alternate model, training or re-encoding. Source/prompt/response digests and token counts logged.

Use only approved V100 UUID, cooperative project lock, recheck live processes before launch. Observed capacity before declaration: V100-SXM2-32GB, 32768 MiB total and 0 MiB used; this is not proof of smoke memory sufficiency. Soft deadline 900 seconds, supervisor TERM after 1200 seconds and KILL grace 30 seconds. OOM/timeout is a recorded failed attempt; no automatic smaller-budget rerun. Record peak allocated/reserved memory and time. Hard process termination can leave incomplete reservations; preserve them.

Remote new job: mtm-20261107/r2-sacr-synthetic-smoke-20261110-v1. Deploy fresh pushed git archive, verify identity JSON digest and Bash LF/syntax in the archive, launch setsid/nohup. Monitor pid, logs/status.log, logs/smoke.log and out/status.log. Raw model output stays remote/private; publish only aggregate summary/digests. No user data or protected source mounted/read by this runner. Model-only engineering checks do not resolve the curator/isolation requirement for actual dev work.

Acceptance: observe actual load/generation termination, exact stop/token accounting and response structural validation. Report each call separately. A completed process with invalid profile is a negative engineering result. No semantic-support claim or advancement to protected evaluation follows.
