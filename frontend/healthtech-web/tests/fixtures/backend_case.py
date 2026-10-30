"""Generate an authored fixture through the current Python backend, without network."""
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))
from patent_to_pilot.healthtech.contracts import DossierVersion, RunManifest, AcquisitionEvent, content_hash
from patent_to_pilot.healthtech.engine import DossierInput, run_dossier, serialize_dossier, export_markdown
from patent_to_pilot.healthtech.history import save_version, append_user_edits, source_view

data = DossierInput.model_validate_json((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
dossier, events, manifest = run_dossier(data, run_id="web-backend-contract", code_commit="test")
with tempfile.TemporaryDirectory(prefix="web-backend-contract-") as temp:
    save_version(temp, dossier)
    dossier = append_user_edits(temp, {"review_note": "Backend edit TH/EN: source check needed"}, expected_parent_version=1)
    source_view(dossier, dossier.query.selected_comparator_source_id)
payload = serialize_dossier(dossier)
print(json.dumps({
    "dossier": payload, "hash": content_hash(payload),
    "manifest": manifest.model_dump(mode="json"),
    "events": [e.model_dump(mode="json") for e in events],
    "schemas": {"dossier": DossierVersion.model_json_schema(), "manifest": RunManifest.model_json_schema(), "event": AcquisitionEvent.model_json_schema()},
    "exports": {lang: export_markdown(dossier, language=lang) for lang in ("th", "en")},
}, ensure_ascii=True))
