"""Run a caller-supplied bounded offline G09/G10 workflow sequence."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.integration.pipeline import IntegrationPipeline, WorkflowInput  # noqa: E402


if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "configs" / "g09-g10-example-input.json"
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "results" / "development" / "g09-g10-new-input"
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    workflows = [WorkflowInput.model_validate(item) for item in payload["states"]]
    started = time.perf_counter()
    report = IntegrationPipeline().run_workflow_sequence(workflows)
    elapsed = time.perf_counter() - started
    IntegrationPipeline.write_workflow_reports(report, output_dir, elapsed)
    print(f"input={input_path}")
    print(f"output={output_dir}")
    print(f"states={len(report['states'])} changes={len(report['changes'])} elapsed={elapsed:.6f}s")
