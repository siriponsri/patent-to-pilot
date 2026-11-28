# MWD assistance HTTP contract v1

`POST /api/v1/tasks` accepts JSON on the same origin as the reader. [Frozen OpenAPI](openapi.json) and the running gateway's `GET /openapi.json` expose the discriminated request and response schemas. No client field selects a provider, model, source URL or route.

## Requests

Set `Content-Type: application/json` and send `Idempotency-Key` with a fresh UUID for each deliberate action. Keys are scoped to the authenticated identity and retained for the life of the ledger. A duplicate returns a conflict even when the first attempt failed or completed. After a network error preserve the key and surface the uncertain result. The gateway stores no response text for replay.

```json
{
  "dossier_id": "U:82VFR53I78",
  "snapshot": "2012-01-01",
  "horizon": 12,
  "language": "th",
  "task": "A1"
}
```

The dossier ID is `key` from the released index. Use `as_of` for the full ISO snapshot date. Horizon is 12 or 24 months. Language is `th` or `en`. Send the selection currently open in the reader. The gateway rejects extra fields and unknown selections.

| Task | Additional fields | Fixture behavior |
|---|---|---|
| A1 | None | Thai or English cited sample, with canonical forecast data when available |
| A2 | `audience` is `fto_evaluator` (default), `dip` or `thai_fda` | Cited checklist draft where eligible evidence exists. Missing in-snapshot checklist evidence yields abstention |
| A3 | `question_id` is `market_window`, `competition`, `thai_status` or `next_checks` | Answer from the selected dossier or abstain. Map and confirm the question locally before sending |
| A4 | `patent_publication`, e.g. `US5006528`, and positive integer `claim_number` | Abstains with `claim_text_missing` and a lookup step. B3 supplies rights-cleared exact text and dependency data |

Keep unmatched questions, letter edits, addressee names and signatures on the device. Format the A2 draft in an editable panel and preserve the returned provenance for the review and export workflow.

## Responses

| HTTP | `state` | Handling |
|---|---|---|
| 200 | `ok` | Show the draft, its label, disclaimer and citations |
| 200 | `abstained` | Show the reason and next step supplied by the gateway |
| 401, 403, 404, 409, 422, 429 | `rejected` | Resolve identity, origin, dossier selection, duplicate/active attempt, input or quota according to `reason` |
| 503 | `unavailable` | Keep the reader available and surface the provider, billing, route or ledger reason. Automatic resubmission is disabled |

On success, `items[]` holds text and dossier claim IDs. Resolve each ID through `citations[]` for the source ID, version, SHA-256, locator and optional URL. A null source digest reflects unavailable original bytes. Render text using text nodes and use server-supplied URLs for navigation. `forecast` is a separate nullable canonical probability with its claim ID, horizon and endpoint. `provenance` contains the provider, model, prompt version and ISO generation timestamp. `reading` is nullable and reserved for the B3 verified original claim and span offsets. On any other state, use `reason` as the stable machine field. `message` and `next_step` are English fallback strings that the UI can localize by reason.

The minimal B1 check verifies claim-ID membership in the evidence projection and resolves the references. B2 owns numeric, date, semantic and citation validation before live outputs can be enabled. All results use `Cache-Control: no-store`.
