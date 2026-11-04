# G7 portable candidate instructions checkpoint

Observed: 2026-11-04 Asia/Bangkok (recorded UTC `2026-11-03T23:43:51.7513342Z`)

## Candidate and scope

- Existing Patent-to-Pilot goal; no new goal or epoch.
- Worktree: `patent-to-pilot-long-run-20261103`.
- Branch: `codex/patent-to-pilot-long-run-20261103`.
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`.
- Tree state: intentionally dirty; unrelated owner/Claude/Luna changes preserved.
- Change type: installation/reproduction documentation only. No model, dataset, GPU, API, ledger, or provider work was rerun.

## Completed package

Root `README.md` now separates the two supported reproduction surfaces:

1. **Source checkout:** repository-relative `src/`, `scripts/healthtech/`, authored fixtures, and tests from a pinned worktree. Private research bundles remain owner-authorized inputs and are not implied by a public checkout.
2. **Installed Python candidate:** wheel `patent_to_pilot-0.1.0-py3-none-any.whl`, `237,355` bytes, SHA-256 `70b8b0d50d60ec4540d640864cee42495daaa68ceee8618c583dffe89b46784d`, installed with `--no-index --no-deps` and exercised through the installed package.

The documented installed-candidate check produced synthetic dossier JSON,
Thai/English Markdown, acquisition events, and a manifest, with `102/102`
tests passing and no skips. The instructions include Windows hash checking,
fresh-venv installation shape, sanitized private artifact recovery, and the
explicit boundaries that clean-machine dependency acquisition, public release,
restricted corpus/model redistribution, and provider credentials were not
verified or published.

## Verification

- Root README links: `15` checked, `0` missing.
- `git diff --check`: pass.
- Wheel hash and size: match the installed-candidate receipt.
- Installed-candidate result: `102 passed`, `0 failed`, `0 skipped`.
- Queue item: `portable_candidate_instructions = COMPLETE`.

## Resource and release boundary

- Paid provider calls: `0`.
- GPU jobs: `0`.
- Downloads: `0`.
- Ledger mutations/reservations: `0`.
- Public release/publish: not performed.
- Clean-machine dependency acquisition: not proven.
- Private raw payloads, credentials, evaluator-only data, and model weights: not added to Git.

## Next action

The continuation queue is exhausted for its current offline packages. Keep the
overall goal open because scientific evidence, paid API comparison, owner
review, and publication/submission dependencies remain incomplete. Resume only
from a new evidence-backed queue item; do not rerun successful model work for
documentation.
