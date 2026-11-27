# E6-alt research receipt

**Disposition: PASS for source assessment.** The [source report](../CHALLENGE-SOURCES.md) recommends dated EDGAR disclosures and a candidate-to-document search using the Rai et al. court-case file. The Eliquis filing establishes a challenge at the 2017 year-end cutoff. The observed date difference between court issuance and repository ingestion prevents using the 2020 Eliquis opinion as a 2017 witness. Sample selection was purposive and included product matches that must be rejected.

| Check | Result |
|---|---|
| Ownership | Dedicated worktree at base `c68063a4`, branch `loe/E6alt`. Initial worktree clean. E6 had a separate checkout. Only the report and this receipt are assigned. |
| Source integrity | Public HTTP bodies hashed in memory. PDF page numbers in the report count the PDF's first page as 1 unless designated printed. Two scanned-page contact sheets were visually checked. |
| Record checks | Pfizer Q2 and FY2017 filings, three Rai case–patent rows, three OCE mirror rows, two GPO opinions with MODS, two CourtListener reporter entries, two Federal Register documents, two tentative letters, two first approvals and two suitability petitions. FDA landing page checked for publication history and schema only. |
| Historical limits | Exact launch day and a guaranteed current FDA publication interval remain unknown. Original OCE 2020 rows and pre-cutoff posting dates for the two tentative letters remain unverified. CourtListener search required authentication. |
| Scope | Research only. No protected cohort, benchmark labels, forecast run, GPU, paid service or login. Coverage, incremental positives versus E6, model effect and automated ingestion are NOT_RUN. No FDA list download or archive crawl. |
| Integration | Planner can first verify the 2017 filing against the dated NDA identity, preserve its brand-level scope, and trace the two separate Eliquis dockets to public pre-cutoff text. Keep other cases unknown until equally documented. |

## Retrieval record

All entries were retrieved **2026-11-27, Asia/Bangkok**. SHA-256 covers the successful HTTP response body after transport decoding, including the compressed ZIP for ZFILE. For the five SEC pages in the second table, the available representation was web-reader text. The SHA-256 there covers the returned numbered content lines after removing line prefixes, joining with LF, trimming outer whitespace and encoding as UTF-8. Those five digests identify the excerpt viewed. They cannot authenticate the original HTML. For machine replication of case records use the issuer PDFs, tabular file, Govt. PDFs and record locators in the report.

| Fetched source | SHA-256 |
|---|---|
| [GUIDE](https://www.fda.gov/media/102650/download) | `a5f7eae703d151eb715f6c7f8cd6af83009c5eece36476dafcdb3d82586450aa` |
| [DVAPI](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/YCMKVU) | `4c3f680cbb251bd42a1c7be4a62bc0000783d705f8978d4e46753ef95ae12b36` |
| [ZEN](https://zenodo.org/records/10426559) | `86c61be035e8a1d382210c39d3793e3f42cebc4ca33c88a3321a45751ec876d8` |
| [FTERM](https://www.fda.gov/about-fda/about-website/website-policies) | `253e9d93b83d7537495c6914c9ffe95119fdcb398b32391b523c10c0fbe15a5c` |
| [GPO](https://www.govinfo.gov/help/uscourts) | `cbb1a5cf9712f70e589b108a27331c2a69234675038d833c5f69840f8d014c5e` |
| [FRHELP](https://www.govinfo.gov/help/fr) | `5918fb658af9124c31e0814304cc2d4ae53954f98fe917b9be87c2b1033cb055` |
| [CLAW](https://www.govinfo.gov/about/policies) | `d9e3a2f1cb4486ab4ecc4eff640f94f9a9bb8655ca71ff00694b236e7011ad1c` |
| [HIST](https://www.law.nyu.edu/sites/default/files/ECM_PRO_064165.pdf) | `e2d0f6cbee35d89850e7f1471bb773bb69d1b89a24c72d7cf767ca59e40441fa` |
| [GENIDX](https://www.fda.gov/drugs/first-generic-drug-approvals/anda-generic-drug-approvals-previous-years) | `aa65d752d8926d3705e728cb857b4386c110428ffc2789d965abb9c1398a908b` |
| [OTHERM](https://www.govinfo.gov/metadata/granule/USCOURTS-ilnd-1_14-cv-10150/USCOURTS-ilnd-1_14-cv-10150-0/mods.xml) | `feb7c612f4bd720537c2038d13f7993c71f0bacfebe6d848cd7164b5670d3277` |
| [GEN](https://www.fda.gov/drugs/first-generic-drug-approvals/2019-first-generic-drug-approvals) | `3b06ddba3712996367661b87b61e64288ab384bb4522e5975aecfe9f37a2374e` |
| [PFE1](https://s206.q4cdn.com/795948973/files/doc_financials/2017/q2/10-Q.pdf) | `a7f32bc2c40be4d2de8370e805f4cdaa627ae4cc0a85f8e75f3de9eb4e90afb4` |
| [OTHER](https://www.govinfo.gov/content/pkg/USCOURTS-ilnd-1_14-cv-10150/pdf/USCOURTS-ilnd-1_14-cv-10150-0.pdf) | `d6cacf4449869d8f823200f83c8bf07a81ba3d1865b947e72527e9f000df1a36` |
| [PFE2](https://s206.q4cdn.com/795948973/files/doc_financials/2017/q4/Form-10-K-2017.pdf) | `254e545196c2fdc9801e4272c026ee7069a6e836553820e3d05c09dc27155abd` |
| [CL](https://wiki.free.law/c/courtlistener/help/api/bulk-data/bulk-legal-data) | `99f7ff4afba1a1374ed6d67ceaa717c66b34a0b378a667e3b71a3d3b40da02e3` |
| [ZFILE](https://zenodo.org/records/10426559/files/litigation_patents.csv.zip?download=1) | `dc362be43dadd0ac4d251af8cdbee171478543e417f553a2e7ad934ad607d952` |
| [RAI](https://lawcat.berkeley.edu/record/1257859/files/0003-37-1-Rai.pdf) | `dcb7276db7d2cb546de643205890591943848a35cd26a2187ee1fe68caf0086d` |
| [TA2](https://www.accessdata.fda.gov/drugsatfda_docs/appletter/2019/210013Orig1s000TAltr.pdf) | `4e03d65a4a1eda547504b385d5e3ecec92e240465a7fcc3126605f3a85aa0b8b` |
| [TA](https://www.accessdata.fda.gov/drugsatfda_docs/appletter/2020/210053Orig1s000TAltr.pdf) | `03f892e0086a2e6a5c626b4d1f1dd678d5cb8dface543f2e880da1f53a81370c` |
| [LIP](https://www.govinfo.gov/content/pkg/USCOURTS-njd-3_12-cv-02389/pdf/USCOURTS-njd-3_12-cv-02389-8.pdf) | `7cb64a3a316cd532ad350c3b14f34639fd17695cc1f615711f5803aa97bea956` |
| [CLCASE](https://www.courtlistener.com/c/f-supp-3d/282/) | `83c58a40af26a0ab06db632e3626488dba2af4a50aa681753028098bb6b7016d` |
| [DF](https://dataverse.harvard.edu/api/access/datafile/4789869) | `abb54817c8e6fbc90077007a42bb1cd7870a64940ce3aa7a7d36d83dafaa06e5` |
| [CLVOL](https://www.courtlistener.com/c/f3d/457/?page=1) | `c9a504d355235a6e401ced019ef67ddba67b0dc84c442a090db45ce0d2d5e451` |
| [NOS](https://www.ded.uscourts.gov/sites/ded/files/news/NOS%20835%20ANDA.pdf) | `b461b28c55d752647c568cbe4533cd5008eb46476469e99dfad1bfa2b01d56d2` |
| [FRB2](https://www.govinfo.gov/content/pkg/FR-2003-03-13/pdf/FR-2003-03-13.pdf) | `e922f8c0a44ffcb8ca3bf23652f2251b5823f68fcd7fb11e42c995e265939e13` |
| [FDAABOUT](https://www.fda.gov/drugs/drug-approvals-and-databases/about-drugsfda) | `5691131620ffcd5de7b0871a06aaa1113bfc5fe973d43683568fd685500ce9c6` |
| [FDADATA](https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files) | `00043a8c2232e2e15c0e8e148bcf8361a83297e53322c55f94f1f806a37ab213` |
| [ZAPI](https://zenodo.org/api/records/10426559) | `06cb8655258350940502eb5e6aedb767b8ac889abaabdce8bf8e4f2a1f93956b` |
| [PET](https://www.fda.gov/media/93090/download) | `dcfb024b06c84f80eec06d47477d0fa9e0a171d7ae8e46643284be62c5138a43` |
| [DIST](https://www.govinfo.gov/content/pkg/USCOURTS-ded-1_17-cv-00374/pdf/USCOURTS-ded-1_17-cv-00374-3.pdf) | `d5108cd90c6680a3bc8cfc27870fea226831302324b3ef22cca8f6319e47265f` |
| [FRX](https://www.govinfo.gov/content/pkg/FR-2015-12-10/pdf/2015-31096.pdf) | `6d9a5df8e6b9b47937fb95e9c28405403eae5ae42bc8a931bc5bdea0506f1d8e` |
| [ORIG](https://www.thefdalawblog.com/2024/09/happy-40th-anniversary-hatch-waxman-were-celebrating-by-providing-access-to-a-new-archive/) | `25283b93af94a746c90ceb58827ec572865607f709b343e5495eef889a21c3fa` |
| [ANN](https://www.uspto.gov/about-us/news-updates/patent-litigation-data-through-2016-now-available) | `1273cc9d80d387cea637b68fa5902ae3f993ab240ef9858b673133f5f6a68323` |
| [MAP](https://www.govinfo.gov/sitemaps) | `a121086262a13093f98e3cd60987c4b20b3575b1c1c601783adae6ddef4c80f7` |
| [FDA](https://www.fda.gov/drugs/abbreviated-new-drug-application-anda/patent-certifications-and-suitability-petitions) | `784c01c0405e2dcd48b0442702088612a26c530497c1685cc4c7fd8a741778b2` |
| [USP](https://www.uspto.gov/ip-policy/economic-research/research-datasets/patent-litigation-docket-reports-data) | `e9d4ee21caa2ecc7ac650085442103e517c7cd9d3bc9f36d6b50e0ce0da30092` |
| [PLOS](https://doi.org/10.1371/journal.pmed.1004540) | `3820eecf7c47cf8403657432a37bc5a607b5d979b44b5af3d17bcbdee96869c6` |
| [LETTER](https://www.thefdalawblog.com/wp-content/uploads/2024/09/00p-1556-pav00001-vol11.pdf) | `f8b15f29d181ded220a773f79a809ed0b734acd0cd984bf6410962cfeb09771e` |
| [MODS](https://www.govinfo.gov/metadata/granule/USCOURTS-ded-1_17-cv-00374/USCOURTS-ded-1_17-cv-00374-3/mods.xml) | `743186bf5afcbccbf5f7d52dad66c915d9d3eba4ff082c9f7ffb4945c2b5b9a1` |

| SEC text-view locator | SHA-256 of viewed text |
|---|---|
| [PI](https://www.sec.gov/Archives/edgar/data/78003/000007800317000039/0000078003-17-000039-index.htm) | `82595d735201ef08402cf1960b322bb11655321089aa747986afa6a6e4dee9e4` |
| [PK](https://www.sec.gov/Archives/edgar/data/78003/0000078003-18-000027-index.htm) | `f433ce9e9719826668d3beb4fd140054fc25a2de3befb23a28318491a52513f2` |
| [SECAPI](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | `b62eab09a111715d090b3dcb619425c31be614ec9f203de959eb44be27c4b8cb` |
| [EDHELP](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) | `37bcfd6708d0935a57b917137bef699639a5aaf455920485e710f55bb14628a9` |
| [EDTERM](https://www.sec.gov/files/about/webmaster-faq.htm) | `47aef170333d89ddadd601008c24d8f24b16ccfe646e4868684b5893285cc573` |

**Replay the table checks.** Read `patents.csv` inside the Zenodo ZIP and select `case_row_id` 10573, 10592 and 10638. Read the Harvard tab-separated file and select D.Del., Eliquis, civil actions 1:17-cv-00374 and 1:17-cv-00412, retaining the three patent pairs specified in the report. Its reported date bounds are the minimum and maximum parseable `filedon` dates across the file. Match each court PDF to the corresponding MODS constituent by granule ID. The package-level ingest field can coexist with several different issue dates.

**Access limitations.** OCE's official 2020 [patents link](https://data.uspto.gov/ui/datasets/products/files/PTLITIG/2020/patents.csv.zip) and [cases link](https://data.uspto.gov/ui/datasets/products/files/PTLITIG/2020/cases.csv.zip) returned an HTML application, not ZIP bytes. The open 2016 mirror supplied the three records. Direct SEC HTTP requests returned 403 for the BMS filing and index, Pfizer submissions JSON and API documentation. The two independently published Pfizer PDFs and the public SEC filing-index text views supplied the evidence. The [anonymous CourtListener request](https://www.courtlistener.com/api/rest/v4/search/?q=apixaban&type=o) returned 401. Its reporter volumes were readable. The academic dataset DOI redirected to an empty HTTP 202 response locally. The [Dataverse metadata API](https://dataverse.harvard.edu/api/datasets/:persistentId/?persistentId=doi:10.7910/DVN/YCMKVU) and [DataCite DOI record](https://api.datacite.org/dois/10.7910/DVN/YCMKVU) identified the released dataset, and file 4789869 was readable without credentials. The Federal Register developer page led to an access-request screen. GovInfo supplied the official issues and sitemap documentation.

The 2004 FDA reply was a seven-page scan with no searchable text. A web screenshot attempt timed out. Direct PDF retrieval succeeded and its visually checked pages document the monthly pilot, the decision to post submission dates prospectively and the change in cadence. The two local JPEG derivatives are in `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/challenge/`. Their digests are `a9b6e14f8d921797c8e9b0b0217b66fed0593bd4b504f90e7cb9618ccacf9aac` for `e6alt-fda-2004-pp1-4.jpg` and `00b61a4a3105c96e5959b8ab5c599f3b073bb61647143382eb08a02ce220f613` for `e6alt-fda-2004-pp5-7.jpg`. [Original signed letter, pp. 2 and 4–6](https://www.thefdalawblog.com/wp-content/uploads/2024/09/00p-1556-pav00001-vol11.pdf)

No code changed. Pytest was NOT_RUN. Publication target is `origin/loe/E6alt` on `siriponsri/patent-to-pilot`. Verify the published commit with `git ls-remote origin refs/heads/loe/E6alt`.
