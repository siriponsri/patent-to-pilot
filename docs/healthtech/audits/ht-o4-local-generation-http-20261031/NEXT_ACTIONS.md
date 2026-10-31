# Next actions

1. When the permitted runtime assets are available, run the named Abbott
   browser harness from `frontend/healthtech-web` with:
   `HEALTHTECH_ABBOTT_COHORT`, `HEALTHTECH_ABBOTT_RIGHTS_MATRIX`,
   `HEALTHTECH_ABBOTT_VECTOR_CONFIG`, and
   `HEALTHTECH_ABBOTT_PROVIDER=local-vector`.
2. For the full retrieval-to-generation browser path, also provide a
   server-owned `ht-http-local-generation-config-v1` and run with
   `HEALTHTECH_ABBOTT_PROVIDER=local-generation`.
3. Preserve the resulting sanitized receipt, model/pack hashes, resource
   facts, and browser outcome in a new continuation audit. Do not commit the
   temporary case bundle, vectors, model weights, or raw restricted payloads.
4. Keep OpenRouter dispatch closed until the canonical cumulative ledger,
   current account credit, exact route/authorization, and rights-cleared
   outbound prompt manifest are all evidenced.
