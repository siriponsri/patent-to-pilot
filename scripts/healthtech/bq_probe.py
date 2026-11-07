"""Guarded BigQuery runner for the medtech time-machine data plan (owner-run credentials, never printed).

Subcommands:
  dry-run  estimate the bytes a SQL file would process (free; no data returned)
  run      dry-run first; refuse if the estimate exceeds the cap; then run with maximum_bytes_billed = cap,
           write rows to a private CSV and a receipt (SQL hash, job id, bytes, rows, timing). Refuses to overwrite.

Credentials come from an explicit key file (default .env.bigquery, git-ignored) with only these names:
GOOGLE_CLOUD_PROJECT, GOOGLE_APPLICATION_CREDENTIALS (path to a service-account JSON kept outside the repo; empty means
gcloud application-default login), PTP_BQ_MAX_BYTES_BILLED (per-query cap, bytes). Values are never printed or logged.
Plan: docs/healthtech/research/MEDTECH_TIME_MACHINE_DATA_PLAN_DRAFT_20261107_EN.md.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = ("GOOGLE_CLOUD_PROJECT", "GOOGLE_APPLICATION_CREDENTIALS", "PTP_BQ_MAX_BYTES_BILLED")
PLACEHOLDER_PREFIX = "REPLACE_WITH"
DEFAULT_CAP = 100 * 1024 ** 3  # 100 GiB per query unless the key file sets a lower or higher cap
MAX_FILE_BYTES = 4096


class ConfigError(ValueError):
    """Carries a code only; never a value, line or path."""


def parse_config(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.removeprefix("﻿").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if not sep or name not in ALLOWED or name in values:
            raise ConfigError("CONFIG_INVALID_LINE")
        if value.startswith(PLACEHOLDER_PREFIX):
            raise ConfigError("CONFIG_PLACEHOLDER")
        values[name] = value
    if not values.get("GOOGLE_CLOUD_PROJECT"):
        raise ConfigError("CONFIG_MISSING_PROJECT")
    cap = values.get("PTP_BQ_MAX_BYTES_BILLED")
    if cap is not None and (not cap.isdigit() or int(cap) <= 0):
        raise ConfigError("CONFIG_BAD_CAP")
    return values


def load_config(path: Path) -> dict[str, str]:
    try:
        raw = path.read_bytes()
    except OSError:
        raise ConfigError("CONFIG_UNREADABLE") from None
    if len(raw) > MAX_FILE_BYTES:
        raise ConfigError("CONFIG_TOO_LARGE")
    return parse_config(raw.decode("utf-8-sig"))


def effective_cap(config: dict[str, str], requested: int | None) -> int:
    cap = int(config.get("PTP_BQ_MAX_BYTES_BILLED") or DEFAULT_CAP)
    return min(cap, requested) if requested else cap


def check_estimate(estimate: int, cap: int) -> None:
    if estimate > cap:
        raise SystemExit(f"refused: estimate {estimate / 1024 ** 3:.1f} GiB exceeds cap {cap / 1024 ** 3:.1f} GiB")


def _client(config: dict[str, str]):
    from google.cloud import bigquery

    credentials_path = config.get("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        return bigquery.Client(project=config["GOOGLE_CLOUD_PROJECT"], credentials=credentials), bigquery
    return bigquery.Client(project=config["GOOGLE_CLOUD_PROJECT"]), bigquery


def _dry_run(client, bigquery, sql: str) -> int:
    job = client.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    return int(job.total_bytes_processed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("dry-run", "run"))
    parser.add_argument("--sql-file", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / ".env.bigquery")
    parser.add_argument("--max-gib", type=float, help="lower per-query cap for this call")
    parser.add_argument("--output", type=Path, help="private CSV path (run only)")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        raise SystemExit(f"config error: {exc}") from None
    sql = args.sql_file.read_text(encoding="utf-8")
    sql_sha = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    cap = effective_cap(config, int(args.max_gib * 1024 ** 3) if args.max_gib else None)
    client, bigquery = _client(config)
    estimate = _dry_run(client, bigquery, sql)
    summary = {"sql_file": args.sql_file.name, "sql_sha256": sql_sha, "estimate_bytes": estimate,
               "estimate_gib": round(estimate / 1024 ** 3, 3), "cap_gib": round(cap / 1024 ** 3, 3)}
    if args.command == "dry-run":
        print(json.dumps(summary, indent=1))
        return 0
    if not args.output:
        raise SystemExit("run needs --output")
    receipt_path = Path(str(args.output) + ".receipt.json")
    if args.output.exists() or receipt_path.exists():
        raise SystemExit("output exists: refusing to overwrite")
    check_estimate(estimate, cap)
    started = time.perf_counter()
    job = client.query(sql, job_config=bigquery.QueryJobConfig(maximum_bytes_billed=cap, use_query_cache=True))
    rows = job.result()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([field.name for field in rows.schema])
        for row in rows:
            writer.writerow([json.dumps(v) if isinstance(v, (list, dict)) else v for v in row.values()])
            count += 1
    receipt = {**summary, "status": "PASS", "job_id": job.job_id, "location": job.location,
               "bytes_processed": job.total_bytes_processed, "bytes_billed": job.total_bytes_billed,
               "cache_hit": job.cache_hit, "rows": count, "seconds": round(time.perf_counter() - started, 3),
               "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "rows", "bytes_processed", "bytes_billed", "cache_hit", "seconds")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
