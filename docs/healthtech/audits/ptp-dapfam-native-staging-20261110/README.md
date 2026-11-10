# Native DAPFAM curator preparation

Status: IMPLEMENTED_FIXTURE_VERIFIED; REAL_STAGING_NOT_RUN. Sole writer Codex Pepo: Patent to pilot, 10 November 2026. Scope HT-ST1-W1, existing owner authorization applies.

## Contract

Owner-only entrypoint scripts/healthtech/stage_dapfam_native_dev.py reads the three pinned parquet sources and preserved split into immutable byte buffers, checks exact hashes before parsing, and delegates to evaluation/dapfam_staging.py. No new split, protected export, model call, corpus encoding or retrieval. Destination must not exist; no overwrite/retry. Original failed MTM staging remains untouched.

- Native query is title plus abstract with native newline joining; claims are never read for queries. Full TAC corpus is retained without IN/OUT candidate filtering.
- Original474dev/773protected assignment required; full query membership checked. Native IN/OUT eligibility is computed only for dev and written only to evaluator manifest.
- Historical canonical corpus bytes must match42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d. This is only one vector-input gate, not vector-order/model/baseline parity proof.
- runtime-dev has corpus, native TA queries and source/hash manifest; dev-evaluation has dev-only relations and eligibility manifest. No protected output, IDs or per-test statistics. Completion receipt written last. Actual separate read-only mounts/no-network evaluator/runtime remain required; source SHA provenance is not physical isolation.

## Evidence

`python -m pytest tests/test_dapfam_staging.py tests/test_dapfam_native.py -q`:15/15 PASS. Fixtures cover TA/no claims, exclusion of protected identifiers/text/relations, no labels/eligibility in runtime, full candidate corpus, preserved split, missing/empty/duplicate/drift refusal and exclusive destination. Existing native evaluator tests cover native semantics. These are software checks, not real-data parity or semantic fidelity.

Source paths exist under existing repository methodology/datasets/research-only-nc: corpus1149928014bytes, queries62667355bytes, qrels828375bytes. File existence/size only inspected; no source content read. Original split located in sibling _private_artifacts/healthtech/ptp-org-adaptive-20261105/split.json,141779bytes; opaque byte SHA256dd76c019ee74c8d256e182ecfb329f9235638c1ecf9d2c7b1fa8073c4958e6dc matches historical pin. No parsing or ID display. Local pyarrow/numpy available. First PowerShell hash/dependency probe failed (Get-FileHash unavailable and quoting); portable Python hash/import-spec probe succeeded without data parsing.

Read-only disk observation of all remote job directories named20261110: SYN0032892KiB, ownerMTM4496KiB, CPU0042860KiB, CPU0031536KiB. This is a scoped observation, NOT complete cumulative disk admission: local new artifacts/output allowance and other storage must also be accounted before real staging. No GPU job started.

## Next

Prepare resource-enforced owner launcher and complete disk admission; supply exact owner command after publication. Owner must execute mixed-source stage personally. Then inspect only completion/runtime/dev-evaluator allowlists, validate separate mounts, bind existing vectors and establish native TA baseline. Do not run the curator from this agent session. No additional permission needed for this approved preparation, but owner execution and runtime gates remain actual dependencies.
