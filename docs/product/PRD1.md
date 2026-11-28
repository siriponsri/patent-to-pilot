# PRD1 development demo

The demo packages a US first-final-ANDA forecast with a dated evidence bundle for BD, R&D and FTO review. Open the [Thai moxifloxacin dossier](../../product/demo/dossiers/U-U188XYD42P-2014-01-01-24m.th.html) or its [Thai PDF](../../product/demo/dossiers/U-U188XYD42P-2014-01-01-24m.th.pdf). The HTML links to the English edition. The development outcome reveal is collapsed in HTML and visible in the PDF.

## Rebuild from the repository root

```powershell
py -3.12 -m product.mwd.build
py -3.12 -m product.mwd.audit
py -3.12 -m product.mwd.render --pdf
py -3.12 -m pytest product/mwd/tests
```

The build uses NumPy through the guarded LOE-Bench C3 input adapter. HTML rendering and the C8 CLI use the standard library. The tests also require pytest and jsonschema. The default private artifact root is `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench`. Override it with `build --private-root`. Keep the frozen score exports, `raw-20261127`, `moiety`, `ob_editions`, `piv`, `challenge` and `medicaid_sdud` in their expected layout under that root.

PDF output uses the Python Playwright package to control the installed headless Chrome at `C:/Program Files/Google/Chrome/Application/chrome.exe`. Install TH Sarabun New for the Thai output. The HTML falls back to Segoe UI. Pass `render --dossier <path>` to render one dossier, and `--output-dir <path>` to choose a destination. The committed HTML ships with embedded styles and needs no network to display.

## Contract

- [Dossier schema](../../product/mwd/schema/dossier.v1.schema.json) uses JSON Schema Draft 2020-12. The forecast contains native M3 and B1 probabilities, a 1-based M3 rank, capacity, queue flag and development status. `TRACK_A_FROZEN` is reserved for future consumers of the contract. The builder emits only `DEVELOPMENT_ONLY`. The observed outcome uses the window `(as_of, window_end]`. A null date means no observed first final approval in that window.
- `queue-<as_of>-<horizon>m.json` uses schema tag `mwd.queue.v1`. It contains `as_of`, `horizon_months`, `window_end`, `status`, `queue_size`, `tie_rule`, the score hash, and `ranked_rows` with key, display name, M3 and B1 probabilities, rank, membership and development outcome flag. `capture` records eligible rows, observed events, captured events, queued rows without an event, missed events, recall and precision. A zero denominator produces null. The product tie rule is descending native M3 then ascending key. Published LOE-Bench comparisons use fractional boundary ties.
- `DEMO_MOLECULES.json` is an ordered array of the four highest-ranked supported queued events, the first queued false alarm and the first event outside the queue at 2014-01-01 and 24 months. Each record contains the active-moiety key, GSRS display name, M3 rank and selection role. The build uses all scheduled cells where each selected molecule is eligible. If a GSRS key has a native-name component, that component supplies the display fallback.
- `docs/product/evidence/<key>.json` can provide a `claims` array for `thai_asean` and a `sources` array in the dossier shape. Use `U-<UNII>.json` for a single UNII on Windows or replace consecutive non-alphanumeric characters other than underscores and hyphens with a single hyphen. An optional `key` field verifies the case identity. Current lookups require `time_basis: "current_lookup"` and visible current-lookup wording in both languages. With no file, the report points the evaluator to DIP and leaves Thai status unknown.

## Evidence policy

- Eligibility and outcomes use the hash-verified C3 development projection through 2016-01-01. It supplies original final ANDA actions and exact raw-line locators for observed outcomes. The eligible group has zero final ANDA approvals in those linked records through its cutoff. Historical Orange Book product rows supply dated NDA approval evidence and linked dosage forms where available.
- Patent and exclusivity rows use the latest FDA ZIP proven public by the cutoff. A printed stale-edition warning identifies editions more than six months old. The report preserves the drug-substance and drug-product flags, use code, delist flag and listed dates. FTO checklist order uses DS before DP before use, nearest listed expiry within type, then exact patent-linked challenge as a tie-break. Check patent claim scope, status and relevant activities in each jurisdiction. The witness panel uses dated E7 FDA Paragraph IV records and E7b docket links with a filing-date public-access assumption. Historical evidence does not establish current enforceability.
- The C5 price scenario uses the 2019 FDA report, p. 9, preserved SHA-256 `5b748fa2eb20a4af86d1c28705add5e99a9351f58dbfaf6833736871c6610a4b`. The source is dated to month precision using its month's end for comparison. It is explicit retrospective scenario context. The C4 baseline is retrospective and vintage-uncontrolled. It checks Q2 of the preceding year against the pinned CMS national rows and the exact full-moiety FDA package crosswalk. Missing or incomplete linked counts remain unknown.
- C8 counts every claim once. A resolvable citation requires ID, version, locator and SHA-256 or HTTP(S) URL. The audit reports hash-backed coverage separately. A null publication date reflects an undated reference, artifact or query scope. Report claims default to as-of. The narrow contextual exceptions are the FDA scenario, retrospective Medicaid baseline and explicitly marked Thai/ASEAN current lookups. The distinct development reveal has its own outcome window check. Citation resolution does not establish semantic support or legal suitability.

## Demo selection and C8 results

The queue at 2014-01-01 and 24 months has 544 eligible rows, 108 review slots and 50 observed events. It captures 23 events. The six-case selection illustrates four evidence-rich captures, one false alarm and one missed event. Its case mix was selected for demonstration.

| Molecule | Active-moiety key | M3 rank | Selection role | Dossiers | Traceable claims | Hash-backed |
|---|---|---:|---|---:|---:|---:|
| Moxifloxacin | `U:U188XYD42P` | 6 | Supported event | 5 | 196/196 | 191 |
| Argatroban anhydrous | `U:OCY3U280Y3` | 12 | Supported event | 5 | 98/98 | 93 |
| Aripiprazole | `U:82VFR53I78` | 15 | Supported event | 6 | 703/703 | 697 |
| Bimatoprost | `U:QXS94885MZ` | 31 | Supported event | 5 | 184/184 | 179 |
| Gadolinium cation (3+) | `U:AZV954TZ9N` | 1 | False alarm | 6 | 464/464 | 458 |
| Solifenacin | `U:A8910SQJ1U` | 143 | Miss | 5 | 75/75 | 70 |
| **Total** | | | | **32** | **1,720/1,720** | **1,688** |

C8 reported zero future-dated as-of claims. The 32 URL-only claims are the DIP fallback. Nine dossiers have a retrospective Medicaid value for a linked package subset. The other 23 report unknown demand. The [executor receipt](../loe-bench/receipts/PRD1.md) records verification and next steps.
