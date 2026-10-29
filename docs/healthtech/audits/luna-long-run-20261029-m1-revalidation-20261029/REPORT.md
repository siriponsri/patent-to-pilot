# M1 revalidation report

## Objective

Revalidate the confirmed M1 repairs at the current implementation head and close
the historical probe drift without changing prior audit records.

## Findings closed

F1 is covered at the external export boundary. A deliberately tampered evidence
item with an allowed `trade_name` field but restricted statement/value is projected
back to `trade_name: MitraClip` and `MitraClip` from the source payload. A second
literal-span item with a restricted quoted value is omitted. English and Thai
product-display Markdown and redistribution JSON contain neither restricted value.

F2 is covered through the actual Abbott adapter builder. Changing only
`runtime["patents"][0]["text"]` invalidates the manifest-pinned runtime hash and
fails closed. The same rejection is observed for both the authored synthetic
fixture and a local copy of the frozen Abbott cohort.

F3 remains covered by the existing current suite: typed policy resolution,
unknown/mismatched/blank policy IDs, unresolved-rights status, absence of verified
policy IDs, and uncovered disclosure-pair rejection. This package does not weaken
those checks or change evaluator/runtime separation.

## Corrected reproduction

The historical real-manifest probe copied a hardcoded subset of raw files and was
therefore stale after the adapter began validating every manifest-pinned raw file.
The new probe copies all 45 declared raw files plus the three runtime metadata
files into an ignored scratch directory. It records only file paths, sizes, hashes,
case counts, and failure messages in the canonical audit folder. The baseline
build produces three cases with 41 patent inputs per case. The post-copy runtime
text mutation is rejected before any dossier construction.

The synthetic probe also confirms that an allowed source field is the only payload
surface exposed externally, while the local research view retains the complete
synthetic payload. No network, provider, or neural inference path is used.

## Interpretation

The result is a current-head engineering pass for the repaired boundaries. It is
not evidence that product-level disclosures are semantic relevance gold, that
unjudged links are negatives, or that the development cohorts generalize. The
frozen Abbott cohort remains a development-only, single-company slice with no
final holdout and unresolved third-party redistribution limits.
