"""Freeze + book + stage the Graph query census ONCE (no launch). Inputs are hard-linked, not copied."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
NAME = 'ptp-auto-sacr-pilot-eval-20261113-v1'; OUT = A/'sacr-pilot-eval'; OUT.mkdir(exist_ok=False)
SRC = {'corpus.jsonl': (JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/corpus.jsonl', '42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d'),
       'queries.jsonl': (JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl', '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a'),
       'qrels.jsonl': (JOBS + '/ptp-native-evaluator-20261110-v2/dev-evaluation/qrels-dev.jsonl', 'ca693dc8a1d5c5bf10249c8e9438be5198346349dcd1b6a6194e0eeb96923473'),
       'panel.jsonl': (JOBS + '/ptp-auto-sacr-pilot-retrieval-20261113-v1/out/attempt/panel-top200-private.jsonl', 'fa1f00db103a2bf12888b757b91251dde181a5221be7fff3713cc7cbb96d852b'),
       'reference.jsonl': (JOBS + '/ptp-auto-sacr-pilot-retrieval-20261113-v1/out/attempt/reference-top200-private.jsonl', 'dd766682bca7c1159f05ec1ebbeffe258158e49db21bc23c7e58b922bbae4c1e')}
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
code = JOBS + '/ptp-auto-sacr-pilot-retrieval-20261113-v1/code/src'
h = journal(code, "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4]}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha, h
blobs, pins = package(['supervise_automatic_grammar.py', 'supervise_graph_census.py', 'supervise_sacr_pilot_eval.py', 'run_sacr_pilot_eval.py'])
package_sha = package_identity(pins)
seg = segment_booking(27, lsha)
mid = copy.deepcopy(ledger); mid['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
b = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': sha((A/'owner-parallel-round2-approval.json').read_bytes()),
     'evidence_sha256': package_sha, 'booking_id': NAME, 'location': 'remote', 'conservative_cpu_seconds': 120,
     'basis': 'upper bound: worker RLIMIT_CPU 90 s + controller 30 s on 1 core, wall stop 110 s; no refund',
     'prior_ledger_sha256': document_hash(mid)}
end = copy.deepcopy(mid); end['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 120
d = {'run_id': NAME, 'kind': 'sacr-pilot-eval', 'model_calls': 0, 'gpu_seconds': 0, 'retry': False, 'cpu_seconds': 90,
     'wall_stop_seconds': 110, 'files_sha256': pins, 'package_sha256': package_sha, 'source_commit': git('rev-parse', 'HEAD').decode().strip(),
     **{k.replace('.jsonl', '_sha256'): v[1] for k, v in SRC.items()}, 'cpu_booking_sha256': document_hash(b), 'qrels_used': 'dev only',
     'protocol': 'docs/healthtech/research/plans/NATIVE-STAGES-20261112.md'}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('segment27-booking.json', seg), ('eval-booking.json', b)): (OUT/n).write_text(json.dumps(v, indent=2) + '\n')
(OUT/'declaration.json').write_bytes(raw)
out = book(code, [seg, b], h['generation']); assert document_hash(out['ledger']) == document_hash(end); write_ledger(out['ledger'])
files = {'code/' + n: x for n, x in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_sacr_pilot_eval.py', 'supervise_graph_census.py', 'supervise_automatic_grammar.py', 'supervise_r3_engine_v2.py', 'r3_engine_client.py')})
files['declaration.json'] = raw
transport = stage(NAME, files)
ssh("import os,hashlib,json\nfrom pathlib import Path\np=Path('" + JOBS + "/" + NAME + "')\nsrc=json.loads(" + repr(json.dumps(SRC)) + ")\n"
    "for n,(path,h) in src.items():\n os.link(path,p/n)\n assert hashlib.sha256((p/n).read_bytes()).hexdigest()==h,n\nprint('{}')\n")
summary = {'jobs': {'census': {'job': NAME, 'supervisor': 'supervise_sacr_pilot_eval.py', 'declaration_sha256': sha(raw), 'transport': transport}},
           'generation': h['generation'] + 2, 'ledger_sha256': document_hash(end),
           'cpu_remaining_seconds': cpu_cap(end['r6_phase0_cpu']) - cpu_used(end['r6_phase0_cpu'])}
(OUT/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
