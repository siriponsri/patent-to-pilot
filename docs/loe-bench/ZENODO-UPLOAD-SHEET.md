# Zenodo upload sheet · LOE-Bench Track A

## Published

Zenodo published version 1.0.0 on 28 November 2026. Use version DOI `10.5281/zenodo.24629100` to retrieve the exact release. The concept DOI for all versions is `10.5281/zenodo.24629099`. The record has one file, `track-a-release.zip` (15,983,054 bytes), with Zenodo checksum `md5:2599a90565e28e69019207884877a407`. [Version record](https://doi.org/10.5281/zenodo.24629100) · [Concept record](https://doi.org/10.5281/zenodo.24629099) · [Independent restore receipt](receipts/RESTORE-DOI.md).

## Deposit instructions

Upload the single [`track-a-release.zip`](<C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/release/track-a-release.zip>) file (15,983,054 bytes) after planner review. The archive contains the scoring guide, source recipes and rights inventory. The [full SHA-256 inventory](<C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/release/SHA256SUMS>) is for verification. [Zenodo upload instructions](https://help.zenodo.org/docs/deposit/create-new-upload/).

| Zenodo field | Value |
| --- | --- |
| Resource type | Dataset |
| Title | LOE-Bench Track A prediction release |
| Creator 1 | Given names **Siripon**, family name **Srihangpiboon** |
| Creator 2 | Given names **Tuchsanai**, family name **Ploysuwan** |
| Version | `1.0.0` |
| Visibility | Public |
| Licence | Apache License 2.0 (`Apache-2.0`) for project material. openFDA and NCATS GSRS source fields retain CC0 1.0. |
| DOI | Select “No” for an existing DOI and let Zenodo mint a version DOI. |
| Publication date | Date of Zenodo publication |
| Keywords | LOE-Bench, loss of exclusivity, generic entry forecasting, ANDA, prospective validation, FDA, reproducibility |

## Description to paste

LOE-Bench Track A is a prospective benchmark for forecasting first final original US Abbreviated New Drug Application (ANDA) approvals. It tests how many eligible drugs with an approval within the window a fixed-capacity review queue captures. The cohort contains 651 ordered active-moiety keys from the 27 November 2026 source snapshot.

This archive contains the exact frozen prediction bytes for ten arms, a CPU scorer, the roster, a scoring identity projection, a hash-locked environment, an example output and instructions for independent scoring. The C9-SFT and C9-GRPO pair contributes 24-month forecasts. The other eight arms contribute 12- and 24-month forecasts. The windows mature on 27 November 2027 and 27 November 2028, respectively. Scoring requires verified FDA source coverage through the relevant maturity date.

The freeze was timestamped in OSF registration update 4 on 28 November 2026 at 11:30:06 UTC (10.17605/OSF.IO/P2SMD). The associated Git tag is loe-track-a-freeze-20261127. The freeze manifest SHA-256 is 8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d.

The project materials are available under Apache-2.0. The public openFDA and NCATS GSRS fields used in the identity projection retain CC0 1.0. The archive provides source recipes for separate acquisition under the source terms, including the NBER Orange Book archive. The archive contains frozen forecasts and a pending example. Prospective outcomes are scored at the registered readouts.

## Related identifiers

| Relation | Identifier scheme | Identifier |
| --- | --- | --- |
| Is supplement to | DOI | `10.17605/OSF.IO/P2SMD` |
| Is supplement to | URL | [GitHub repository](https://github.com/siriponsri/patent-to-pilot) |
| Is derived from | URL | [GitHub freeze tag](https://github.com/siriponsri/patent-to-pilot/tree/loe-track-a-freeze-20261127) |

## SHA-256 checks before publishing

| File | SHA-256 |
| --- | --- |
| `track-a-release.zip` | `acb533afb45f34f40d2ece2b97bc72b2b08fc3f6919fd73e1eb7064bf6e8049a` |
| `freeze-manifest.json` (OSF pin) | `8a78b318a8791649edbee2daab12a4db2d8aa72e33758cd27ae2145a9114c38d` |
| `release.json` | `879d27d9e60fb141d0e46ec2bc17aad3de61938460e678e7178841a8d2ca6d76` |
| `RIGHTS.csv` | `cfdc47614a26ec741ffdf9d21ed269100ca7ac5aa51831035ad5aee783a9f09c` |
| `requirements-tracka.lock` | `afaf49125c7f0198e692412f3632ffa8e3844d35cab721c703a1eef2461789a4` |
| `scorer-version.json` | `470d62ee13f27cdc80ef1cfddff4c12e87553c444a243895d837fa2e3f9bc2d4` |
| `roster.jsonl` | `31d35d30854006586bf0e9642e6b4abb5f11def7b3da2138599323292173597c` |

After publication, download the archive through the exact version DOI in an unauthenticated session and repeat the ZIP and freeze-manifest checks. Use the version DOI, the freeze digest and the full reviewed scorer revision to configure the workflow after default-branch integration. Send the version DOI and scoring guide to the prospective readout custodian. [Scoring guide](HOW-TO-SCORE-TRACK-A.md) · [Release receipt](receipts/RELEASE-KIT.md).
