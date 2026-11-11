# Graph compact v2: first CPU input inspection

The first compact v1 package was frozen but never staged or executed. Before
its first token measurement, completed R6 calibration revealed a prompt/validator
gap: findings for supported dimensions were not explicitly prohibited in the
prompt, although the interpreter rejected them. V2 makes that existing rule,
nonblank reasons and required references explicit. It changes no gold label,
semantic criterion, output schema, evidence catalogue or acceptance threshold.

R6 evaluator v1 remains FAILED_CALIBRATION:23 contract-invalid responses plus
one contract-valid semantic grading failure. Four invalid responses also omit
required flagged findings. Clarifying the prompt does not establish that these
failures are fixed. No old response is repaired or regraded into qualification.
New model calibration requires separate new-candidate authority; CPU inspection
does not grant it.

29 authored transport/controller/worker tests PASS. Production token counts
remain NOT_RUN at freeze. [Declaration](declaration.json) and
[transport](transport.json) supersede the unexecuted compact v1 package only.
This is still the first CPU attempt named
`ptp-sg-compact-input-preflight-20261111-v1`, not a rerun of a consumed attempt.
The original R6 Graph33/114 closure is retained separately.

The exact same282 source families and114 review parents are used. CPU2,
aggregate2GiB,600seconds, zero model/GPU calls, no truncation, no new extraction,
no Neo4j, no protected test. Input8192/catalogue256/risk20 remain unchanged.
All100 source coverage rows and86 abstentions remain in the denominator.

Calibration completed terminal exit0/PID0 and was reconciled once before staging.
Its whole1748.397555 seconds were conservatively charged as1749 GPU+fidelity
seconds, including setup/teardown. The previous pending200 local CPU seconds
were settled with it. Reserve1200 CPU seconds and charge a further100 conservative
local CPU seconds before staging; preserve the old8 CPU-hour ceiling and all
historical accounting. Package/output allocation remains in the existing4GiB
R6 reservation and40GiB total disk ceiling.

Current-state resource/staging/launch/terminal receipts, when present, supersede
this preparation snapshot. Do not execute the retired v1 staging helper.
