#!/usr/bin/env python3
"""Pull patent-to-pilot result artifacts from dr-train and verify them by SHA256.

Repeatable after every phase. It only READS on the remote side (find, tar,
sha256sum). It never deletes anything; deletion is a separate, manual step that
must cite the verified manifest written here (see docs/maintenance/
DR-TRAIN-ARTIFACT-RUNBOOK.md).

What it copies: every readable regular file under the given remote roots that
is not excluded and is no larger than --max-file-mb. Larger files (run TSVs,
vectors, checkpoints, raw data) are listed in large-files.tsv and are NOT
copied, so the operator can decide with the owner.

Hard exclusions (never copied, never read beyond `find` metadata):
sealed / protected TEST material, model weights, virtualenvs, caches and the
raw public datasets that stay on dr-train.

Outputs in --dest:
  files/<remote absolute path>   copied files
  pull-manifest.tsv              path, size, remote sha256, local sha256, status
  large-files.tsv                files skipped for size (path, size)
  excluded-summary.json          counts and bytes per exclusion rule
  pull-summary.json              aggregate totals (safe to commit)

Usage (from the repo root, Windows or POSIX):
  python scripts/maintenance/pull_dr_train_artifacts.py \
      --dest ../_private_artifacts/dr-train-archive/20261121 \
      --root /data/ptp-paper2 --root /home/chaw/patent-to-pilot-jobs \
      --exclude-path /data/ptp-paper2/b53       # e.g. while a job still writes
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath

DEFAULT_HOST = "chaw@100.77.149.83"
DEFAULT_ROOTS = ["/data/ptp-paper2", "/home/chaw/patent-to-pilot-jobs"]

# (rule name, regex on the remote absolute path). Order matters: first match wins.
HARD_EXCLUDES: list[tuple[str, str]] = [
    ("sealed_or_protected_test", r"(^|/)sealed(/|$)|(^|/)pairs\.tsv$|qrels[^/]*test|"
                                 r"(^|/)test-evaluation(/|$)|-test-|(^|/)test(/|$)|"
                                 r"(^|/)splits/private(/|$)|test-eval|test-retrieval"),
    ("model_weights", r"(^|/)models?(/|$)|\.safetensors$|(^|/)ckpt-fp16(/|$)|(^|/)checkpoint(/|$)|"
                      r"(^|/)base-shadow(/|$)"),
    ("venv_or_cache", r"(^|/)(venv|\.venv|\.cache|__pycache__|site-packages|node_modules)(/|$)"),
    ("raw_public_dataset", r"^/data/ptp-paper2/(patentsview|oa2017|panorama|beir)(/|$)"),
]


def ssh_cmd(host: str, remote: str) -> list[str]:
    return ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20", host, remote]


def remote_list(host: str, roots: list[str]) -> list[tuple[str, int]]:
    quoted = " ".join("'" + r.replace("'", "") + "'" for r in roots)
    remote = f"find {quoted} -type f -readable -printf '%s\\t%p\\0' 2>/dev/null; true"
    out = subprocess.run(ssh_cmd(host, remote), capture_output=True, check=True).stdout
    items = []
    for rec in out.split(b"\0"):
        if not rec:
            continue
        size, path = rec.decode("utf-8", "surrogateescape").split("\t", 1)
        items.append((path, int(size)))
    return items


def classify(path: str, size: int, max_bytes: int, extra_excl: list[str]) -> str:
    for p in extra_excl:
        p = p.rstrip("/")
        if path == p or path.startswith(p + "/"):
            return "operator_excluded"
    for name, rx in HARD_EXCLUDES:
        if re.search(rx, path):
            return name
    if size > max_bytes:
        return "large"
    return "copy"


def local_target(dest: Path, remote_path: str) -> Path:
    rel = PurePosixPath(remote_path).relative_to("/")
    # Windows-invalid characters are replaced; the manifest keeps the original path.
    safe = [re.sub(r'[<>:"\\|?*]', "_", part) for part in rel.parts]
    p = dest.joinpath("files", *safe)
    if os.name == "nt":  # extended-length prefix: deep repo copies exceed MAX_PATH (260)
        s = str(p)
        if not s.startswith("\\\\?\\"):
            p = Path("\\\\?\\" + s)
    return p


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def remote_hashes(host: str, paths: list[str]) -> dict[str, str]:
    payload = b"\0".join(p.encode("utf-8", "surrogateescape") for p in paths) + b"\0"
    proc = subprocess.run(ssh_cmd(host, "xargs -0 -r sha256sum --"), input=payload,
                          capture_output=True, check=False)
    hashes = {}
    for line in proc.stdout.decode("utf-8", "surrogateescape").splitlines():
        if len(line) > 66 and line[64:66] == "  ":
            hashes[line[66:]] = line[:64]
    return hashes


def copy_batch(host: str, dest: Path, paths: list[str]) -> dict[str, str]:
    """Stream a remote tar of `paths` and extract member by member. Returns errors."""
    payload = b"\0".join(p.encode("utf-8", "surrogateescape") for p in paths) + b"\0"
    remote = "tar --null -T - -cf - --absolute-names --ignore-failed-read 2>/dev/null"
    proc = subprocess.Popen(ssh_cmd(host, remote), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    assert proc.stdin and proc.stdout
    proc.stdin.write(payload)
    proc.stdin.close()
    errors: dict[str, str] = {}
    with tarfile.open(fileobj=proc.stdout, mode="r|") as tf:
        for m in tf:
            name = "/" + m.name.lstrip("/")
            if not m.isfile():
                continue
            target = local_target(dest, name)
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tf.extractfile(m)
                assert src is not None
                tmp = target.with_name(target.name + ".part")
                with open(tmp, "wb") as out:
                    while True:
                        buf = src.read(1 << 20)
                        if not buf:
                            break
                        out.write(buf)
                os.replace(tmp, target)
            except Exception as exc:  # record, never abort the whole pull
                errors[name] = f"{type(exc).__name__}: {exc}"
    # Drain tar's trailing record padding; otherwise ssh can block on a full pipe
    # and proc.wait() deadlocks (seen on Windows, 21 Nov 2026).
    while proc.stdout.read(1 << 16):
        pass
    try:
        proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--root", action="append", dest="roots")
    ap.add_argument("--dest", required=True)
    ap.add_argument("--max-file-mb", type=float, default=50.0)
    ap.add_argument("--exclude-path", action="append", default=[],
                    help="remote path prefix to skip this time (e.g. a running job)")
    ap.add_argument("--min-free-gb", type=float, default=100.0,
                    help="refuse if local free space would drop below this")
    ap.add_argument("--batch", type=int, default=2000)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    roots = args.roots or DEFAULT_ROOTS
    for p in roots + args.exclude_path:
        if not p.startswith("/"):
            # Git Bash rewrites "/data/..." into "C:/Program Files/Git/data/..." (MSYS path conversion).
            ap.error(f"remote path {p!r} is not POSIX-absolute; under Git Bash run with MSYS_NO_PATHCONV=1")
    dest = Path(args.dest).resolve()
    max_bytes = int(args.max_file_mb * 1024 * 1024)

    t0 = time.time()
    items = remote_list(args.host, roots)
    buckets: dict[str, list[tuple[str, int]]] = {}
    for path, size in items:
        buckets.setdefault(classify(path, size, max_bytes, args.exclude_path), []).append((path, size))
    to_copy = buckets.get("copy", [])
    copy_bytes = sum(s for _, s in to_copy)

    dest.mkdir(parents=True, exist_ok=True)
    free = __import__("shutil").disk_usage(dest).free
    excluded = {k: {"files": len(v), "bytes": sum(s for _, s in v)} for k, v in buckets.items()}
    (dest / "excluded-summary.json").write_text(json.dumps(excluded, indent=2), encoding="utf-8")
    with open(dest / "large-files.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("remote_path\tbytes\n")
        for p, s in sorted(buckets.get("large", []), key=lambda x: -x[1]):
            f.write(f"{p}\t{s}\n")
    print(json.dumps({"listed": len(items), "to_copy_files": len(to_copy), "to_copy_bytes": copy_bytes,
                      "local_free_bytes": free, "buckets": excluded}, indent=2))
    if free - copy_bytes < args.min_free_gb * 1024**3 and copy_bytes > 0:
        # Small result files are always allowed; the margin rule targets big payloads.
        if copy_bytes > 5 * 1024**3:
            print("REFUSED: copy would breach the free-space margin", file=sys.stderr)
            return 2
    if args.dry_run:
        return 0

    paths = [p for p, _ in to_copy]
    sizes = dict(to_copy)
    errors: dict[str, str] = {}
    rhash: dict[str, str] = {}
    for i in range(0, len(paths), args.batch):
        batch = paths[i:i + args.batch]
        # Resume: skip files already present with the same size (they are still hash-verified below).
        need = [p for p in batch
                if not (local_target(dest, p).exists() and local_target(dest, p).stat().st_size == sizes[p])]
        if need:
            errors.update(copy_batch(args.host, dest, need))
        rhash.update(remote_hashes(args.host, batch))
        print(f"copied {min(i + args.batch, len(paths))}/{len(paths)}", flush=True)

    ok = bad = missing = 0
    with open(dest / "pull-manifest.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("remote_path\tbytes\tremote_sha256\tlocal_sha256\tstatus\n")
        for p in paths:
            t = local_target(dest, p)
            r = rhash.get(p, "")
            if not t.exists():
                status, lh = ("COPY_ERROR:" + errors.get(p, "missing")), ""
                missing += 1
            else:
                lh = sha256_file(t)
                if r and lh == r and t.stat().st_size == sizes[p]:
                    status = "OK"
                    ok += 1
                else:
                    status = "MISMATCH"  # e.g. file changed while copying
                    bad += 1
            f.write(f"{p}\t{sizes[p]}\t{r}\t{lh}\t{status}\n")
    summary = {
        "host": args.host, "roots": roots, "max_file_mb": args.max_file_mb,
        "operator_excluded": args.exclude_path, "files_listed": len(items),
        "copied_ok": ok, "mismatch": bad, "copy_error": missing, "copied_bytes": copy_bytes,
        "large_not_copied": excluded.get("large", {}), "excluded": excluded,
        "elapsed_s": round(time.time() - t0, 1),
        "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    (dest / "pull-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if bad == 0 and missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
