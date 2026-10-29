from pathlib import Path

import fitz
import pytest

from scripts.healthtech.fetch_cook_zenith_cohort import (
    COOK_DISCLOSURE_SOURCE_ID,
    PRODUCTS,
    _freeze_groups,
    _validate_product_rows,
    _validate_runtime_separation,
)


def _write_pdf(path: Path, *, include_dissection: bool = True) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text(
        (40, 60),
        "Zenith Renu AAA Ancillary Graft Converter\n7,335,224\n"
        "Zenith Flex AAA Endovascular Graft\n7,335,224; 7,294,147",
    )
    page = document.new_page()
    if include_dissection:
        page.insert_text(
            (40, 60),
            "Zenith Dissection Endovascular Stent\n7,993,383; 9,278,017",
        )
    document.save(path)


def test_cook_pdf_rows_validate_and_preserve_locators(tmp_path: Path):
    pdf_path = tmp_path / "cook.pdf"
    _write_pdf(pdf_path)

    rows = _validate_product_rows(pdf_path)

    assert set(rows) == {str(product["key"]) for product in PRODUCTS}
    assert rows["zenith-flex-aaa"]["raw_patent_numbers"] == ["7335224", "7294147"]
    assert rows["zenith-dissection-stent"]["source_locator"] == "pdf-pages:2"


def test_cook_pdf_rows_reject_missing_product(tmp_path: Path):
    pdf_path = tmp_path / "cook.pdf"
    _write_pdf(pdf_path, include_dissection=False)

    with pytest.raises(ValueError, match="Zenith Dissection"):
        _validate_product_rows(pdf_path)


def test_cook_runtime_separation_rejects_disclosure_leak():
    runtime = {
        "devices": [{"source_id": COOK_DISCLOSURE_SOURCE_ID}],
        "patents": [],
        "runtime_exclusions": ["disclosure", "evaluator", "split"],
    }

    with pytest.raises(ValueError, match="leaked"):
        _validate_runtime_separation(runtime)


def test_cook_exact_patent_overlap_forms_group():
    references = {
        "HT-DEV-COOK-ZENITH-FLEX-AAA": ["US7335224B2", "US7294147B2"],
        "HT-DEV-COOK-ZENITH-RENU-CONVERTER": ["US7335224B2"],
        "HT-DEV-COOK-ZENITH-DISSECTION-STENT": ["US7993383B2", "US9278017B2"],
    }
    _, groups, split = _freeze_groups(references, sorted({value for values in references.values() for value in values}))

    assert sorted(groups["shared_exact_patent_groups"]) == [
        ["HT-DEV-COOK-ZENITH-DISSECTION-STENT"],
        ["HT-DEV-COOK-ZENITH-FLEX-AAA", "HT-DEV-COOK-ZENITH-RENU-CONVERTER"],
    ]
    assert split["final_holdout"] == []
