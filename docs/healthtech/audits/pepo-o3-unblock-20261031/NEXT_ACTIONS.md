# Next actions

1. Provide only the exact location of the existing OpenRouter R1 journal, or a
   sanitized export containing every attempt ID, generation ID, reservation,
   actual/unknown billing state, and reconciliation status after the known
   historical receipts.
2. Provide a sanitized current account-credit/billing snapshot with timestamp,
   or expose the already-approved integration that can return it. Do not send
   credentials or create a new key; do not re-approve the existing USD8 scope.
3. Bind the verified journal with
   `scripts/healthtech/register_canonical_openrouter_ledger.py`, then rerun the
   API dry-run and live preflight on the same canonical registry path.
4. Use the refreshed public route/provider/parameter/pricing snapshot at
   `openrouter-qwen3-32b-endpoint-snapshot-20261031.json`; keep DeepInfra as a
   candidate only until the journal, credit, and rights gates pass.
5. Freeze the rights-cleared outbound pack and exact request bound. Only then
   run the sequential paired comparison within the original cumulative cap and
   existing deadline.

Independent offline engineering and O4 report work is complete and can proceed
without these inputs. Do not treat this audit as a paid-run receipt or as
semantic patent relevance gold.
