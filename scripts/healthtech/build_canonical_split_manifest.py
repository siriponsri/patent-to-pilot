"""Build the canonical split manifest (P1-BridgeRet / P2 / P3) from METADATA only.

Usage (synthetic smoke, no data):
    python scripts/healthtech/build_canonical_split_manifest.py --synthetic OUT_DIR
Usage (real data; needs a recorded owner approval for manifest building):
    python3 -I build_canonical_split_manifest.py --tasks tasks.tsv [--related related.tsv] \
        --build-approval approval.json --release-salt-file salt.txt OUT_DIR

- Reads only app_id / filing_date / art_unit / ipc4_primary from the task table.
- Never reads pairs.tsv, qrels or any label column.
- Writes OUT_DIR/manifest-private.json (raw ids, mode 600 on POSIX) and
  OUT_DIR/manifest-public.json (hashed ids, counts, assertions); never freezes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
for cand in (HERE.parents[2] / 'src', HERE.parent):
    if (cand / 'patent_to_pilot').exists() or (cand / 'canonical_split_manifest.py').exists():
        sys.path.insert(0, str(cand))
try:
    from patent_to_pilot.research import canonical_split_manifest as m
except ImportError:  # flat copy on the remote
    import canonical_split_manifest as m  # type: ignore


def synthetic_tasks() -> list:
    plan = {2006: 40, 2007: 40, 2008: 60, 2009: 60, 2010: 80, 2011: 600, 2012: 400, 2013: 60}
    return [m.TaskMeta(f'S{y}{i:06d}', y, f'AU{i % 11}', 'A61B') for y, n in plan.items() for i in range(n)]


def read_related(path: Path) -> list[tuple[str, str]]:
    import csv
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.DictReader(f, delimiter='\t')
        if not {'app_id', 'related_app_id'} <= set(r.fieldnames or []):
            raise m.ManifestError('related table needs app_id, related_app_id')
        return [(row['app_id'].strip(), row['related_app_id'].strip()) for row in r]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('out_dir', type=Path)
    ap.add_argument('--synthetic', action='store_true')
    ap.add_argument('--tasks', type=Path)
    ap.add_argument('--related', type=Path)
    ap.add_argument('--build-approval', type=Path)
    ap.add_argument('--release-salt-file', type=Path)
    ap.add_argument('--n1', type=int, default=m.DEFAULT_N1)
    ap.add_argument('--val-n', type=int, default=m.DEFAULT_VAL_N)
    a = ap.parse_args(argv)

    code_sha = m.file_sha256(Path(m.__file__))
    inputs: dict[str, str] = {}
    if a.synthetic:
        tasks, links, cfg = synthetic_tasks(), None, m.SplitConfig(n1=100, val_n=20, imbalance_tolerance=0.2)
        salt = 'synthetic-release-salt'
    else:
        if not (a.tasks and a.build_approval and a.release_salt_file):
            ap.error('real data needs --tasks, --build-approval and --release-salt-file')
        appr = json.loads(a.build_approval.read_text(encoding='utf-8'))
        if appr.get('action') != 'build-canonical-split-manifest' or not appr.get('approved_by'):
            raise m.ManifestError('build approval record does not cover manifest building')
        with open(a.tasks, encoding='utf-8', newline='') as f:
            tasks = m.read_task_metadata(f)
        inputs['tasks'] = m.file_sha256(a.tasks)
        links = None
        if a.related:
            links = read_related(a.related)
            inputs['related'] = m.file_sha256(a.related)
        cfg = m.SplitConfig(n1=a.n1, val_n=a.val_n)
        salt = a.release_salt_file.read_text(encoding='utf-8').strip()
        inputs['build_approval'] = m.file_sha256(a.build_approval)
    grouping = m.build_groups([t.app_id for t in tasks], related_links=links)
    man = m.build_manifest(tasks, grouping, cfg, inputs, code_sha, synthetic=a.synthetic)
    a.out_dir.mkdir(parents=True, exist_ok=True)
    priv = a.out_dir / 'manifest-private.json'
    if priv.exists():
        raise m.ManifestError(f'{priv} exists; manifests are never overwritten')
    priv.write_text(json.dumps(man, indent=1, sort_keys=True), encoding='utf-8')
    if os.name == 'posix':
        os.chmod(priv, 0o600)
    pub = m.public_view(man, salt)
    (a.out_dir / 'manifest-public.json').write_text(json.dumps(pub, indent=1, sort_keys=True), encoding='utf-8')
    summary = {k: man[k] for k in ('manifest_sha256', 'block_counts', 'stats', 'notes', 'grouping')}
    summary['assertions'] = {r['id']: r['result'] for r in man['assertions']}
    print(json.dumps(summary, indent=1))
    return 0 if all(r['result'] != 'FAIL' for r in man['assertions']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
