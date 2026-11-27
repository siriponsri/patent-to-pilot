"""C-prime gate fixtures with fabricated cutoffs, editions and histories."""
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import freeze_gate


class FreezeGateTests(unittest.TestCase):
    def setUp(self):
        workspace = self.enterContext(TemporaryDirectory())
        self.root = Path(workspace)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()
        self.ob_dir = self.root / "editions"
        self.ob_dir.mkdir()
        self.projection = self.root / "projection.json"
        self.enterContext(patch.object(freeze_gate, "ROOT", self.root))
        payload = b"synthetic edition bytes"
        self.editions = []
        for year in (2016, 2017):
            filename = f"{year}.zip"
            (self.ob_dir / filename).write_bytes(payload)
            self.editions.append({
                "file": filename,
                "sha256": sha256(payload).hexdigest(),
                "edition_date": f"{year}-12-01",
                "wayback_ts": f"{year}1215000000",
                "source_url": "https://example.invalid/edition",
            })
        self.s0 = self.write_manifest("s0.json", {"t0": "2019-01-01"})
        self.config = {
            "status": "FROZEN_FOR_PREREG",
            "sealed_test": {
                "test_first": "2017-01-01",
                "outcomes_observed_through": "2019-01-01",
                "cluster_gate_horizon": 24,
                "min_distinct_event_drug_clusters": 50,
                "schedule": {
                    "12": {"test_cutoffs": ["2017-01-01", "2018-01-01"]},
                    "24": {"test_cutoffs": ["2017-01-01"]},
                },
            },
            "input_sha256": {"s0_manifest": self.s0},
        }
        self.write_config()
        self.histories = [
            {"drug_cluster": str(i), "nme_from": "2017-01-01",
             "first_final_anda": "2019-01-01"}
            for i in range(50)
        ]
        self.write_projection()

    def write_manifest(self, filename, data):
        payload = json.dumps(data).encode()
        (self.data_dir / filename).write_bytes(payload)
        return {"file": filename, "sha256": sha256(payload).hexdigest()}

    def write_config(self):
        self.config["input_sha256"]["ob_manifest"] = self.write_manifest(
            "ob.json", {"editions": self.editions}
        )
        self.write_manifest("FROZEN_CONFIG.json", self.config)

    def write_projection(self):
        self.projection.write_text(json.dumps({
            "s0_manifest_sha256": self.s0["sha256"],
            "histories": self.histories,
        }), encoding="utf-8")

    def assert_verdict(self, expected):
        output = io.StringIO()
        errors = io.StringIO()
        args = ["freeze_gate.py", str(self.projection), "--ob-dir", str(self.ob_dir)]
        with patch("sys.argv", args), redirect_stdout(output), redirect_stderr(errors):
            code = freeze_gate.main()
        self.assertEqual(output.getvalue(), expected + "\n")
        self.assertEqual(errors.getvalue(), "")
        self.assertEqual(code, 0 if expected == "PASS" else 1)

    def test_exactly_50_event_clusters_pass_including_window_end(self):
        self.assert_verdict("PASS")

    def test_same_day_event_does_not_count_toward_50(self):
        self.histories[-1]["first_final_anda"] = "2017-01-01"
        self.write_projection()
        self.assert_verdict("EVENT_FAIL")

    def test_missing_availability_proof_at_12_month_only_cutoff_fails_coverage(self):
        self.editions[-1]["wayback_ts"] = "20180102000000"
        self.write_config()
        self.projection.unlink()
        self.assert_verdict("COVERAGE_FAIL")

    def test_mismatched_edition_digest_fails_coverage(self):
        (self.ob_dir / "2017.zip").write_bytes(b"wrong bytes")
        self.assert_verdict("COVERAGE_FAIL")

    def test_unreadable_edition_is_technical_failure(self):
        (self.ob_dir / "2017.zip").unlink()
        self.assert_verdict("TECHNICAL_FAIL")

    def test_malformed_projection_is_technical_failure(self):
        self.histories.append(self.histories[0])
        self.write_projection()
        self.assert_verdict("TECHNICAL_FAIL")

    def test_truncated_frozen_schedule_is_technical_failure(self):
        self.config["sealed_test"]["schedule"]["12"]["test_cutoffs"].pop()
        self.write_config()
        self.assert_verdict("TECHNICAL_FAIL")
