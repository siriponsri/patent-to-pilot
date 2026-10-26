# Pepo documentation handoff

Status: **DOCS_READY_FOR_LUNA**
Prepared: 2026-10-26 (UTC)
Scope owner: Pepo (README and documentation assets).
Final integrator and publisher: Luna, under the owner's separate scoped commit/push authorization.

## Delivered files

All paths below are relative to the repository root.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `README.md` | 14911 | `9b787bd570c14b7f05cc182f59ad9a5bdfe6529df3bce996250843eada5aebb0` |
| `docs/assets/patent-to-pilot/logo.svg` | 1681 | `69f61c26504c6bba1edca51fa2bfa2c9eed9497708af36ed56e6daf273a75474` |
| `docs/assets/patent-to-pilot/logo-preview.png` | 19565 | `c62323e92c75e8a4f6652313e49336eea8d92a5356815a160efad040bcced17d` |
| `docs/assets/patent-to-pilot/workflow.mmd` | 429 | `61e0cbe7bf3152c62f8a95ef05caacc795594130c909fb38eb43ac03a3adcc26` |
| `docs/assets/patent-to-pilot/architecture.mmd` | 654 | `b914f058058573ed4a6f7dfaada58eeb9e26a76a93c58bfd00f513a71177c3c6` |
| `docs/assets/patent-to-pilot/DIAGRAMS.md` | 3346 | `b69af538c84f10d5173245c22ee0b2a62b14c70ae599ccfd3074849578e32434` |

The README describes the product vision, bounded implementation, evidence workflow, architecture, source-checked quickstart, reproducibility, contributor guidance, safeguards, and actual license status. The original SVG logo has an accessible title and description. Mermaid sources and readable text alternatives are included.

## Verification actually performed

- UTF-8 readback and SHA-256 verification of the delivered files.
- All 29 relative README links resolved to existing local paths.
- Both Mermaid blocks match their companion `.mmd` source files.
- SVG parsed and checked for scripts, event attributes, external references, foreign objects, DTDs and entities; none were present.
- SVG rendered locally to the supplied PNG with an already installed renderer; the image was visually inspected for clipping and legibility.
- Quickstart arguments and module names were checked against the existing scripts/configuration. No dependencies were installed for this documentation work.
- README replacement and incremental writes were guarded by expected hashes to preserve concurrent changes.

## Checks not performed

No clean-environment installation, workflow execution, pytest run, provider dispatch, inference, credential loading or live service request was performed for this documentation pass. The quickstart is source-checked, not execution-verified here. No Mermaid renderer was available, so Mermaid syntax was reviewed as source rather than rendered. Historical reports and receipts are cited with their limitations; they are not new independent scientific results.

Git metadata inspection was blocked by Git's ownership safeguard (`fatal: detected dubious ownership`). No `safe.directory`, ACL or security setting was changed. Branch, remote, upstream and publication state must be checked by the authorized final integrator in a permitted context.

## Luna integration checklist

1. Preserve Pepo's reserved README/assets scope while completing the comparison-layer work. Flag factual corrections rather than independently replacing the design.
2. Reconcile README status with final G10 correctness/search-readiness code and evidence. It currently calls that work active and B4 conditional.
3. When the comparison runner gains a verified fresh-output-directory option, replace the current caution about its fixed output directory with the actual tested command. Do not run the old command over retained evidence merely to verify documentation.
4. Keep synthetic transport echoes, mock mechanics, scientific pilot/main study `NOT_RUN`, historical W2 access `BLOCKED`, and the separate current W2 fairness work clearly distinct.
5. Report actual tests, errors, pending checks and limitations. Do not turn documentation or source-linked spans into a claim of full G10 completion, scientific utility, clinical validity, patentability or freedom to operate.
6. Recheck links and hashes if you edit these files. The table above records Pepo's delivered version, not a requirement to freeze later authorized factual corrections.
7. Before the owner's authorized combined commit/push, review the complete scoped diff, run affected checks, scan intended staged files for secrets/private data, and verify code/evidence/README consistency and redistribution rights. Stage explicit relevant paths, including this handoff; preserve unrelated dirty work.
8. Use only the established intended remote after verifying branch/upstream. Do not force-push, create a repository, change visibility, merge or deploy. Record the commit and verify the remote ref/available CI for that exact commit. If publication destination or sensitivity remains unresolved, ask narrowly before push.

## Scope preserved

This documentation work did not modify comparison code, tests, integration/adaptation modules, frozen evaluation, paid evidence, journals, `docs/research/pilot-next/`, the delivered Luna goal, or shared memory. No commit, push or deployment was performed. Client-tool inventory and installation proposals are a separate owner task and are not included in this public project handoff.
