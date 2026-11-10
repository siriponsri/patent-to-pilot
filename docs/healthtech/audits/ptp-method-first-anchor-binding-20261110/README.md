# Predeclared original-anchor fallback binding

2026-11-10 10:07:11 Bangkok; base 2d12d358ec3a62576bd09f5f766bf2df88ef968f. Authored anchor fixtures, no real ranking access.

Execution v2 adds required anchor_bundle_sha256; v1 behavior is preserved and cannot
accept a late anchor bundle. The journal validates v2 bundle bytes before directory
allocation, writes those exact private bytes exclusively, and rechecks them before stages
and finalization. Bundle binds dev split, baseline receipt digest, query/index/encoder
manifests, depth, ordered query/source records, mask digest and anchor ranking.

Mixed controller finalization permits failed/interrupted profile or canonical failed/empty
extraction only with this predeclared anchor, downstream stages explicitly skipped, and
query mask/eligible exposure matching the bound index. Four arms receive the same original
ranking, preserving failure state. Journal also rejects substituted fallback rankings.
Report lists bundle/baseline references, fallback count, external baseline costs NOT_INCLUDED
and actual baseline parity requiring external verification. No search/retry is performed.

Nine new cases;57 focused PASS;27 SACR files + MTM bound runner:319 PASS (session4492 exit0).
Ruff on six changed Python files PASS. Cases cover empty/failed/exception fallback, invalid
protocol/depth/encoder/baseline reference, changed bytes and ineligible anchor family.

Hash agreement is not proof that these rankings came from the historical baseline. Trusted
real receipt preparation, actual baseline parity, mask correctness, physical isolation and
baseline cost attribution are still required. Test baseline SHA and rankings are authored.
No raw rankings/source are committed. Malformed/failed view generation policy remains open;
resource memory/live caps, real model/index preflight and generation/fidelity gates remain.
Next resolve failed-view behavior against existing declared method policy, then memory and
resource gates. R3/R4 absent, R5 not authorized, R6 incomplete.
