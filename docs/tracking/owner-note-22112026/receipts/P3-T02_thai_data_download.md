# P3-T02 — Thai dataset download (owner decision D18)

**Done:** 23 Nov 2026 (UTC 00:01–00:02 for the downloads). **Spend:** USD 0 (public Hugging Face HTTPS, no account, no gate).
**Authority:** D18 in `docs/maintenance/OWNER-DECISIONS-20261122.md`. **Pins:** P3-T01 contract
(`receipts/P3-T01_thai_data_contract.md`) and `src/patent_to_pilot/workbench/datasets/registry.json`.
**Tool:** `scripts/research/fetch_thai_datasets.py` (stdlib download, run with `python -I`; row counts from parquet footers
via pyarrow metadata only). No data content is in Git.

Status fields: `method_evidence` NOT_YET_DEMONSTRATED (no retrieval run), `product_readiness` unchanged (never bundled),
`publication_readiness` unchanged.

## 1. What was downloaded

Every pinned revision resolved. For every parquet file, the local sha256 equals the Hub LFS oid and the size equals the Hub
size. README.md and .gitattributes (non-LFS) match the Hub git blob sha1 at the pinned revision. Row counts match the P3-T01
contract.

| Repo @ revision | License | File | Role | Bytes | Rows | sha256 (prefix) |
|---|---|---|---|---|---|---|
| `VISAI-AI/thai-gazette-evidence-retrieval` @ `87e695ee4951ff34932804431433ac55991ec374` | CC BY 4.0 | `corpus/corpus-00000-of-00001.parquet` | CORPUS | 18,772,903 | 25,000 | `d417ff90208e` |
| | | `queries/queries-00000-of-00001.parquet` | HELD_OUT | 167,030 | 2,000 | `2763d38bc51b` |
| | | `default/test-00000-of-00001.parquet` (qrels/spans) | HELD_OUT | 971,877 | 2,594 | `c5a41ade0ad0` |
| `VISAI-AI/nitibench` @ `9f75697075e0f5691e3b821037b908c05f1821a7` | MIT | `data/ccl-00000-of-00001.parquet` | HELD_OUT | 4,479,757 | 3,729 | `d9b8bdf1aaeb` |
| | | `data/tax-00000-of-00001.parquet` | HELD_OUT | 248,444 | 50 | `0a6c9d39a92e` |
| | | `data/nitibench-ccl.parquet` (non-config copy) | HELD_OUT | 4,480,677 | 3,729 | `ac28f0b16cc3` |
| | | `data/nitibench-tax.parquet` (non-config copy) | HELD_OUT | 248,552 | 50 | `966b08688b77` |
| `VISAI-AI/nitibench-statute` @ `069e774f015a50e801dbe2055a29be580c54a83c` | MIT | `data/ccl-00000-of-00001.parquet` | CORPUS | 1,777,237 | 5,127 | `f171a25878ad` |
| `airesearch/WangchanX-Legal-ThaiCCL-RAG` @ `654e1a10afc44ecaee36fd739bc90078dcc62388` | MIT | `data/train-00000-of-00001.parquet` | DEV_TRAIN | 17,970,460 | 8,211 | `c87708fb9a04` |

Each repo folder also holds its `README.md` and `.gitattributes` (role CARD). Total about 47 MB. Full hashes, sizes, Hub
oids and per-file download times are in the manifest.

## 2. Locations

- **Local:** `C:\Users\User\Desktop\myProject\_private_artifacts\thai-data\`, one folder per repo named `<repo>@<sha8>`, plus
  `MANIFEST.json` (repo, revision, license, scoreboard, role, size, sha256, Hub oid, row count, download time) and
  `SHA256SUMS` (17 data and card files, for remote verification).
- **dr-train:** **NOT YET COPIED.** On 23 Nov 2026 dr-train (`100.77.149.83`) was unreachable: SSH port 22 timed out on
  every attempt and `tailscale ping` got no reply, although Tailscale listed the node as active via relay `sin`. Planned
  target: `/data/ptp-paper2/thai-data/` (mode 700), verified with `sha256sum -c SHA256SUMS` on the remote side.

## 3. Held-out labelling

- The Gazette `queries` and `default/test`, and all four NitiBench files, are labelled **HELD_OUT** in the manifest. They
  were downloaded only because D18 approves the whole datasets for held-out evaluation of a frozen method.
- They were not opened beyond the parquet footer row count. No column values, labels or qrels were read, and they select
  nothing.
- The Gazette remains an exposed public transfer (P3-T01 §4). The WangchanX train split is the only candidate DEV source.
  Because NitiBench-CCL is derived from WangchanX, its overlap with the held-out CCL set must be audited before any use.

## 4. Not downloaded

- WangchanX `data/test-*` (same held-out family as NitiBench-CCL; not approved);
- the `assets/*.png` card images of NitiBench and WangchanX (not data);
- NitiBench+ (gated, not approved);
- ThaiOCRBench;
- any model weights;
- the Thai-LLM pretraining collection.
