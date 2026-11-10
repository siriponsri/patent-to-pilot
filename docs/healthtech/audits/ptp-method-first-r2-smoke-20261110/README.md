# SYN-SACR-001: bounded synthetic engineering smoke

DECLARED BEFORE EXECUTION. Actual run completed; profile failed structural validation. The declaration below remains unchanged in scope. One authored input only: “Reduce reverse flow of liquid at low pressure without external electrical power.” It is not a benchmark example. No query/corpus/label/ranking input path exists in the runner. This is an engineering smoke, not R3 pilot or evidence of SACR effectiveness/fidelity.

At most three calls in fixed order: profile, generic, then selective only if profile is structurally usable. No output repair, retry or replacement query. A failed/invalid profile skips selective; generic still tests its independent response contract. Invalid outputs are preserved privately and reported, not treated as success because the process exits normally. No manual edits based on output.

Reuse the pinned local Qwen3-8B weights after full identity recheck. fp16/eager attention, local_files_only/offline, batch one, greedy/nonthinking, max input 8192 tokens, output 4096, byte cap 65536, explicit EOS [151645,151643], pad 151643. Bind the actual effective configuration hash from the CPU observation. No quantization, alternate model, training or re-encoding. Source/prompt/response digests and token counts logged.

Use only approved V100 UUID, cooperative project lock, recheck live processes before launch. Observed capacity before declaration: V100-SXM2-32GB, 32768 MiB total and 0 MiB used; this is not proof of smoke memory sufficiency. Soft deadline 900 seconds, supervisor TERM after 1200 seconds and KILL grace 30 seconds. OOM/timeout is a recorded failed attempt; no automatic smaller-budget rerun. Record peak allocated/reserved memory and time. Hard process termination can leave incomplete reservations; preserve them.

Remote new job: mtm-20261107/r2-sacr-synthetic-smoke-20261110-v1. Deploy fresh pushed git archive, verify identity JSON digest and Bash LF/syntax in the archive, launch setsid/nohup. Monitor pid, logs/status.log, logs/smoke.log and out/status.log. Raw model output stays remote/private; publish only aggregate summary/digests. No user data or protected source mounted/read by this runner. Model-only engineering checks do not resolve the curator/isolation requirement for actual dev work.

Acceptance: observe actual load/generation termination, exact stop/token accounting and response structural validation. Report each call separately. A completed process with invalid profile is a negative engineering result. No semantic-support claim or advancement to protected evaluation follows.

## Actual result (negative profile outcome)
Code c9c37d01f6f3472ad614aead719cb81b07cb7a37, supervisor 2771699 / timeout 2771701 / Python 2771702. Started 01:09:47Z, exit 0 at 01:11:37Z; no runner or GPU compute process remained. Runtime 108.552s including identity rehash, load 3.666s. Peak allocated 16,671,569,920 bytes; reserved 17,794,334,720 bytes. This capacity observation covers only the short authored fixture, not maximum-length inputs.

Profile: 725 input / 845 output tokens, EOS complete, 58.8s, INVALID_RESPONSE_PRESERVED. Diagnostic found seven source-span slice mismatches; six cited snippets occur once in the source and one has no exact occurrence. No offsets/text were repaired. Generic: 297 input / 41 output tokens, EOS complete, 2.781s, structurally valid; no semantic fidelity rating. Selective: skipped because profile unusable. Two model calls, zero retries. Process exit 0 means completion of the engineering attempt, not profile/method success.

Result/diagnostic aggregates are in result.json. Raw generated text remains under remote job out/profile/generation.json and out/generic/generation.json, never staged. Full model identity recheck and effective decoder binding passed.

Next consider a separately versioned profile proposal that asks for exact source quotations and resolves unambiguous offsets deterministically, rejecting absent/ambiguous matches. This is a proposed implementation change, not permission to repair this attempt or rerun it. The current model's relation extraction quality also needs review; correct offsets alone will not establish fidelity. Actual R1 isolation/A03/parity and semantic policy remain open.
