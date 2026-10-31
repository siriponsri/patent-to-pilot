# O4 remote HTTP generation browser acceptance — 2026-10-31

Status: `PASS_O4_REAL_HTTP_GENERATION_BROWSER_O3_API_BLOCKED_LOCAL`.

This continuation closes the named Abbott engineering path through Chrome,
loopback HTTP, server-owned PatEmbed retrieval, the frozen local Qwen3-8B
generation contract, history editing, and selected-version JSON export. It
extends the parent audit at
`../ht-o4-local-generation-http-20261031/README.md`; historical receipts remain
unchanged.

## Acceptance result

- Cases: `HT-DEV-MITRACLIP`, `HT-DEV-TENDYNE`, `HT-DEV-TRICLIP`.
- Browser route: source inspection passed with the selected evidence ID; no
  source mismatch was reported.
- Provider: `local-generation` with the server-owned PatEmbed runtime and
  pinned `Qwen/Qwen3-8B` revision
  `b968826d9c46dd6066d109eabc6255188de91218`.
- Generation: schema-valid for `3/3` jobs; measured model latency was
  approximately 32.89–33.12 seconds per case.
- History: version `1 -> 2` edit passed for all three cases.
- Export: selected version `2` JSON passed for all three cases.
- Accounting: three local generation jobs, zero paid/provider calls, and USD
  `0.00` paid cost.

Sanitized job IDs, result status, and the exact browser receipt are in
`browser-receipt.json`. No raw dossier, source payload, generated text, model
weight, credential, or private runtime path is stored in this audit.

## Runtime bindings

- PatEmbed corpus: 41 rows, 768 dimensions, 3 shards.
- PatEmbed queries: 3 rows, 768 dimensions, 1 shard.
- PatEmbed corpus manifest SHA-256:
  `75348afa4fede2535c09970d70353ecf9477f306a48fa46c71a445677f2302f1`.
- PatEmbed query manifest SHA-256:
  `45da46ee7dbd755f8ca8dd4c244ff6b9063f16253c27907e92ff0291c61c7e54`.
- Server-owned vector config SHA-256:
  `d244533de54f22576afad75d71dec939b3b0b9e1b3fd1992ece9ceca68eeda79`.
- Server-owned generation config SHA-256:
  `fa9b9eeac8f90a346923bdae034ae96c294813d2d7b53000303dd1d966d88a35`.
- Public provider metadata kept the OpenRouter paid gate closed.

## Boundaries

This is real product-path engineering evidence for the named cases. It is not
semantic device–patent gold, exhaustive recall, clinical suitability, FTO,
patent validity, investment merit, deployment readiness, publication evidence,
or commercial/user validation. O3 remains `BLOCKED_LOCAL`: canonical ledger
identity, current account credit, exact comparison authorization, and
rights-cleared outbound dossier prompts are still unresolved. No OpenRouter
request was dispatched.

## Verification

See `verification.json` for the command receipt and `CHECKPOINT.json` for the
resume boundary. The SSH loopback tunnel used for the acceptance is transient
and is not a required project artifact.
