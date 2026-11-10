# Byte-stable CPU archive packaging

Status: LOCAL_ARCHIVE_VERIFIED; remote execution NOT_RUN.

The CPU-ESCAPE-003 failure remains unchanged. Its Windows Git archive changed LF
blob bytes to CRLF. The new local-only packager applies `core.autocrlf=false` and
`core.eol=lf` to its single Git archive command. It does not modify Git configuration,
normalize bytes after hashing, weaken the remote guard, or launch any process remotely.

`scripts/healthtech/package_sacr_cpu_archive.py` reads the declaration from the archive,
requires it to equal the selected committed blob, and checks all four pinned code files
plus the payload against both declared SHA256 and committed bytes. Missing, duplicate
and nonregular pinned members fail closed. It writes code.tar and a receipt only after
verification, into a new exclusive output directory. A write interruption leaves that
directory reserved; it must not be mistaken for a complete package.

Verification used the immutable original declaration commit
`a9c1d640d0c950fc0c032339fac87a29fd622ab2`. The resulting archive is 1,239,040 bytes,
SHA256 `f419f8032baa2a015a329460a3b8be07a1f81c8878650118fba7160f72550139`.
This is a local packaging check, not permission to execute the old attempt again.

Reproduce six positive/negative cases from the repository root:

```powershell
rtk proxy python docs/healthtech/audits/ptp-method-first-archive-packaging-20261110/check_packaging.py
rtk proxy python -m ruff check scripts/healthtech/package_sacr_cpu_archive.py docs/healthtech/audits/ptp-method-first-archive-packaging-20261110/check_packaging.py
```

Both commands passed. `verification.json` records exact checks: valid archive;
CRLF-converted declaration; changed payload; changed callback code; missing payload;
duplicate payload. These checks neither import tokenizer/model libraries nor establish
grammar performance, effective configuration, fidelity or scientific benefit.

## Next action

Owner approval requested for CPU-ESCAPE-004: one new 120-second CPU-only attempt using
the same 14 authored cases, schema and candidate; only packaging changes, no model calls,
no automatic retry, five-second termination grace. Approval remains PENDING. CPU-003's
declaration explicitly says a failure does not authorize another attempt. Do not create
a new remote job until approval and a separate pushed declaration/prelaunch checkpoint.
For any authorized later dispatch, verify transmitted archive SHA256 before extraction
and keep remote exact-file guards. This package does not attest remote identity or
authorize model generation. R1 curator/isolation and protocol decisions remain pending.
