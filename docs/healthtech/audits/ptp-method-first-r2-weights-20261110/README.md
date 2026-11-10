# Qwen CPU identity observation
PRELAUNCH checkpoint. Inspector hashes all distinct safetensors shards named by the local index plus config/tokenizer/generation files; no weights loaded, no GPU or benchmark input. Two synthetic tests pass (0.22s); Ruff passed before status-log wiring. Actual result pending.

Planned remote job: /home/chaw/patent-to-pilot-jobs/mtm-20261107/r2-qwen-identity-20261110-v1. Code shipped from containing pushed SHA via git archive. Launch setsid/nohup existing venv Python; model root existing research-product-o1-o4-20261031/models/qwen3-8b. Observe logs/status.log and logs/inspection.log, pid file, and identity.json. Exclusive new paths, no retry/overwrite. Recheck live state before launch; no GPU model run.
