# Actual Qwen weight and decoder observation
CPU inspector deployed via git archive of acf03860fb5ee30dc5f2dc1c1c4cb484f63a2e91 (pushed and remotely verified). Remote job mtm-20261107/r2-qwen-identity-20261110-v1, launcher PID 2735622, actual inspector PID 2735623. It ran 01:04:05Z–01:04:43Z, exit 0, then process absent. Prelaunch nvidia-smi reported no compute processes. No GPU model job launched.

identity.json binds five local weight shards (16,381,516,776 bytes), index and config/tokenizer files. Hashing took 37.69 seconds. Every previously observed small-file hash matches. This is a current local identity record, not external proof of model source/authenticity or evidence of historical run weights. No weights loaded.

decoder-observation.json records actual installed-library GenerationConfig resolution and a CPU-only tokenizer synthetic-template check. do_sample=false, one beam, explicit 4096 output cap, EOS [151645,151643], padding 151643. The inherited file has temperature .6, top_k 20, top_p .95; transformers warned these sampling-only flags may be ignored with greedy decoding. Repetition penalty is 1, no repeat-ngram ban, minimum length 0. Full resolved configuration hash recorded. This did not invoke model.generate.

The nonthinking chat-template suffix was present on the authored synthetic fixture (34 input tokens). Tokenizer loaded on CPU; no benchmark input or protected label access. Full SACR prompt capacity, fp16/eager model loading, GPU memory/time and actual output validity still NOT_RUN. Existing semantic and curator/isolation gates remain.

Two synthetic inspector tests pass (0.22s); Ruff passed after status-log wiring. Actual CLI success provides integration evidence for status/output handling. Launch/status/output paths are durable; no job remains and no automatic retry occurred.
