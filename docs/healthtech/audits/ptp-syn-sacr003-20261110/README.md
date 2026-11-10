# SYN-SACR-003 guarded profile smoke

DECLARED_NOT_RUN at publication. CPU004 passed14/14; owner approved one new
generation smoke<=30min. Exactly one quote-profile generation, authored source
identical to CPU004, query_id q1, existing profile-quotes prompt. Uses the accepted
CPU candidate callback/config plus independent complete-JSON EOS guard. No selective
or generic call in this diagnostic; downstream view-generation viability remains open.
Maximum8192input/4096output tokens, context40960, response65536bytes, no retries.

Use existing pinned Qwen3-8B, fp16/eager, greedy/nonthinking, explicit EOS. Rehash
model files before loading and preserve loaded class/device/dtype, effective decoder,
prompt, source and grammar receipts. No benchmark input or protected data. Raw outputs
stay private. Passing requires EOS, exact quote alignment and usable structural profile;
it does not establish fidelity or full SACR. All failures preserved.

Temporary Docker container uses pinned existing Python3.12 image and read-only existing
site-packages/model/code, no network, nonroot1000:1000, read-only root, no privileges,
cap-drop ALL, no-new-privileges,8CPU,32GiB RAM/no additional swap,256PIDs, only V100.
Only dedicated private output and the single cooperative lock file are writable.
The child sees the existing host lock file at its model-parent path and acquires the
standard nonblocking lock before model loading. Do not mount the whole model-parent
or source-job root. The supervisor does not hold that lock while the child acquires
it; use the existing child lock, with fresh host conflict check before dispatch.

Wall1800s; soft alarm1740s; supervisor TERM then5s KILL, retain container terminal/OOM
and memory evidence. Python container3.12.15 differs from historical host3.12.3 and
must be disclosed. CPU compatibility import passed; GPU capability/model load is
part of this one bounded attempt, not assumed. No automatic alternative image/runtime.
