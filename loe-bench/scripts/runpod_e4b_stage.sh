#!/usr/bin/env bash
set -euo pipefail

root=${1:?provide the E4b staging directory on the mounted network volume}
wheel_dir=$(mktemp -d /tmp/loe-e4b-wheels.XXXXXX)
trap 'rm -f -- "$wheel_dir"/*.whl; rmdir -- "$wheel_dir"' EXIT

python "$root/scripts/runpod_e4b_stage.py" "$root/data/E4b_model.json" "$root/model"
python -m pip download --only-binary=:all: --dest "$wheel_dir" "transformers==4.55.2"
python - "$wheel_dir" "$root/dependencies.json" <<'PY'
import email
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

rows = []
for wheel in sorted(Path(sys.argv[1]).glob("*.whl")):
    with ZipFile(wheel) as archive:
        entry = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(entry))
    with wheel.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    rows.append({"wheel": wheel.name, "name": metadata["Name"], "version": metadata["Version"],
                 "license": metadata["License-Expression"] or metadata["License"],
                 "license_classifiers": [c for c in metadata.get_all("Classifier", []) if c.startswith("License ::")],
                 "sha256": digest})
Path(sys.argv[2]).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
PY
python -m pip install --no-index --no-deps --target "$root/deps" "$wheel_dir"/*.whl
PYTHONPATH="$root/deps" python -c 'import torch, transformers; print(torch.__version__, transformers.__version__)'
