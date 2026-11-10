# CPU-ESCAPE-003 observed outcome

Status: **FAILED before all 14 cases; callback runtime NOT_RUN.**

One declared attempt used code archive `a9c1d640d0c950fc0c032339fac87a29fd622ab2`. The child exited 1 at the initial `declared payload mismatch` guard before tokenizer imports. Supervisor recorded 0.0748766 seconds, zero cases, no result file and zero model calls; this is not a grammar failure measurement or 0/14 executed cases. No model weights were loaded. Terminal UTC: 2026-11-10T03:58:53.704497Z.

`observed-result.json` preserves the terminal record, traceback and later process checks: child3823049 reaped and absent; supervisor3823048 absent. `launch.json` records dispatch. The retained HTTP service was not stopped. Original declaration, supervisor and failed remote job remain unchanged. No retry occurred.

## Byte diagnosis

`archive-byte-diagnosis.json` compares the five declared payload/code files against local checkout and Git blobs: all match their declared hashes. This initially excluded ordinary checkout changes but did not establish archive equality.

`transport-byte-diagnosis.json` reads the exact authored remote payload and independently creates a local Git archive of the same commit. Both are 37,318 bytes with 427 CRLF sequences, SHA256 `eae376bd3c618b6f964fe25af6d2fc69082d33f3e14068b13d285a7c02993b08`. Converting only CRLF to LF reproduces the declared payload SHA256 `71a047b9a422f9599ba80adf49b7fc53762ed9d0afcd0077cb7116fdeb8958a8`. Thus archive line-ending conversion explains the guard failure; transport preserved the archived payload. Remote code file hashes were not checked by the child because the first guard stopped it.

A first inline local diagnostic command had a quoting SyntaxError and performed no remote execution; a standalone read-only script completed the byte check. No grammar or model work was triggered by diagnosis.

## Next action and limits

Verify a byte-stable archive locally, including every pinned code/data file, without relaxing exact-byte guards or rewriting the failed declaration. Any later CPU run requires a new explicit declaration and bounded attempt; do not restart this job. No model dispatch follows automatically. Curator/isolation and view-failure decisions remain unanswered. R1 actual parity, generation/fidelity, R3/R4 and R6 remain incomplete; R5 is not authorized.
