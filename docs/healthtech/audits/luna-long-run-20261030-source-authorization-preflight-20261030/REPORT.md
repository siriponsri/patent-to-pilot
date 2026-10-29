# M23 report

## Decision

Add a separate authorization preflight before semantic judgment acquisition.
This closes the missing operational boundary between owner permission and the
existing label-ingest validator without fabricating a source or labels.

## Contract checks

- Requires pinned source identity, revision, SHA-256, locator, and source class.
- Requires source-specific rights policy, exact rights clause, intended use,
  local-use decision, attribution flag, and explicit denial of provider
  transfer/public redistribution.
- Requires resumable acquisition, expected/max byte and file bounds, and safe
  relative raw/normalized storage paths.
- Requires exactly `relevant` / `not_relevant`, exact locators, adjudicator
  roles, and `unjudged_not_negative` for absent pairs.
- Requires at least two company groups, two family groups, a predeclared final
  holdout, and reject-on-leakage policy.

## Verification

The new validator, CLI, and regression suite pass alongside the existing
judgment contract, submission adapter, and G6 checks. The CLI smoke used an
authored synthetic authorization manifest only; no real source was read or
persisted.

## Not run

No data acquisition, source license adjudication, semantic review, baseline
rerun, provider call, paid inference, public release, or external outreach was
performed.
