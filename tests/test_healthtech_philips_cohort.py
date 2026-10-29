from pathlib import Path

import pytest

from scripts.healthtech.fetch_philips_cardiovascular_cohort import (
    PHILIPS_DISCLOSURE_SOURCE_ID,
    PRODUCTS,
    _freeze_groups,
    _validate_product_rows,
    _validate_runtime_separation,
)


def _philips_fixture_html() -> bytes:
    rows = "".join(
        f"<tr><td>{product['label']}</td><td>{'; '.join(product['patent_numbers'])}</td></tr>"
        for product in PRODUCTS
    )
    return f"<html><body><table>{rows}</table></body></html>".encode("utf-8")


def test_philips_rows_validate_exactly_and_preserve_locators():
    rows = _validate_product_rows(_philips_fixture_html())

    assert set(rows) == {str(product["key"]) for product in PRODUCTS}
    assert rows["angiosculpt-scoring-balloon"]["raw_patent_numbers"] == ["7686824"]
    assert "html-table:row=" in rows["turbo-elite-laser-catheter"]["source_locator"]


def test_philips_rows_reject_patent_mutation():
    mutated = _philips_fixture_html().replace(b"8920402", b"9999999")

    with pytest.raises(ValueError, match="unexpected Philips patent row"):
        _validate_product_rows(mutated)


def test_philips_runtime_separation_rejects_disclosure_leak():
    runtime = {
        "devices": [{"source_id": PHILIPS_DISCLOSURE_SOURCE_ID}],
        "patents": [],
        "runtime_exclusions": ["disclosure", "evaluator", "split"],
    }

    with pytest.raises(ValueError, match="leaked"):
        _validate_runtime_separation(runtime)


def test_philips_exact_overlap_forms_shared_group():
    references = {
        "HT-DEV-PHILIPS-A": ["US7686824B2"],
        "HT-DEV-PHILIPS-B": ["US7686824B2", "US8920402B2"],
        "HT-DEV-PHILIPS-C": ["US6440125B2"],
    }
    _, groups, split = _freeze_groups(references, sorted({value for values in references.values() for value in values}))

    assert sorted(groups["shared_exact_patent_groups"]) == [
        ["HT-DEV-PHILIPS-A", "HT-DEV-PHILIPS-B"],
        ["HT-DEV-PHILIPS-C"],
    ]
    assert split["final_holdout"] == []
