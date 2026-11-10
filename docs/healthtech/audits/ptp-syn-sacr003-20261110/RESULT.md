# SYN-SACR-003 result: FAILED structural acceptance

The one approved real generation attempt finished normally but failed its declared
profile acceptance. Exit0 is not PASS. Container exited, no OOM and no restart.
CPU004 remains14/14 PASS; it was not a claim of viable model output.

One model call,677 input and917 output tokens, EOS_COMPLETE; generation83.307s,
supervisor wall141.93697s, model load3.696s. GPU peak allocated16,655,618,048bytes,
reserved17,735,614,464bytes. Observed cgroup memory.peak1,654,444,032bytes is a sampled
lower bound on final peak; hard container cap32GiB was enforced. Actual GPU busy
seconds were not separately measured; conservatively charge the full141.93697s
container-supervisor interval against the72h continuation budget.

Private stored response replay (zero new calls) confirms valid full JSON schema,
correct query/source identity and18 exact unambiguous source quotations. The subsequent
canonical profile validator rejects `blocks not in source order` at sacr_profile.py:78.
No block sorting, output repair or replacement generation was performed. This narrows
the failure from JSON syntax to a cross-field structural condition that the grammar
does not enforce. It does not establish complete source coverage or semantic fidelity.
Raw generated text remains private; diagnosis.json contains only counts/categories.

Exact code146d6117268c5a6a8e879392f3dd951c10a53229, pinned model hashes matched, actual
Qwen3ForCausalLM loaded fp16/eager on cuda:0. Decoder hash remained pinned. Python
container3.12.15 versus historical host3.12.3 is disclosed. The decoder warned that
sampling flags temperature/top_p/top_k do not apply with deterministic decoding;
do_sample=False was explicit. No fallback configuration was selected.

observed-result.json preserves terminal/container configuration, sanitized summary,
runtime identity and raw artifact hashes. Full source/generated artifacts stay under
/home/chaw/patent-to-pilot-jobs/syn-sacr003-20261110-v1/out/attempt, never committed.
The preflight-only Windows newline mismatch and original declaration are preserved;
that guard ran before any remote attempt and did not consume a model call.

Next: no automatic retry. Diagnose the structural failure statically and preserve
the output. A new generation attempt needs a separately justified declaration and
applicable owner approval; the approved one smoke is consumed. MTM/DAPFAM curator,
isolation and baseline work remain independently authorized. Do not advance SACR
to pilot merely because an anchor fallback could produce rankings.
