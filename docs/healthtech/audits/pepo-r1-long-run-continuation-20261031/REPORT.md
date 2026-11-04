# R1 long-run continuation report

## Scope

The candidate continues Patent-to-Pilot O1-O4 under the existing `PTP-HT-OR-R1-20261028-USD8` authorization. The USD8 authorization and original 24-hour clock are reused. No new allowance, key, top-up, registry, or paid attempt is created by this continuation.

## Change set

The recovery patch was checked against `9ac38720d219b83acccaa92dcabc4480283914c4`, applied once on an isolated branch, and then extended with the reviewed migration seam. The migration accepts only an existing R1 journal with the expected policy and canonical identity. It creates no replacement SQLite file. A reviewed history anchor and a separately typed pre-R1 carryover are installed in the same journal under one transaction, then the canonical registry binds that exact path.

The budget snapshot now reports `historical_carryover_nano_usd` and includes it in committed and actual totals while leaving phase totals and R1 attempt rows separate. For the owner evidence, `USD0.0001464` equals `146,400` nano-USD, so conditional admission headroom is `USD6.9998536` before any unresolved exposure. That number is not treated as available dispatch budget until the live review gate passes.

## Gate result

The supplied owner evidence reconciles four settled legacy attempts to the sanitized OpenRouter usage observation. It is not an R1 all-attempt completeness proof. The canonical R1 journal path is not present in the candidate, and the process observation only identifies an `rtk.exe`-owned SSH transport; it does not prove external writer quiescence. The visual `USD10.00` receipt is retained as owner-supplied UI evidence, not as an API balance.

The paid runner therefore remains fail-closed. Live transport requires a reviewed history anchor with `writer_quiescence=verified`, zero reviewed unresolved exposure, a matching positive pre-R1 carryover, the single registry binding, current route/pricing, and current scoped account/key availability. No key was read in this continuation.

## O4 and research boundary

The private current FDA pack contains three cases and three exact message records for the local/API path. Its sanitized hashes are in `pack-receipt.json`. The current executor cannot run Qwen3-8B because the local runtime dependencies and visible model files are absent. The API branch is not dispatched. Existing parent O4 engineering evidence covers three Abbott browser/HTTP/local-generation cases, but it is not a matched fixed/adaptive scientific comparison. The current private runtime cohort has no evaluator references/groups in the permitted pack, so recall or paired deltas cannot be computed without importing labels or inventing them. The Stryker frontier is explicitly excluded.

## Acceptance

Engineering acceptance is `PASS` for the migration and gate implementation. Research acceptance is `PARTIAL`: no current local/API pair, no paid output, and no matched current-cohort fixed/adaptive metrics were produced in this continuation. The exact next unblock is the real R1 journal or sanitized all-attempt export plus verified writer quiescence, followed by a current authorized credit observation and permitted evaluator references/groups for the O4 research branch.
