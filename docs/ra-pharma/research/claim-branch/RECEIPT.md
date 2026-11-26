# Claim branch development result

**Structural conformance PASS. Read-efficiency contrast NULL on this document.** The shared-evidence specialist, cache-aware parent walk and full offline read all recovered the five independently transcribed dependency paths for three target claims in EP2298134 A1. Each opened four unique claim blocks. The specialist grouped three still-open rows' demand for claim 1 into one read. The parent-walk control also read claim 1 once by caching it. All four claims were required by the requested complete branch sets, so four unique claim blocks were a lower bound for this exact task.

| Condition | Shared reader | Cache-aware parent walk | Full offline reference |
|---|---|---|---|
| Four-read main cap | 4 reads, five supported paths across 3/3 rows | 4 reads, identical paths across 3/3 rows | 4 reads, identical paths |
| One-read failure probe | 1 read, no complete path, explicit requests for claims 1, 3 and 4 under cap | 1 read, same requests and zero complete paths | Outside probe scope |
| Claim 1 unavailable | 3 reads, zero complete paths, missing claim 1 identified in all five paths | 3 reads, same paths and requests | Outside probe scope |

The [structural key](conformance-key.json) was transcribed from the numbered claim text before the reader's outcome was generated. Claim 3 has two alternatives through claims 1 and 2. The second path inherits 1 through 2. Claim 4 preserves both routes through 3. The implementation attaches the target and each inherited limitation block with its own XML locator and document edition/hash. The weak signal that a publication cites another patent never enters the packet. Structural completeness provides no element-level mapping to a product, validity, infringement or FTO adjudication.

## Acquisition and version evidence

- Source is [European Patent Office publication EP2298134 A1, 23 March 2011](https://data.epo.org/publication-server/rest/v1.2/patents/EP2298134NWA1/document.xml), root `ep-patent-document` and English claim nodes `c-en-0001` through `c-en-0004`. One intentional REST request returned 15,246 bytes of XML and SHA-256 `e03018f582e9f5dcbb936c38755c6f54250eef73661376d33d4fea420fd95f0b`. The actual source is a mechanical article. This exposed example and any verified family aliases are excluded from future held roles.
- The [prospective scope and controls](PROTOCOL.md) and [machine freeze](freeze.json) identify the exact inputs. Freeze SHA-256 is `79870ee42a89d7ca594c3893234c0ada3dbace54e817cb3aea3ebc9d0dbe7997`. The protocol was written before retrieving XML, and the code, source and structural key were locked before the capture. The key is outside the reading entrypoint. The comparison used one capture. The Planner independently reproduced five paths and the 4-read/1,539-byte counts directly from the retained original. No independent human claim adjudication or reserved execution was performed.
- The local directory is `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-claim-branch-20261126/`. Retained decoded text and publisher XML stay there. `original.json` is 33,465 bytes, SHA-256 `d816042c9e42e874c00dfa4c455c60139c3d268e5672a09a04724c81103b1156`. To generate an engineering replay in a fresh private file, use the command below. Timestamp measurements will differ and the original file is exclusive-create.

```powershell
$case = 'C:/Users/User/Desktop/myProject/_private_artifacts/ptp-claim-branch-20261126'
rtk proxy python scripts/research/ra_pharma/claim_branch_probe.py (Join-Path $case 'EP2298134-A1.xml') (Join-Path $case 'replay.json')
rtk proxy python -m pytest -o addopts= -q tests/ra_pharma_research/test_claim_branch_probe.py
```

Logical counts are measured after common XML indexing. Each main arm opened 1,539 UTF-8 claim bytes. All seven runs together used 20 unique claim openings at the policy level and 6,417 decoded claim bytes. Indexing loaded the complete 15,246-byte file once and took about 0.69 ms. The seven reading-policy runs and packet computations together took about 0.59 ms before serialization. Timed CPU readings were zero at timer resolution. No model, paid service or GPU used. No latency improvement can be inferred from the logical reads or single timing.

## Development stop

The selected case cannot answer whether partial chart completion or choosing among interchangeable valid witnesses makes ordering reduce reads. A next microscope would require a separately attributable development-only source with genuinely optional witness passages or a useful lossy budget and an independently fixed completion objective. Greedy unmet valid rows per read is a relevant comparator with the shared cache. The current parser deliberately supports the single dependency and explicit numeric OR constructions on this source. Recognized claim-number expressions that are conjunctive, forward or ambiguous are marked for review. The Planner found that unrecognized references phrased as item numbers or preceding paragraphs can be classified as independent. The exact source hash limits this executable to the verified document. A broader parser must explicitly handle or abstain on these other cues. The lower bound for all-required paths already explains the null here.

The [TeamLab paper](https://aclanthology.org/2026.findings-aacl.16/) and [author release documentation](https://github.com/TeamLab/probing-rag-patent-amendment/blob/main/docs/corpus.md) are relevant to claim text paired with administrative events. The [release README](https://github.com/TeamLab/probing-rag-patent-amendment) declares CC BY 4.0 for data. Directory metadata lists one 53,963,235-byte combined `patentamend_7k.jsonl.gz`, a separate retrieval-pool index and a separate cohort file. Author documentation describes evaluation cohort, retrieval pool and replication reserve. No separately addressable development-only claim-text file was confirmed. The first capped recursive tree listing was truncated. A directory-only request supplied the names and sizes. No mixed corpus, cohort IDs, reserved outputs or index payload was opened. A separately served and audited development claim-text release could reopen this route.

## Code gate

CPython 3.12.10, existing S4 QA overlay, and a fresh short `ptp-branch-claim-r1` basetemp. The focused suite passed 2/2. Full `python -m pytest` finished in 264.24 s with 2,795 passed, 8 failed, 10 skipped and 1 xfailed, exit 1. The eight failures match the standing SACR exception IDs. Private `pytest.log` SHA-256 `f27afe53b778a0959301a5649a24b6f17a355b8491d51d10d8ffdb612a7a68a0`.
