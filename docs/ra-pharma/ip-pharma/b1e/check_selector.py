"""Prospective selector checks on fictional local archives."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from selector import classify, original_date, prefix, run


class SelectionTest(unittest.TestCase):
    def test_original(self):
        self.assertEqual(original_date({("2021-01-01", "1"), ("2022-01-01", "2")}), ("2021-01-01", 1))
        self.assertIsNone(original_date({("2021-01-01","1"), ("2021-01-01","2")}))
        self.assertIsNone(original_date({("","1")}))

    def test_moieties(self):
        def reason(name):
            return classify({(name,"TABLET;ORAL","5MG","RX","YES")}, {("A","TABLET","5MG")},
                            {"A":"u1","B":"u2"}, {"X"}, {"TABLET"})
        self.assertEqual(reason("B; A")[1], ("u1","u2"))
        self.assertEqual(reason("B; X")[0], "KNOWN_INGREDIENT")
        self.assertEqual(reason("B; C")[0], "UNKNOWN_MOIETY_OR_CLASS")

    def test_order(self):
        rows = [dict(date="2020-01-01",nda=str(i),product="002",moieties=("A",)) for i in range(1,27)]
        rows.append(dict(rows[0],product="001"))
        n, selected = prefix(reversed(rows))
        self.assertEqual((n,len(selected),selected[0]["product"],selected[-1]["nda"]), (26,24,"001","24"))

    def test_join_and_duplicate_listing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with ZipFile(root/"f", "w") as f:
                f.writestr("Applications.txt","ApplNo\tApplType\n000001\tNDA\n000002\tNDA\n")
                f.writestr("Submissions.txt","ApplNo\tSubmissionType\tSubmissionStatus\tSubmissionStatusDate\tSubmissionNo\n000001\tORIG\tAP\t2020-01-01\t1\n000002\tSUPPL\tAP\t2020-01-01\t1\n")
                f.writestr("Products.txt","ApplNo\tProductNo\tActiveIngredient\tForm\tStrength\n000001\t002\tA\tTABLET\t2MG\n")
            with ZipFile(root/"o", "w") as f:
                f.writestr("products.txt","Appl_Type~Appl_No~Product_No~Ingredient~DF;Route~Strength~Type~RLD\nN~000001~002~A~TABLET;ORAL~2MG~RX~Yes\n")
                f.writestr("patent.txt","Appl_Type~Appl_No~Product_No~Patent_No\nN~000001~002~123\nN~000001~002~123\nN~000001~001~456\n")
            (root/"d").write_text('{"A":"u1"}')
            (root/"e").write_text("[]")
            files = {k:dict(path=v,sha256=hashlib.sha256((root/v).read_bytes()).hexdigest())
                     for k,v in [("fda","f"),("orange","o"),("dictionary","d"),("exposure_aliases","e")]}
            result = run(root, dict(files=files, forms=["TABLET"],excluded_names=[],excluded_ndas=[],excluded_us_grants=[]))
            self.assertEqual(result["original_ndas_in_period"],1)
            self.assertEqual(result["prefix"][0]["grants"],["123"])
            self.assertEqual(result["prefix"][0]["exposure"],"EXPOSURE_UNKNOWN")


if __name__ == "__main__":
    unittest.main()
