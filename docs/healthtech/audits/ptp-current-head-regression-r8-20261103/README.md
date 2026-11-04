# Current-head O1/O3/O4 regression recheck (2026-11-03)

This checkpoint binds a fresh focused regression run to the current candidate. It covers the HTTP/history/export path, generation payload/API fail-closed behavior, local execution guards, current-head frontier helpers, and vector-bundle verification. It does not claim a paid API run, remote encoding allocation, semantic gold, or research superiority.

## Candidate

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Working tree: dirty changes preserved; no reset, clean, stash, merge, or ownership change

## Test result

Corrected command:

```text
rtk proxy python -B -m pytest -ra --junitxml=docs/healthtech/audits/ptp-current-head-regression-r8-20261103/focused-tests.xml tests/test_healthtech.py tests/test_healthtech_http.py tests/test_healthtech_generation_payload.py tests/test_o3_generation_repair.py tests/test_healthtech_api_generation.py tests/test_healthtech_current_head_frontier.py tests/test_healthtech_local_execution.py tests/test_verify_vector_bundle_pair.py
```

- Result: `72 passed`, `0 failed`, `0 errors`, `0 skipped`
- JUnit: `focused-tests.xml`
- JUnit SHA-256: `d654dc08e80117420f15a520bb56a33cbeda20610738761bbd8974e7e6975f6f`

The first invocation in this audit passed an invalid `--junitxml` argument and ran zero tests; it created no provider, ledger, GPU, or dataset state. The corrected invocation above is the authoritative result.

## Boundary

The regression confirms current-head engineering contracts only. O2 remains blocked on an evidenced remote allocation, and paid O3 remains blocked before reservation on canonical R1 history plus current scoped credit. O4 research remains descriptive/partial.
