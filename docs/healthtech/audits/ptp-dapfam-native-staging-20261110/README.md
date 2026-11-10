# Native DAPFAM curator preparation

## Verified v1 cause and bounded v2 preparation

[Read-only diagnostic](diagnosis-v1.json) proves all4 pins/split/count/type checks pass; earliest mismatch is corpus serialization hash. [Byte-only proof](newline-proof-v1.json): historical328,999,080bytes SHA42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d contains45,336 CRLF separators; normalize LF gives328,953,744bytes SHA0d57b65bb9f314dab82e6a77018a42bd9e824fa9fe9b6f75ee8eb475b216613b, exactly newly derived serialization. LF→CRLF reconstruction equals historical bytes. No corpus contents/labels returned to parent. Diagnostics10.75s and2.641s, no stage calls/model calls.

Fix accepts only LF serialization or its CRLF record-separator form if it equals the existing exact historical hash. No changed pin or semantic rewrite; manifest declares separator form.18/18 staging/native tests PASS, including exact historical restoration and refusal on real content change. V1 remains FAILED. A fresh v2 projection is the next bounded action under approved diagnosed-repair authority, with same31GiB/1800s/CPU8/8GiBoutput caps, prior attempts preserved, no automatic retry on further failure. Curator must recheck absent v2 destination/free disk and source revision before GO.

## Attempt v1 terminal failure — 21:34 Bangkok

Single real curator attempt FAILED before destination creation; no completion marker or output corpus. [Terminal evidence](attempt-v1.json): child10184/session72462 exit1, supervisor16.312s, child15.344s, peak committed memory3,644,051,456bytes,31GiB cap, no timeout/model/GPU calls. Generic handled input error initially hid exact category. No staging retry. Curator authorized one separate <=120s read-only diagnostic under same31GiB/CPU8 limits to compare pinned hashes, schema/counts and serialization; no dataset writes or protected values returned. Exact cause pending.

CLI now emits only whitelisted constant error categories, never arbitrary exception text/paths/source values.17 staging/native fixtures PASS including exception-redaction check. This messaging change does not relax any gate or repair data; failed attempt preserved. Parent previously tried two nonexistent prompt paths while inspecting SACR, then located actual quotes-v1 prompt; no prompt or generation changed.

## Prelaunch resource checkpoint

Curator temporary launcher synthetic tests:256MiB Job Object rejected512MiB allocation; timeout2s stopped sleeping child after2.031s with terminal receipt. Parent reviewed source, requested stronger affinity/flags readback before GO. Final child cap31GiB reserves1GiB overhead inside32GiB ceiling; affinity <=8 logical CPUs, thread env8, Arrow1, no GPU, wall1800s with kill/wait5s, no retry. Job limits affect only child processes, no ACL/system configuration changes. Windows memory/affinity contracts checked against Microsoft documentation: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information and https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information .

Scoped cumulative disk admission: local ptp temp/private Nov10 artifacts75,751,499bytes + remote Nov10 jobs12,066,816 +8,589,934,592 output reservation +134,217,728 code/log margin =8,811,970,635 <42,949,672,960. Local free96,772,603,904 at observation. Existing source data/weights/vectors not copied or charged anew. Recheck free capacity and absent output immediately before single dispatch. Curator remains waiting GO pending strengthened launcher proof. Parent does not parse protected source. Real output destination private sibling healthtech/ptp-dapfam-native-dev-20261110-v1; process/terminal receipts in curator temp run directory to be recorded on dispatch.

## Authorized curator subagent preparation

Owner authorized subagent-run curator, superseding personal execution for this task. Curator role dapfam_curator is preparing a temporary Windows Job Object launcher with synthetic cap tests; parent remains sole repo writer. Real stage waits for parent GO after source revision and disk/resource validation. No protected information returned. Shared host access limitation disclosed.

Added8GiB hard aggregate output-byte ceiling, with conservative pre-write projection plus per-write accounting; over-budget refusal precedes destination creation. Arrow CPU/I/O pools set1 and parquet use_threads=False; launch env/affinity caps still required. Updated staging/native checks16/16 PASS. This is an output reservation inside existing40GiB aggregate allowance, not a reset or new allocation. No real source parsing or staging has occurred yet.

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
