from datetime import date
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from zipfile import ZipFile

from loe_bench.challenge import ChallengeIdentity, CourtRow, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory, normalize_patent_number
from loe_bench.kleene import T3
from loe_bench.ob_history import OBHistory


FILED = date(2011, 12, 20)
CUTOFF = date(2012, 1, 1)
KEY = "U:EXAMPLE"
PATENT = "5322055"


class PatentChallengeTests(TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.raw = Path(directory.name)
        self.editions = []
        self.linker = SimpleNamespace(
            registry=SimpleNamespace(composition=lambda names: SimpleNamespace(key=KEY if names == ["EXAMPLE"] else "")),
            canonical=lambda key: key,
            entities={KEY: SimpleNamespace(nda_first=date(2000, 1, 1))},
            application_type=lambda row: "N",
            match=lambda row: (KEY, "ingredient"),
        )
        self.identity = ChallengeIdentity(self.linker, [("Example Brand", KEY, date(2005, 1, 1))])

    def add_edition(self, edition_date, captured, patent=PATENT):
        path = self.raw / f"{edition_date}.zip"
        with ZipFile(path, "w") as archive:
            archive.writestr("products.txt", "EXAMPLE~TABLET~Example Brand~Maker~10 MG~123456~001"
                                            "~~Jan 1, 2000~Yes~RX~Maker\n")
            archive.writestr("patent.txt", f"123456~001~{patent}~Jan 1, 2020~Y~~~\n")
            archive.writestr("exclusivity.txt", "")
        self.editions.append(dict(
            edition_date=edition_date, wayback_ts=captured, file=path.name,
            sha256=sha256(path.read_bytes()).hexdigest(), source_url="https://www.fda.gov/example.zip",
        ))
        return path

    def index(self):
        return FilingPatentIndex(OBHistory.from_records({"editions": self.editions}, str(self.raw)), self.linker)

    def history(self, court=(), proof=(), *, piv_fresh=False):
        edition = SimpleNamespace(version_date=FILED, wayback_timestamp="20111221000000",
                                  sha256="fixture", file="fixture.pdf", source_url="example")
        piv = SimpleNamespace(edition_asof=lambda cutoff: edition if piv_fresh else None,
                              entries=lambda selected: ())
        return PatentChallengeHistory(piv, self.identity, court,
                                      {"version": "fixture", "sha256": "hash", "url": "example"},
                                      proof, self.index())

    def test_normalization_preserves_series_and_rejects_non_grants(self):
        for raw, expected in (
            (" US 5,322,055 B2 ", PATENT), ("US005322055A", PATENT), ("0" + PATENT, PATENT),
            ("US RE 043,462 E1", "RE43462"), ("D599999", "D599999"), ("PP012345", "PP12345"),
            ("", None), ("000", None), ("EP5322055", None), ("2010/5322055 A1", None),
            ("US20100000001A1", None), ("5322055; 5322056", None),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(normalize_patent_number(raw), expected)

    def test_only_fresh_editions_proven_by_filing_are_loaded(self):
        self.add_edition("2011-12-01", "20111205000000")
        self.add_edition("2011-12-10", "20111221000000", "5555555").unlink()
        self.add_edition("2011-12-21", "20111222000000", "6666666").unlink()
        self.add_edition("2012-01-02", "20120103000000", "7777777").unlink()
        index = self.index()
        status, number, edition, rows = index.match(PATENT, FILED, CUTOFF)
        self.assertEqual((status, number, edition["chosen_edition"]), ("LISTED", PATENT, "2011-12-01"))
        self.assertEqual(rows[0][0], KEY)
        self.assertEqual(index.match("6666666", FILED, CUTOFF)[0], "PATENT_ABSENT")
        self.assertEqual(index.match("7777777", date(2012, 1, 3), CUTOFF)[0], "AFTER_CUTOFF")
        self.assertEqual(index.match(PATENT, date(2013, 1, 1), date(2013, 1, 1))[0], "NO_FRESH_EDITION")

    def test_selected_zip_must_match_pinned_bytes(self):
        path = self.add_edition("2011-12-01", "20111205000000")
        path.write_bytes(b"wrong bytes")
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            self.index().match(PATENT, FILED, CUTOFF)

    def test_closed_world_and_future_filings(self):
        self.add_edition("2011-12-01", "20111205000000")
        future = CourtRow("D.Del.", "1:12-cv-00001", date(2012, 1, 2), "", "", "TSV line 2", PATENT)
        for fresh, absent in ((True, T3.FALSE), (False, T3.UNKNOWN)):
            history = self.history([future], piv_fresh=fresh)
            self.assertIs(history.lookup(KEY, CUTOFF).state, absent)
            self.assertEqual(history.patent_evidence(CUTOFF)[1]["filed_cases"], 0)
            self.assertIs(history.lookup(KEY, future.filed).state, T3.TRUE)
            self.assertEqual(history.patent_evidence(future.filed)[1]["filed_cases"], 1)

    def test_name_and_patent_provenance_share_one_case_key(self):
        self.add_edition("2011-12-01", "20111205000000")
        court = [
            CourtRow("D.Del.", "1:11-cv-12345", FILED, "Example Brand", "EXAMPLE", f"TSV line {i}", PATENT)
            for i in (2, 3)
        ]
        proof = {"court": court[0].court, "docket": court[0].docket, "filed": FILED.isoformat(),
                 "brand": "Example Brand"}
        history = self.history(court, [proof])
        result = history.lookup(KEY, CUTOFF)
        self.assertIs(result.state, T3.TRUE)
        self.assertEqual([w.source for w in result.witnesses], ["RAI_COURT", "RAI_OB_PATENT"])
        _, patent = result.witnesses
        self.assertEqual(patent.locator, "TSV line 2, TSV line 3")
        self.assertEqual(patent.corroboration["case_type"], "ANDA_CORROBORATED")
        self.assertEqual(patent.corroboration["matches"][0]["orange_book"]["locator"], "patent.txt data row 1")
        _, audit = history.patent_evidence(CUTOFF)
        self.assertEqual(audit["filed_cases"], 1)
        self.assertEqual(audit["patent_case_key_pairs"], 1)
        self.assertEqual(audit["admitted_name_agreement"], {"exact": 1})

    def test_listing_without_moiety_approved_by_filing_is_only_a_linkage_hit(self):
        self.add_edition("2011-12-01", "20111205000000")
        self.linker.entities[KEY].nda_first = CUTOFF
        case = CourtRow("D.Del.", "1:11-cv-12345", FILED, "", "", "TSV line 2", PATENT)
        history = self.history([case])
        self.assertIs(history.lookup(KEY, CUTOFF).state, T3.UNKNOWN)
        _, audit = history.patent_evidence(CUTOFF)
        self.assertEqual(audit["cases_with_listed_patent"], 1)
        self.assertEqual(audit["cases_with_resolved_moiety"], 0)
        self.assertEqual(audit["row_dispositions"], {"LISTED_WITHOUT_DATED_MOIETY": 1})

    def test_rai_reader_keeps_patent_and_excludes_boundary(self):
        path = self.raw / "rai.tsv"
        path.write_text(
            "court\tcivilaction\tfiledon\torangebookproducts\torangebookingredients\tpatent\n"
            f"D.Del.\t1:11-cv-12345\t12/20/2011\t\t\t{PATENT}\n"
            f"D.Del.\t1:12-cv-12345\t01/01/2012\t\t\t{PATENT}\n",
            encoding="utf-8",
        )
        row, = court_rows(path, CUTOFF)
        self.assertEqual((row.patent, row.locator), (PATENT, "TSV line 2"))
