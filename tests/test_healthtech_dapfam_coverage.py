import importlib.util
import os
import re
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/healthtech/analyze_dapfam_coverage.py"
SPEC = importlib.util.spec_from_file_location("dapfam_coverage", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_screening_pattern_is_case_insensitive_and_deterministic():
    pattern = MODULE.screening_pattern(("catheter", "medical device"))
    assert pattern == r"(?i)(catheter|medical\ device)"


def test_screening_expression_rejects_unsafe_alias():
    with pytest.raises(ValueError, match="simple SQL identifier"):
        MODULE.screening_expression("c; DROP TABLE", ("catheter",))


def test_sql_literal_escapes_paths_and_quotes():
    assert MODULE.sql_literal(Path("C:\\data\\O'Reilly.parquet")) == "C:/data/O''Reilly.parquet"


def test_screening_sql_keeps_declared_fields_and_policy():
    sql = MODULE.build_screening_sql(Path("corpus.parquet"), "c", "corpus")
    assert "read_parquet('corpus.parquet')" in sql
    assert "title_en" in sql
    assert "abstract_en" in sql
    assert "medical_device_rows" in sql
    assert "pharma_biologics_rows" in sql


def test_qrel_sql_uses_positive_labels_and_keeps_domain_partition():
    sql = MODULE.build_qrel_sql(Path("corpus.parquet"), Path("queries.parquet"), Path("qrels.parquet"))
    assert "WHERE relevance_score > 0" in sql
    assert "domain_rel" in sql
    assert "unjudged" not in sql.lower()


@pytest.mark.parametrize(
    "terms,text,expected",
    [
        (("medical device",), "A MEDICAL DEVICE for screening", True),
        (("delivery system",), "a delivery system", True),
        (("medical device",), "medical/ device", False),
        (("delivery system",), "delivery systems", True),
        (("a+b",), "a+b", True),
        (("a+b",), "aaab", False),
        (("patient's device",), "PATIENT'S DEVICE", True),
        (("medical device",), "medical equipment", False),
    ],
)
def test_sql_screen_preserves_substring_contract(terms, text, expected):
    # Round-trip the SQL literal, then evaluate the emitted regex. This covers
    # the actual expression boundary that the old pattern-only test missed.
    expression = MODULE.screening_expression("c", terms)
    literal = expression.rsplit(", '", 1)[1][:-2]
    pattern = literal.replace("''", "'")
    assert bool(re.search(pattern, text)) is expected


def test_duckdb_screening_expression_matches_real_rows():
    executable = os.environ.get("PTP_TEST_DUCKDB")
    if not executable or not Path(executable).is_file():
        pytest.skip("set PTP_TEST_DUCKDB to run the native SQL integration check")
    expression = MODULE.screening_expression("c", ("medical device", "delivery system", "patient's device", "a+b"))
    result = MODULE.duckdb_json(Path(executable), f"""
        SELECT id, {expression} AS matched FROM (VALUES
            (1, 'A MEDICAL', 'DEVICE for screening'),
            (2, NULL, 'a delivery system'),
            (3, 'patient''s device', NULL),
            (4, 'a+b', ''),
            (5, 'medical/ device', 'aaab'),
            (6, NULL, NULL)
        ) AS c(id, title_en, abstract_en) ORDER BY id
    """)
    assert [row["matched"] for row in result] == [True, True, True, True, False, False]
