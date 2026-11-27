"""Small synthetic analogues of the publicly observed FDA list layouts."""
from datetime import date
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile
import zlib

from ..kleene import T3
from ..piv_history import EntityMatcher, EntityProduct, PIVEntry, PIVHistory, parse_entries


def xlsx(name="Example Hydrochloride", when="12/20/2010", form="Tablets"):
    stream = BytesIO()
    with ZipFile(stream, "w") as archive:
        archive.writestr("xl/workbook.xml", """<workbook xmlns:r="urn:r"><sheets>
          <sheet name="PIV" r:id="sheet1"/></sheets></workbook>""")
        archive.writestr("xl/_rels/workbook.xml.rels", """<Relationships>
          <Relationship Id="sheet1" Type="urn:/worksheet" Target="worksheets/table.xml"/>
          </Relationships>""")
        archive.writestr("xl/sharedStrings.xml", "<sst><si><r><t>DRUG </t></r><r><t>NAME</t></r></si></sst>")
        numeric = when.isdigit()
        date_cell = f'<c r="D2"><v>{when}</v></c>' if numeric else (
            f'<c r="D2" t="inlineStr"><is><t>{when}</t></is></c>')
        archive.writestr("xl/worksheets/table.xml", f"""<worksheet><sheetData>
          <row r="1"><c r="A1" t="s"><v>0</v></c>
          <c r="B1" t="inlineStr"><is><t>DOSAGE FORM</t></is></c>
          <c r="C1" t="inlineStr"><is><t>RLD/NDA</t></is></c>
          <c r="D1" t="inlineStr"><is><t>DATE OF SUBMISSION</t></is></c></row>
          <row r="2"><c r="A2" t="inlineStr"><is><t>{name}</t></is></c>
          <c r="B2" t="inlineStr"><is><t>{form}</t></is></c>
          <c r="C2" t="inlineStr"><is><t>Example Brand 12345</t></is></c>
          {date_cell}</row></sheetData></worksheet>""")
    return stream.getvalue()


def tagged_pdf():
    labels = [
        "DRUG NAME", "DOSAGE FORM", "RLD", "DATE OF SUBMISSION",
        "Example Hydrochloride", "Tablets", r"Example \(Brand\)", "12/20/2010",
        "Other", "Capsules", "Other Brand",
    ]
    content = b"".join(
        f"/Span <</MCID {n}/Lang (en-US)>> BDC\n[({label})] TJ\nEMC\n".encode()
        for n, label in enumerate(labels)
    )
    compressed = zlib.compress(content)
    objects = [
        b"<</Type/Page/Contents 2 0 R>>",
        f"<</Filter/FlateDecode/Length {len(compressed)}>>\nstream\n".encode()
        + compressed + b"\nendstream",
        b"<</S/Table/K[4 0 R 5 0 R 6 0 R]>>",
        b"<</S/TR/Pg 1 0 R/K[7 0 R 8 0 R 9 0 R 10 0 R]>>",
        b"<</S/TR/Pg 1 0 R/K[11 0 R 12 0 R 13 0 R 14 0 R]>>",
        b"<</S/TR/Pg 1 0 R/K[15 0 R 16 0 R 17 0 R]>>",
    ] + [f"<</S/TD/K[{n}]>>".encode() for n in range(len(labels))]
    return b"%PDF-1.5\n" + b"".join(
        f"{n} 0 obj\n".encode() + obj + b"\nendobj\n"
        for n, obj in enumerate(objects, 1)
    )


class ParsingTests(unittest.TestCase):
    def test_xlsx_all_fields_and_excel_serial(self):
        entry, = parse_entries(xlsx(name="Example_x000D_Hydrochloride", when="40532"), "xlsx")
        self.assertEqual(entry, PIVEntry("Example Hydrochloride", "Tablets",
                                        "Example Brand 12345", "012345", date(2010, 12, 20),
                                        "PIV!2", "40532"))

    def test_tagged_pdf_and_undated_row(self):
        entry, undated = parse_entries(tagged_pdf(), "pdf")
        self.assertEqual(entry.ingredient, "Example Hydrochloride")
        self.assertEqual(entry.rld, "Example (Brand)")
        self.assertEqual(entry.first_submission, date(2010, 12, 20))
        self.assertEqual(entry.locator, "PDF table row object 5")
        self.assertEqual(undated.ingredient, "Other")
        self.assertIsNone(undated.first_submission)

    def test_reject_unrecognized_payload(self):
        with self.assertRaises(ValueError):
            parse_entries(b"%PDF-1.4\n", "pdf")


class MatcherTests(unittest.TestCase):
    def test_legacy_and_active_moiety_key(self):
        when = date(2010, 1, 1)
        piv = PIVEntry("Example Hydrochloride and Second", "Extended-release Tablets",
                       "", None, when, "test")
        form = "TABLET, EXTENDED RELEASE;ORAL"
        legacy = EntityMatcher([EntityProduct("EXAMPLE|SECOND", "Example;Second", form, when)])
        self.assertEqual(legacy.match(piv, when), "EXAMPLE|SECOND")
        code = "U:1111111111|U:2222222222"
        moiety = EntityMatcher([EntityProduct(code, "Example;Second", form, when)],
                               resolve=lambda names: code if len(names) == 2 else "")
        self.assertEqual(moiety.match(piv, when), code)
        self.assertIsNone(moiety.match(piv, date(2009, 12, 31)))
        wrong_form = EntityMatcher([EntityProduct(code, piv.ingredient, "CAPSULE;ORAL", when)])
        self.assertIsNone(wrong_form.match(piv, when))

    def test_ambiguous_alias(self):
        when = date(2010, 1, 1)
        entry = PIVEntry("Example", "Tablets", "", None, when, "test")
        matcher = EntityMatcher([EntityProduct(key, "Example", "Tablet", when)
                                 for key in ("N:EXAMPLE", "U:1234567890")])
        self.assertIsNone(matcher.match(entry, when))


class HistoryTests(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.raw = Path(directory.name)
        self.manifest = self.raw / "editions.json"
        self.rows = []
        self.cutoff = date(2011, 1, 1)
        self.matcher = EntityMatcher([
            EntityProduct("EXAMPLE", "Example", "Tablet;Oral", date(2000, 1, 1)),
            EntityProduct("OTHER", "Other", "Tablet;Oral", date(2000, 1, 1)),
        ])

    def edition(self, version, capture, data):
        digest = sha256(data).hexdigest()
        file = f"{digest}.xlsx"
        (self.raw / file).write_bytes(data)
        self.rows.append(dict(version_date=version, wayback_timestamp=capture, file=file,
                              format="xlsx", rows=1, sha256=digest, parse_status="PASS",
                              source_url="https://www.fda.gov/example.xlsx"))

    def history(self):
        self.manifest.write_text(json.dumps({"editions": self.rows}), encoding="utf-8")
        return PIVHistory(self.manifest, self.raw, self.matcher)

    def test_future_capture_and_future_edition_cannot_backfill(self):
        self.edition("2010-12-20", "20101222110000", xlsx(name="Other"))
        self.edition("2010-12-25", "20110102110000", xlsx())
        self.edition("2011-01-03", "20110105110000", xlsx())
        self.edition("2010-12-30", None, xlsx())
        history = self.history()
        self.assertEqual(history.edition_asof(self.cutoff).version_date, date(2010, 12, 20))
        self.assertEqual(history.challenge_asof("EXAMPLE", self.cutoff), T3.FALSE)
        self.assertEqual(history.challenge_asof("OTHER", self.cutoff), T3.TRUE)
        self.assertEqual(history.challenge_asof("EXAMPLE", date(2011, 1, 2)), T3.TRUE)

    def test_inclusive_six_month_floor_and_cutoff_capture(self):
        self.edition("2010-07-01", "20110101235959", xlsx(when="6/1/2010"))
        history = self.history()
        self.assertEqual(history.challenge_asof("EXAMPLE", self.cutoff), T3.TRUE)
        self.assertEqual(history.challenge_asof("EXAMPLE", date(2011, 1, 2)), T3.UNKNOWN)

    def test_undated_future_and_unlinked_rows_remain_unknown(self):
        for when, form in [("Pre - MMA", "Tablets"), ("1/2/2011", "Tablets"),
                           ("12/20/2010", "Capsules"), ("12/20/2010", "")]:
            with self.subTest(when=when, form=form):
                self.rows.clear()
                self.edition("2010-12-21", "20101223110000", xlsx(when=when, form=form))
                self.assertEqual(self.history().challenge_asof("EXAMPLE", self.cutoff), T3.UNKNOWN)

    def test_tampered_bytes_cannot_establish_absence(self):
        self.edition("2010-12-21", "20101223110000", xlsx(name="Other"))
        (self.raw / self.rows[0]["file"]).write_bytes(xlsx())
        self.assertEqual(self.history().challenge_asof("EXAMPLE", self.cutoff), T3.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
