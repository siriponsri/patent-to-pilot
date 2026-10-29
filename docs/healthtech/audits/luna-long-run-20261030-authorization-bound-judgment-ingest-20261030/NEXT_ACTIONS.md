# M24 next actions

1. Obtain an owner-authorized semantic source manifest and pass the M23
   authorization preflight.
2. Invoke `ingest_relevance_judgments.py` with both the source manifest and
   the matching authorization manifest.
3. Inspect the validation report; preserve omitted pairs as unjudged and keep
   the frozen denominator, split contract, and untouched holdout unchanged.
4. Rerun HT-B0a/B0b/B1/B2/B3 only after the real judgment manifest passes.
