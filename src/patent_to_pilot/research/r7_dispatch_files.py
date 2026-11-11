"""R7 bindings on top of the unchanged historical dispatch file contract."""
from .r6_dispatch_files import (load_dispatch as load_r6_dispatch,
    validate_worker_package as validate_r6_package, read_pinned, validate_deadline, package_identity)
from .r6_dispatch_journal import document_hash
from .r7_dispatch_journal import R7DispatchJournal
from .mtm_runtime import InputBoundaryError


def load_dispatch(root, *, manifest_path, manifest_sha256):
    result=load_r6_dispatch(root,manifest_path=manifest_path,manifest_sha256=manifest_sha256)
    d=result['declaration'];s=result['scope']
    R7DispatchJournal._r7_bounds(d,result['ledger'],s,result['gates'])
    if d['stage']!='calibration' or document_hash(d)!=s['r7_authority']['declaration_sha256']:
        raise InputBoundaryError('R7 exact calibration declaration required')
    result['receipt']['candidate_authority_sha256']=s['r7_authority_sha256']
    return result


def validate_worker_package(root,pins,expected_package_sha256):
    validate_r6_package(root,pins,expected_package_sha256)
    for name in ('run_r7_calibration.py','supervise_r7_calibration.py'):
        path='scripts/healthtech/'+name
        if path not in pins:raise InputBoundaryError('R7 entrypoint pin missing')
        read_pinned(root,path,pins[path])
