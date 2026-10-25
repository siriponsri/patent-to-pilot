# G09/G10 audit regression fixtures

These are small synthetic, non-evaluator fixtures for the bounded development slice.
They exercise positive, negative, and unknown outcomes without copying expected answers,
source archives, or frozen methodology fixtures.

- `regression-matrix.json` records the input shape and intended assertion class.
- Tests construct the typed packets and verify the actual result and reason.

The fixtures are not benchmark data and do not establish scientific utility.
