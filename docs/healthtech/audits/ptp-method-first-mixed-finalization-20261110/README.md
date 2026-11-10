# Mixed terminal cohort finalization

2026-11-10 09:57:49 Bangkok; base 5948638b2ec8cbf30669ea8859c1f66c59869bdf. Authored inputs only.

Journal now exposes verified terminal receipt/output pairs; unsealed reservations remain
unclassified and require process inspection. Completed dependencies use the same reader.
Controller finalize_mixed requires all six explicit terminal slots for every declared query.
It derives missing input from bound absent source plus all skips, review from canonical
profile/view replay plus no executed retrieval, retrieval failure from a terminal failed/
interrupted stage with earlier retrieval stages complete and later ones skipped, and ready
from the existing sealed full-chain finalizer. No query is omitted or rewritten as success.

Five new tests;40 focused PASS;26 SACR files + MTM bound runner:310 PASS, exit0 verified
for local session50935. Ruff PASS. Ready+missing keeps denominator2; review makes the
cohort unscorable; failed embedding preserves unknown costs; unsealed state is not guessed;
failed extraction without anchor evidence is refused before outcome artifacts.

No automatic skips or retries. Canonical failed/empty extraction and failed profile transport
still require separately bound original anchor results. Malformed/failed view generation
remains blocked on its declared family failure policy. These are explicit incomplete paths,
not an altered no-fallback method. Mixed finalization cannot manufacture anchor rankings.
Actual resources/model/index provenance, R1 isolation/A03/parity, generation compatibility
and fidelity remain unresolved; no real run or protected evaluation.
Next add predeclared original-anchor evidence and failure-family policy, then bounded memory/
resource/preflight acceptance. Terminal status handling is not live job supervision.
