# Pre-embedded factorial integration: synthetic only
research/sacr_factorial.py connects full-index acquisition with local coverage and
selection for G/G,G/L,I/G,I/L. All arms share one exact anchor vector, index,
eligibility mask and component profile. Each view family retains its own acquisition
union; mean-only and bottleneck selectors share that union. Component similarities
are computed once over the union of both candidate sets, then reused without adding
candidates to either arm.

An expected SHA256 binds the ordered passage IDs and family ownership before search.
Every component block receives exactly the same ordered passage slice for a family.
A component block consists of relation then explicit conditions, at most9 rows and
at most8 blocks. No per-component passage maximum is taken before conjunction.
Returned private evidence preserves passage IDs/positions and semantic_status unknown.
An empty component profile is rejected: declared anchor fallback orchestration is
still required, not silently replaced by invented coverage. Empty eligible output
remains empty in all arms.

Important limits: the order digest is a caller-supplied consistency binding. It does
not independently establish that vector rows encode those passages, that component
embeddings encode the right profile text, or that extraction/attachment is faithful.
Actual vector/index/encoder preflight and component text/source manifests remain open.
No benchmark adapter, generator, complete missing-query fallback, encoder or qrels
are inside this module. Status explicitly says PREEMBEDDED_FACTORIAL_ONLY_NOT_END_TO_END_SACR.
Only CPU NumPy synthetic behavior was checked; real GPU numerical parity/resource
feasibility and baseline ranking parity remain NOT_RUN.

Accounting records both actual acquisition scans (anchor is computed twice here),
actual reused component dot products, and standalone per-view-family component
dot products. Generation/embedding costs and timings/peak memory are explicitly
not included/measured. Do not call these complete method costs. No forced budget
padding or inference that all views survived was introduced.

44 tests passed:11 factorial,18 acquisition,15 selector. Tests cover same-view
collapse, separate acquisition unions, same-passage conjunction versus split evidence,
condition-free mean/bottleneck equality, empty universe, order/owner/anchor defects,
nonfinite/empty profile, duplicate passage IDs and binding rejection before search.
Ruff passed for two new files. No real data, generation, GPU job, test access or
re-encoding. Earlier failures remain preserved.

Next: bind validated profile component text and row identities before embedding;
define per-query status/fallback and full cost-ledger orchestration. Actual R1
curator/isolation/A03/parity and viable generation/fidelity review remain gates.
This is not R3, R4, scientific benefit or Goal completion.
