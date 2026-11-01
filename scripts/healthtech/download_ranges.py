#!/usr/bin/env python3
"""Download one public file with resumable HTTP range chunks."""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import subprocess
import urllib.request
from pathlib import Path


CHUNK_SIZE = 8 * 1024 * 1024


def resolve_url(url: str) -> str:
    completed = subprocess.run(
        ["curl.exe", "-sS", "-I", "-L", "--max-time", "60", url],
        check=True,
        capture_output=True,
        text=True,
    )
    resolved = url
    for line in completed.stdout.splitlines():
        if line.lower().startswith("location:"):
            resolved = line.split(":", 1)[1].strip()
    return resolved


def fetch_chunk(url: str, start: int, end: int, part: Path) -> tuple[int, int]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "patent-to-pilot/benchmark-expansion",
            "Range": f"bytes={start}-{end}",
        },
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        if response.status != 206:
            raise RuntimeError(f"Range request returned HTTP {response.status}; refusing full-file duplicate")
        data = response.read()
    expected = end - start + 1
    if len(data) != expected:
        raise RuntimeError(f"Chunk {start}-{end} returned {len(data)} bytes, expected {expected}")
    part.write_bytes(data)
    return start, end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bytes", type=int, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    resolved_url = resolve_url(args.url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    parts_dir = args.output.parent / (args.output.name + ".parts")
    parts_dir.mkdir(parents=True, exist_ok=True)
    ranges = []
    start = 0
    while start < args.bytes:
        end = min(args.bytes - 1, start + CHUNK_SIZE - 1)
        ranges.append((start, end))
        start = end + 1

    def submit(item: tuple[int, int]) -> tuple[int, int]:
        start, end = item
        part = parts_dir / f"{start:012d}-{end:012d}.part"
        if part.exists() and part.stat().st_size == end - start + 1:
            return start, end
        return fetch_chunk(resolved_url, start, end, part)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        list(executor.map(submit, ranges))

    temporary = args.output.with_suffix(args.output.suffix + ".range-part")
    with temporary.open("wb") as target:
        for start, end in ranges:
            part = parts_dir / f"{start:012d}-{end:012d}.part"
            data = part.read_bytes()
            if len(data) != end - start + 1:
                raise RuntimeError(f"Stored chunk size mismatch for {part}")
            target.write(data)
    if temporary.stat().st_size != args.bytes:
        raise RuntimeError(f"Merged file has {temporary.stat().st_size} bytes, expected {args.bytes}")
    if args.output.exists():
        args.output.unlink()
    temporary.replace(args.output)
    for part in parts_dir.glob("*.part"):
        part.unlink()
    parts_dir.rmdir()
    print(f"downloaded {args.bytes} bytes to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
