"""Serve the local HealthTech dossier engine over loopback HTTP."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.healthtech.http import create_server  # noqa: E402


def _head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--data-dir", type=Path, default=ROOT / ".local" / "healthtech-http")
    parser.add_argument("--code-commit", default=None)
    parser.add_argument("--delay-ms", type=int, default=0, help="test-only delay before local execution")
    parser.add_argument(
        "--vector-config",
        type=Path,
        default=None,
        help="server-owned JSON config for a validated vector corpus/query bundle pair",
    )
    args = parser.parse_args()
    if args.delay_ms < 0:
        parser.error("--delay-ms must be non-negative")
    server = create_server(
        args.host,
        args.port,
        args.data_dir,
        code_commit=args.code_commit or _head(),
        execution_delay_seconds=args.delay_ms / 1000,
        vector_config=args.vector_config,
    )
    bound_host, bound_port = server.server_address[:2]
    print(f"healthtech local HTTP listening on http://{bound_host}:{bound_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.healthtech_service.close()


if __name__ == "__main__":
    main()

