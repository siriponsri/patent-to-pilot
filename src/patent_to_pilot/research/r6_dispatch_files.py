"""Load frozen dispatch evidence from exact files before live GPU admission.

Hashes prove file identity, not that a PASS receipt is true. The controller must
qualify the underlying evidence and pin this manifest outside worker-writable
storage. Live GPU lock, resources and attempt consumption remain separate gates.
"""
import hashlib
import json
import math
from pathlib import Path

from .mtm_runtime import InputBoundaryError,decode_json
from .r6_admission import REQUIRED_GATES,validate_dispatch,digest


def read_pinned(root,relative,expected,maximum_bytes=8*1024**2):
    if type(relative) is not str or not digest(expected):
        raise InputBoundaryError('dispatch file identity missing')
    part=Path(relative)
    if part.is_absolute() or '..' in part.parts or not part.parts:
        raise InputBoundaryError('dispatch file path outside root')
    root=Path(root).resolve(strict=True)
    path=root/part
    cursor=root
    for component in part.parts:
        cursor=cursor/component
        if cursor.is_symlink():raise InputBoundaryError('dispatch file symlink forbidden')
    if not path.resolve(strict=True).is_relative_to(root):
        raise InputBoundaryError('dispatch file outside root')
    with path.open('rb') as handle:raw=handle.read(maximum_bytes+1)
    if len(raw)>maximum_bytes or hashlib.sha256(raw).hexdigest()!=expected:
        raise InputBoundaryError('dispatch file hash or size mismatch')
    return raw


def load_dispatch(root,*,manifest_path,manifest_sha256):
    manifest=decode_json(read_pinned(root,manifest_path,manifest_sha256))
    roles={'declaration','ledger','scope'}|{'gate:'+name for name in REQUIRED_GATES}
    if (type(manifest) is not dict or set(manifest)!={'version','files'}
            or manifest['version']!='r6-dispatch-files-v1'
            or type(manifest['files']) is not dict or set(manifest['files'])!=roles):
        raise InputBoundaryError('dispatch evidence manifest shape')
    values={};paths=set()
    for role,entry in manifest['files'].items():
        if type(entry) is not dict or set(entry)!={'path','sha256'}:
            raise InputBoundaryError('dispatch manifest entry shape')
        if type(entry['path']) is not str:raise InputBoundaryError('dispatch evidence path type')
        canonical=(Path(root)/entry['path']).resolve(strict=True)
        if canonical in paths:raise InputBoundaryError('dispatch evidence path reused')
        paths.add(canonical)
        values[role]=decode_json(read_pinned(root,entry['path'],entry['sha256']))
        if type(values[role]) is not dict:raise InputBoundaryError('dispatch receipt must be object')
    gates={name:values['gate:'+name] for name in REQUIRED_GATES}
    receipt=validate_dispatch(values['declaration'],values['ledger'],values['scope'],gates)
    return {'declaration':values['declaration'],'ledger':values['ledger'],'scope':values['scope'],
            'gates':gates,'receipt':dict(receipt,evidence_manifest_sha256=manifest_sha256)}


def package_identity(pins):
    return hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def validate_worker_package(root,pins,expected_package_sha256):
    if not digest(expected_package_sha256) or package_identity(pins)!=expected_package_sha256:
        raise InputBoundaryError('qualified package manifest identity mismatch')
    root=Path(root).resolve(strict=True)
    required={p.relative_to(root).as_posix() for p in (root/'src').rglob('*.py')}
    required.update('scripts/healthtech/'+name for name in (
        'run_r6_calibration.py','supervise_r6_calibration.py','inspect_qwen_weight_identity.py',
        'r3_engine_client.py','supervise_r3_engine_v2.py','supervise_sacr_r5_engine.py'))
    required.add('docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json')
    if not (root/'src/patent_to_pilot/research/r6_backend.py').is_file() or not required<=set(pins):
        raise InputBoundaryError('R6 staged source or current entrypoint pins missing')
    for path,expected in pins.items():read_pinned(root,path,expected)


def validate_deadline(stop,now,seconds):
    if (any(type(x) not in (int,float) or not math.isfinite(x) for x in (stop,now,seconds))
            or not 30<stop-now<=seconds or seconds<=0):
        raise InputBoundaryError('worker deadline outside declared remaining stage')
