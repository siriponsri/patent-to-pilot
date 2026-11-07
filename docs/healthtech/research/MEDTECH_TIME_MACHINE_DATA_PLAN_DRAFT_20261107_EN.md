# Medtech time-machine benchmark: data plan (DRAFT, 7 Nov 2026)

- **Status:** DRAFT. Nothing has been downloaded. Every download needs the owner's explicit approval, naming the file, source and size.
- **Owner decision (7 Nov 2026):** expand the data beyond DAPFAM before the time-machine claim is confirmed.
  - Why: DAPFAM caps the medtech time-machine population at about 65 queries (25 dev plus about 40 test).
  - The dev probe passed `GO_SHOCK` narrowly, on n = 25 ([audit](../audits/ptp-time-machine-dev-probe-20261107/README.md)).
- **Goal:** a public-domain, releasable benchmark of thousands of US medtech (A61) patents. Each is paired with the **older, examiner-cited** patents from **other fields** that it cites. The time-machine search is scored on it.
  - Retrieval method development happens on its dev part.
  - The DAPFAM test (Amendment 1 draft, E6) stays the untouched one-time confirmation on independent data.

## Source options

| Source | Access | What it has | Rights | Fit |
|---|---|---|---|---|
| **USPTO Patent Grant Full Text (XML, weekly)** on data.uspto.gov (`ptgrxml`) | The FAQ says bulk files are free and non-authenticated through the web pages. The API endpoint needs a free MyUSPTO key. **Verify with one pilot file** | Full text, CPC, dates, and references cited. The examiner-vs-applicant flag is expected in the XML; **verify against the v4.x DTD** | US government work, public domain | **Recommended.** The benchmark labels, and even the texts, can be released |
| Google Patents Public Data (BigQuery) | Needs the owner's Google account; the BigQuery sandbox has no card and allows 1 TB of queries per month | Publications with CPC, citations, US claims and description | Terms to verify on Google's dataset page | Fast to build with one SQL extract, but scan quotas and terms need checking |
| Lens.org Patent API | Needs the owner's account. Third-party pages say it is free for non-commercial use, about 1,000 requests a day | Citations, CPC, text | Terms to verify; one source reports a 2026 ownership change | Fallback |
| PatentsView | Needs a USPTO login (owner rule: agents do not log in) | — | — | Not used |
| HUPD (already local) | — | Application text, IPC3, dates; **no citations** | CC BY-SA 4.0 | Cannot supply targets |

## Recommended pipeline (USPTO XML, stream-processed on dr-train)

1. **Pilot (needs owner approval):** download **one** recent weekly grant XML zip, likely 100–300 MB, by direct web download.
   - Confirm three things: that no key is needed, the citation category field, and the CPC fields. Record the hashes.
2. **Full pass (needs owner approval, with the measured sizes):**
   - Stream the weekly grant files from 2002 to the present; XML starts in 2002, earlier years are in another format and are out of scope.
   - About 1,200 files, roughly 150–250 GB downloaded in total. Each zip is deleted after extraction.
   - Disk is the reason for streaming: dr-train has about 109 GB free and this laptop about 57 GB.
   - The pass keeps a compact JSONL of each grant: number, dates, CPC, title, abstract, first claim, and cited US patents with their category.
3. **Benchmark rules** (pre-declared in a protocol before any scoring):

   | Item | Rule |
   |---|---|
   | Queries | US utility grants with an A61 CPC, in a fixed grant-year window |
   | Targets | Cited US patents marked as examiner-cited, sharing no 3-character CPC code (IPC3-equivalent) with the query, and filed at least 5 years before the query |
   | Candidate corpus | All targets plus distractors sampled by year and section, at stated sizes. Corpus size changes hit rates, so two sizes are reported |
   | Split | Temporal and by CPC group, for example dev = earlier grant years, test = later ones, held out until a freeze |
   | Query text | A problem description without the solution: the patent's background section, or the frozen `PROBLEM` brief. Chosen on dev and stated as a leakage risk |
   | Arms | U (all patents) vs X (other-fields lane) vs M (mixed), time-filtered, as in the dev probe |

4. **Encoding:** PatEmbed-large on the V100, sized by the corpus decision. The GPU authorization window ends 15 Nov 2026 16:59 UTC (`local_execution.py`); a longer run needs a new owner window.

## Owner asks

1. Approve the **pilot download** of one USPTO weekly grant file (about 100–300 MB, data.uspto.gov) to dr-train.
2. If the web download turns out to need a key, register a free MyUSPTO account and API key. The agent does not log in.
3. Extend the V100 window past 15 Nov 2026 if the full build runs later.

## Risks

- **Citations are not a complete gold.** Examiner citations are incomplete and partly strategic. Unjudged is not negative, and known-link hits are not exhaustive recall.
- **Defining "medtech" by CPC is approximate.** A61 also includes cosmetics and pharma (A61K/A61Q), so the subclasses must be pinned, for example A61B/F/G/H/J/L/M/N.
- **Pre-2002 targets are excluded.** This biases the measured age gap down, which is conservative for a "years older" claim.
- **Distractor sampling changes absolute rates.** Report the corpus size beside every number.
- **Timeline estimate:** about 1 week for the pilot plus extraction, 1 week for the benchmark freeze and dev runs, then test.
