import unittest
from datetime import date
from unittest.mock import patch

from loe_bench import run_baselines, run_profile, seal


class SealTests(unittest.TestCase):
    def test_development_rows_pass_without_consulting_lock(self):
        with patch.object(type(seal.LOCK_PATH), "read_text", side_effect=AssertionError):
            seal.require_rows([{"t": date(2016, 12, 31)}])

    def test_test_boundary_and_later_dates_refused_without_lock(self):
        for cutoff in (seal.TEST_FIRST, date(2020, 1, 1)):
            with self.subTest(cutoff=cutoff), patch.object(
                type(seal.LOCK_PATH), "read_text", side_effect=FileNotFoundError
            ), self.assertRaises(seal.TestSealError):
                seal.require_rows([{"t": date(2016, 1, 1)}, {"t": cutoff}])

    def test_inherited_runners_refuse_before_reading_inputs(self):
        for runner in (run_baselines, run_profile):
            with self.subTest(runner=runner.__name__), patch("sys.argv", [runner.__name__]), patch.object(
                type(seal.LOCK_PATH), "read_text", side_effect=FileNotFoundError
            ), patch.object(runner, "build_entities", side_effect=AssertionError), self.assertRaises(
                seal.TestSealError
            ):
                runner.main()
