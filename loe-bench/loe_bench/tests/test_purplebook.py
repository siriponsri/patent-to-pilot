import os
import tempfile
import unittest

from loe_bench.purplebook import biosimilar_entries, parse_purplebook, read_pb_text

HDR = "N/R/U,Applicant,BLA Number,Proprietary Name,Proper Name,{t},Strength,Dosage Form,Route,Presentation,Status,Licensure,Approval Date,Ref. Product Proper Name,Ref. Product Proprietary Name,Supplement Number,Submission Type,Inter. Supp,License Number,Product Number,Center"
ROW = "N,Acme,761999,Biox,adalimumab-xxxx,351(k) Biosimilar,40MG,Inj,SC,PFS,Marketed,Licensed,\"July 27, 2023\",adalimumab,Humira,0,Original,,1,1,CDER"


class TestPurpleBook(unittest.TestCase):
    def test_license_type_alias_header(self):
        # 2023-08..10 and 2026 releases name the column 'License Type'; must still yield 351(k) rows
        for col in ("BLA Type", "License Type"):
            rows = parse_purplebook(HDR.format(t=col) + "\n" + ROW + "\n")
            e = biosimilar_entries(rows)
            self.assertEqual(len(e), 1, col)
            self.assertEqual(e[0]["bla"], "761999")

    def test_cp1252_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.csv")
            open(p, "wb").write("a \x96 b".encode("latin1"))
            self.assertIn("b", read_pb_text(p))
            open(p, "wb").write(b"\xef\xbb\xbfhello")
            self.assertEqual(read_pb_text(p), "hello")


if __name__ == "__main__":
    unittest.main()
