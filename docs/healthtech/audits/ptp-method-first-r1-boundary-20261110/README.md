# R1 input boundary: prospective implementation, synthetic verification

Date: 10 November 2026 (Bangkok). Base: `b72cea102d880781b3e1da269a956a54da4d9af9`.
Status: IMPLEMENTED_FIXTURE_VERIFIED; real staging, physical isolation and real baseline parity NOT_RUN. A01 remains open until those checks and prospective runner integration are complete. Goal ACTIVE; Codex remains the single active writer.

## Changes and reason

The frozen MTM runner reads mixed query metadata containing both splits' targets. This package adds a separate prospective input path rather than silently changing frozen code or historical receipts:

- `research/mtm_runtime.py`: strict, label-free query metadata, real calendar dates, typed identifiers/CPC3 codes, duplicate-key and duplicate-query/family rejection. A fixed-name manifest binds payload bytes and row count. The loader rejects test manifests before opening their payloads. Errors omit supplied field names and values.
- `evaluation/mtm_staging.py`: trusted-curator projection into separate runtime dev/test directories, dev qrels and protected qrels. It preserves populations and ordering, refuses overlapping/existing destinations, validates all rows before output, writes the completion receipt last, and does not claim OS isolation.
- `evaluation/mtm_dev_inputs.py`: evaluator-only dev qrels loader with exact population matching; rejects a protected manifest before opening its qrels.
- `scripts/healthtech/stage_mtm_metadata.py`: explicit curator entry point. Requires operator acknowledgement and prints counts/status only. This command has not been run on real data.

No frozen script, split, target definition, method configuration or benchmark score was changed. Prospective retrieval runners are not implemented in this package, so this does not yet prevent someone manually launching a historical unsafe command. Historical `analyze_mtm.py` test support remains a known access risk; it must not be used for new dev work.

## Verification

- `rtk proxy python -m pytest tests/test_mtm_input_boundary.py tests/test_mtm_pipeline.py tests/test_mtm_methods.py`: exit 0, **39 passed**, 3.80 s.
- `rtk proxy python -m ruff check src/patent_to_pilot/research src/patent_to_pilot/evaluation/mtm_staging.py src/patent_to_pilot/evaluation/mtm_dev_inputs.py scripts/healthtech/stage_mtm_metadata.py tests/test_mtm_input_boundary.py`: exit 0, all checks passed.
- All new fixtures are hand-authored. The apparent protected sentinel is fictional, not copied from a benchmark.
- Tests cover nested labels, construction tags, booleans/string dates, invalid dates/CPC, payload tampering (including recomputed hash), manifest redirection, duplicate JSON keys/IDs, population mismatch, cross-split family duplication, destination overlap and overwrite refusal.
- A spy verifies protected payloads are not opened on manifest rejection. Synthetic metadata projection preserves output of the actual frozen `keep_mask` helper on U/X and two view masks. This is mask parity, **not real dense-ranking parity**.
- Zero new GPU jobs, paid calls, experiments or real protected-label reads. No remote state revalidation was needed for CPU fixture-only work.

## Curator operation and limits

The tool reads the mixed source's protected labels, so it must be executed by an authorized trusted curator outside the development agent's label access. A CLI acknowledgement, a directory name, or a hash does not enforce an OS boundary. The curator must arrange that the original mixed source and protected output cannot be opened from the development process/mount. This package changes no ACL, account, hook or global setting.

Reviewable command template (placeholders must be bound by the curator; do not execute from the development agent):

```text
python scripts/healthtech/stage_mtm_metadata.py --trusted-curator
  --source <curator-only-mixed-metadata>
  --runtime-root <new-runtime-export-directory>
  --dev-eval-root <new-dev-evaluator-directory>
  --protected-root <new-protected-evaluator-directory>
```

All three output roots must be absent and disjoint. Runtime consumers receive only `runtime/dev`; dev evaluation receives its qrel bundle separately. The test runtime export remains unused until authorized. Source labels remain unchanged in curator storage; no payload goes to Git. Preserve failed staging directories for inspection rather than retrying over them. The receipt says `STAGED_NOT_ISOLATION_ATTESTED` until independent operational evidence establishes access isolation.

## Next bounded work

1. Implement the A03 auditor against these staged dev inputs and the exact frozen mask, without dropping queries or changing qrels; measure only after safe staging is available.
2. Implement A14 corpus/passage/model/vector bindings and same-shape/wrong-order rejection, using existing provenance before considering re-encoding.
3. Finish native DAPFAM loader/evaluator parity and denominator fixtures; keep native OUT separate from X masking.
4. Integrate the validated runtime path into a prospective parity runner; do not run historical commands on mixed metadata.
5. Present the complete staging/isolation procedure and remaining operational decision to the owner once the dependent tools are ready. Continue independent safe fixtures meanwhile.

Required method sections 8–13 and architecture section 15 were read in bounded chunks before implementation. The initial combined output truncated sections 12/13; both were read separately in full. No scoped AGENTS.md was found under src/scripts/tests; the repository has no `.agents` directory.
