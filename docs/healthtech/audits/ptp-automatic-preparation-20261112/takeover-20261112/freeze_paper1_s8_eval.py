"""Paper 1 S8: freeze + book + stage the SINGLE CPU-only test evaluation ONCE (no launch). Derived from freeze_paper1_s5_eval.py.

This is where the sealed test qrels are opened: they are copied from the local private staging folder to the remote
job ONCE (hash checked against the test evaluator manifest pinned in the test freeze manifest). Requires the S8 test
retrieval settled with C1 = MOVEMENT_PRESENT for all three arms. Evaluator kind paper1-test-eval adds the frozen
confirmatory gatekeeping (paper1_dev_eval.confirmatory). No model/GPU. Run once; never rerun.
"""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
NAME = 'ptp-auto-paper1-test-eval-20261115-v1'; OUT = A/'paper1-s8-eval'; OUT.mkdir(exist_ok=False)
from test_configs import TEST_INPUT, TEST_SHA
import subprocess
PRIV = R.parent/'_private_artifacts/healthtech/ptp-dapfam-native-test-20261115-v1'
TF = json.loads((A/'paper1-freeze/test-freeze-manifest.json').read_bytes())['test_inputs']
EM = (PRIV/'test-evaluation/manifest.json').read_bytes(); assert sha(EM) == TF['evaluator_manifest_sha256']
QRELS_SHA = json.loads(EM)['files']['qrels-test.jsonl']
INPUTS = JOBS + '/ptp-paper1-test-inputs-20261115-v1'
RET = JOBS + '/ptp-auto-paper1-all-test-retrieval-20261115-v1/out/attempt/'
completion = json.loads((A/'paper1-s8-retrieval/terminal-observation.json').read_bytes())['completion']
assert completion['status'] == 'PAPER1_RANKINGS_COMPLETE_NOT_EVALUATED' and completion['labels_used'] is False
c1 = {a: completion['c1_manipulation_and_truncation'][a]['verdict'] for a in ('FA', 'GR', 'SACR')}
assert all(v == 'MOVEMENT_PRESENT' for v in c1.values()), c1
f = completion['files_sha256']
SRC = {'corpus.jsonl': (JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/corpus.jsonl', '42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d'),
       'queries.jsonl': (TEST_INPUT, TEST_SHA),
       'qrels.jsonl': (INPUTS + '/qrels-test.jsonl', QRELS_SHA),
       'reference.jsonl': (RET + 'reference-top200-private.jsonl', f['reference-top200-private.jsonl']),
       'shuffle.jsonl': (RET + 'shuffle-top200-private.jsonl', f['shuffle-top200-private.jsonl']),
       **{a + '-panel.jsonl': (RET + a + '-panel-top200-private.jsonl', f[a + '-panel-top200-private.jsonl']) for a in ('FA', 'GR', 'SACR')},
       'retrieval-completion.json': (RET + 'completion.json', None)}
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', p.name).group(1)) for p in A.rglob('segment*-booking.json'))
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
code = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
h = journal(code, "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':json.loads(h[3])['automatic_study']['status']}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha and h['status'] == 'IDLE', h
SRC['retrieval-completion.json'] = (RET + 'completion.json', ssh(
    "import hashlib,json\nprint(json.dumps(hashlib.sha256(open('" + RET + "completion.json','rb').read()).hexdigest()))\n"))
blobs, pins = package(['supervise_automatic_grammar.py', 'supervise_graph_census.py', 'supervise_paper1_dev_eval.py', 'run_paper1_dev_eval.py'])
package_sha = package_identity(pins)
seg = segment_booking(SEG, lsha)
mid = copy.deepcopy(ledger); mid['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
b = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': sha((A/'owner-paper1-freeze-approval.json').read_bytes()),
     'evidence_sha256': package_sha, 'booking_id': NAME, 'location': 'remote', 'conservative_cpu_seconds': 660,
     'basis': 'upper bound: worker RLIMIT_CPU 600 s + controller 60 s on 1 core, wall stop 640 s; no refund (S8 test evaluation)',
     'prior_ledger_sha256': document_hash(mid)}
end = copy.deepcopy(mid); end['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 660
assert cpu_used(end['r6_phase0_cpu']) <= cpu_cap(end['r6_phase0_cpu'])
d = {'run_id': NAME, 'kind': 'paper1-test-eval', 'model_calls': 0, 'gpu_seconds': 0, 'retry': False, 'cpu_seconds': 600,
     'wall_stop_seconds': 640, 'files_sha256': pins, 'package_sha256': package_sha, 'source_commit': git('rev-parse', 'HEAD').decode().strip(),
     'inputs_sha256': {k: v[1] for k, v in SRC.items()}, 'cpu_booking_sha256': document_hash(b), 'qrels_used': 'test (opened once, here)', 'test_freeze_manifest_sha256': sha((A/'paper1-freeze/test-freeze-manifest.json').read_bytes()),
     'c1_verdicts': c1, 'protocol': 'docs/healthtech/research/plans/PAPER1-ACQUISITION-PROTOCOL-DRAFT-20261113.md (frozen) sections 5-6 + A1'}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('segment%d-booking.json' % SEG, seg), ('eval-booking.json', b)): (OUT/n).write_text(json.dumps(v, indent=2) + '\n')
(OUT/'declaration.json').write_bytes(raw)
out = book(code, [seg, b], h['generation']); assert document_hash(out['ledger']) == document_hash(end); write_ledger(out['ledger'])
files = {'code/' + n: x for n, x in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_dev_eval.py', 'supervise_graph_census.py', 'supervise_automatic_grammar.py', 'supervise_r3_engine_v2.py', 'r3_engine_client.py')})
files['declaration.json'] = raw
transport = stage(NAME, files)
# Open the sealed test qrels ONCE: copy to the remote input folder (read-only), verify the pinned hash.
assert sha((PRIV/'test-evaluation/qrels-test.jsonl').read_bytes()) == QRELS_SHA
subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', str(PRIV/'test-evaluation/qrels-test.jsonl'), HOST + ':' + INPUTS + '/qrels-test.jsonl'], check=True, timeout=300)
assert ssh("import hashlib,os,json\np='" + INPUTS + "/qrels-test.jsonl'\nos.chmod(p,0o444)\n"
           "print(json.dumps(hashlib.sha256(open(p,'rb').read()).hexdigest()))\n") == QRELS_SHA
ssh("import os,hashlib,json\nfrom pathlib import Path\np=Path('" + JOBS + "/" + NAME + "')\nsrc=json.loads(" + repr(json.dumps(SRC)) + ")\n"
    "for n,(path,h) in src.items():\n os.link(path,p/n)\n assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n\nprint('{}')\n")
summary = {'job': NAME, 'supervisor': 'supervise_paper1_dev_eval.py', 'declaration_sha256': sha(raw), 'transport': transport,
           'generation': h['generation'] + 2, 'ledger_sha256': document_hash(end), 'segment': SEG,
           'cpu_remaining_seconds': cpu_cap(end['r6_phase0_cpu']) - cpu_used(end['r6_phase0_cpu'])}
(OUT/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
