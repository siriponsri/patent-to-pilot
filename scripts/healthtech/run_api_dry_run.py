"""Validate and execute a HealthTech dry-run request without network access."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.api import HealthTechAPIConfig, HealthTechRequest, dispatch_healthtech_request


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_bundle", type=Path, help="JSON object with config and request")
    args = parser.parse_args()
    bundle = json.loads(args.request_bundle.read_text(encoding="utf-8"))
    config = HealthTechAPIConfig.model_validate(bundle.get("config", {}))
    request = HealthTechRequest.model_validate(bundle["request"])
    receipt = dispatch_healthtech_request(config, request)
    print(receipt.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
