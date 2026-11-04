# OpenRouter key metadata recheck r13

Read-only recheck performed after the owner recorded an initial OpenRouter MCP/provider limit of USD30.00.

The existing owner `.env` dispatch key was read only inside the approved observer. No credential was printed, copied, staged, or persisted. The observer received HTTP 200 from `/api/v1/key` and reported lifetime usage of USD0.0001464, matching the reconciled E2 legacy receipts. It still returned `limit=null`, `limit_remaining=null`, an empty budget list, and no account-scope binding.

This receipt therefore confirms that the owner-supplied USD30.00 value is recorded authorization/provider metadata, but it is not key-level remaining-limit evidence. The paid branch remains blocked before reservation. No generation request, reservation, ledger mutation, retry, or budget/window reset occurred.

The sanitized source receipt is `metadata-observation.json`. Its file SHA-256 is `ec8b5757a5f8eeb3d96c71dd78ee6a19724f78a9ac3ad8820233a3051daac03e`; its internal receipt SHA-256 is `fbf832664173bb0de1efc620c958c31bd35cfe278cba04dc93deb45c25b94ea0`.

Next evidence, only if the paid comparison remains required: a permitted non-secret observation of the dispatch key's remaining limit or explicit unlimited status, with scope and observation time. Do not send the key or repeat this check without new evidence.
