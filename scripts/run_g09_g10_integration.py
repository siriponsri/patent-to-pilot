"""Run the bounded offline G09/G10 integration slice."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.integration.pipeline import IntegrationPipeline  # noqa: E402

if __name__ == "__main__":
    output = ROOT / "results" / "development" / "g09-g10"
    report = IntegrationPipeline().run_all()
    IntegrationPipeline.write_reports(report, output)
    print(f"wrote {output / 'integration.json'}")
    print(f"wrote {output / 'integration.md'}")
    print(f"wrote {output / 'integration.html'}")
    print(f"cases={report['metrics']['case_count']} states={report['metrics']['state_count']} elapsed={report['metrics']['elapsed_seconds']:.6f}s")
