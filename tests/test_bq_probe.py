import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "bq_probe", Path(__file__).resolve().parents[1] / "scripts/healthtech/bq_probe.py")
bq = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bq)


def test_parse_accepts_only_allowed_names_and_hides_values():
    config = bq.parse_config("# c\nGOOGLE_CLOUD_PROJECT=demo-project\nGOOGLE_APPLICATION_CREDENTIALS=\n")
    assert config["GOOGLE_CLOUD_PROJECT"] == "demo-project"
    with pytest.raises(bq.ConfigError) as err:
        bq.parse_config("GOOGLE_CLOUD_PROJECT=p\nOPENROUTER_API_KEY=secret-value\n")
    assert "secret-value" not in str(err.value)


def test_parse_rejects_placeholder_missing_project_and_bad_cap():
    for text, code in (("GOOGLE_CLOUD_PROJECT=REPLACE_WITH_YOUR_PROJECT_ID", "CONFIG_PLACEHOLDER"),
                       ("PTP_BQ_MAX_BYTES_BILLED=10", "CONFIG_MISSING_PROJECT"),
                       ("GOOGLE_CLOUD_PROJECT=p\nPTP_BQ_MAX_BYTES_BILLED=ten", "CONFIG_BAD_CAP"),
                       ("GOOGLE_CLOUD_PROJECT=p\nGOOGLE_CLOUD_PROJECT=q", "CONFIG_INVALID_LINE")):
        with pytest.raises(bq.ConfigError) as err:
            bq.parse_config(text)
        assert str(err.value) == code


def test_cap_and_estimate_guard():
    assert bq.effective_cap({"PTP_BQ_MAX_BYTES_BILLED": "1000"}, None) == 1000
    assert bq.effective_cap({}, 500) == 500
    assert bq.effective_cap({"PTP_BQ_MAX_BYTES_BILLED": "1000"}, 5000) == 1000
    bq.check_estimate(900, 1000)
    with pytest.raises(SystemExit):
        bq.check_estimate(1001, 1000)
