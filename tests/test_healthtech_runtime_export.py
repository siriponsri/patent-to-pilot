import pytest

from scripts.healthtech.export_runtime_text import runtime_rows


def test_runtime_rows_exports_only_task_neutral_identity_and_text():
    rows = list(runtime_rows(
        [
            {"relevant_id": "US000002A1", "title_en": "Valve", "abstract_en": "A device"},
            {"relevant_id": "US000001A1", "title_en": "Pump", "abstract_en": "Another device"},
        ],
        id_column="relevant_id",
        dataset_id="dapfam-corpus",
        source_revision="source-r1",
    ))
    assert rows[0]["item_id"] == "US000002A1"
    assert rows[0]["document_id"] == "US000002A1"
    assert rows[0]["text"] == "Valve A device"
    assert set(rows[0]) == {"item_id", "document_id", "text", "source_id", "source_revision"}


def test_runtime_rows_rejects_missing_text_or_id():
    with pytest.raises(ValueError, match="missing relevant_id"):
        list(runtime_rows(
            [{"relevant_id": "", "title_en": "Valve", "abstract_en": "A device"}],
            id_column="relevant_id",
            dataset_id="fixture",
            source_revision="r1",
        ))
    with pytest.raises(ValueError, match="missing relevant_id"):
        list(runtime_rows(
            [{"relevant_id": "p1", "title_en": "", "abstract_en": ""}],
            id_column="relevant_id",
            dataset_id="fixture",
            source_revision="r1",
        ))
