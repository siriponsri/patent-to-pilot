# Confirmation queue — PTP-FIC-ORG-A v1.0.0

**Status:** bounded G04 fictional fixture; not an approved real-organization card.  
**Profile:** [profile.json](profile.json) · **Policy:** [policy.json](policy.json) · **Source map:** [source-map.json](source-map.json)

| ID | Critical question | Affected claim/route | Evidence now | Required state |
|---|---|---|---|---|
| CQ-A-001 | Does the organization own formulation equipment, use an external partner, or both? | formulation route and capability state | Public source reports expertise but does not establish ownership or availability | `pending`; keep capability `unknown` until confirmed |
| CQ-A-002 | Is external formulation support available for this project and timeframe? | external formulation route | Fictional stipulation permits consideration only | `pending`; do not label route feasible |
| CQ-A-003 | Does the silicon restriction apply only to substrate? | substrate route and downstream change diff | Fictional stipulation explicitly says substrate-only | `not_required` for this fixture; preserve scope in every change event |

## Queue rules

- Do not ask the owner to review every extracted token; queue only interpretations that can change a route or hard constraint.
- A pending item blocks only the affected claim/route. Unrelated source-linked artifacts may continue to draft and can become `ready_for_review` when their artifact/traceability checks pass.
- Confirmation changes the interpretation state; it does not rewrite the public source assertion or erase prior versions.
