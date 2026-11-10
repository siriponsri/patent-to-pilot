"""One-shot terminal closeout for the fixed never-started continuation, CPU only.

Run only after its supervisor terminal receipt exists. Output stays private;
aggregate-closeout.json contains no query IDs/text. No retries or ledger writes.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

JOB = Path(__file__).resolve().parent
PRIOR = JOB.parent / 'ptp-native-sacr-fidelity-20261110-v1'
OUTPUT = PRIOR / 'out/continuation-a2966f862e87c13f1f1abca8b6b903e7a860f7bff57737759e3c9d8d06da5b91/attempt'


def main():
    if JOB.name != 'ptp-native-sacr-continuation-20261111-v1':
        raise ValueError('fixed remote job required')
    if (JOB/'aggregate-closeout.json').exists() or (JOB/'observed-terminal-state.json').exists():
        raise ValueError('closeout files already exist; inspect rather than replay')
    declaration_raw=(JOB/'declaration.json').read_bytes()
    expected='76dcfb90c69c2eb98410b55ff18c4d0742cb463f09c46fbe2873cea17fc42f01'
    if hashlib.sha256(declaration_raw).hexdigest()!=expected:
        raise ValueError('actual continuation declaration differs')
    declaration=json.loads(declaration_raw)
    manifest_raw=(JOB/'private-plan/continuation.json').read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest()!=declaration['continuation_manifest_sha256']:
        raise ValueError('selection manifest differs')
    manifest=json.loads(manifest_raw)
    if manifest['selected_indices']!=list(range(46,100)) or manifest['blocked_indices']!=[45]:
        raise ValueError('fixed selection differs')
    state=json.loads(subprocess.run(['docker','inspect',JOB.name],check=True,capture_output=True,text=True,timeout=10).stdout)[0]['State']
    sys.path.insert(0,str(JOB/'runtime-code/src'))
    spec=importlib.util.spec_from_file_location('selected_closeout',JOB/'summarize-selected-reviewed.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    result=helper.summarize(JOB,state,output_root=OUTPUT,selected_indices=manifest['selected_indices'],expected_declaration_sha256=expected)
    result['selection_manifest_sha256']=declaration['continuation_manifest_sha256']
    result['closeout_helper_sha256']=hashlib.sha256((JOB/'summarize-selected-reviewed.py').read_bytes()).hexdigest()
    result['finalizer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for name,value in [('observed-terminal-state.json',state),('aggregate-closeout.json',result)]:
        with (JOB/name).open('x') as f:json.dump(value,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__':main()
