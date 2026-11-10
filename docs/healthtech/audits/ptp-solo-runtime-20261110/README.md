# Solo runtime compatibility observation

Owner approved temporary existing-Docker runtime/evaluator separation. One CPU-only,
no-data container imported the existing read-only site-packages successfully: Python
3.12.15, Torch2.8.0+cu128, Transformers4.55.2, LMFE0.11.3. No image pull/install/model
load or GPU computation. Python patch version differs from host3.12.3.

container-probe.json preserves actual Docker configuration/state: user1000:1000,
network none, readonly root, cap-drop ALL, no-new-privileges, not privileged,8CPU,
32GiB memory and equal total memory+swap,256PIDs, only dependency-directory bind
read-only. Container exited0 and is retained stopped. No protected/test/source-job
mount, Docker socket, account/ACL/daemon setting change. This is evidence for this
one CPU container, not attestation of a future GPU/data runtime or agent blindness.
Image/venv identity is in metadata.json. CUDA was intentionally unavailable in this
CPU probe. Actual GPU exposure/model compatibility remains the declared smoke gate.
