"""Freeze + book + stage the Graph query census ONCE (no launch). Inputs are hard-linked, not copied."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap
NAME = 'ptp-auto-graph-extractor-v3-20261112-v1'; OUT = A/'graph-extractor-v3'; OUT.mkdir(exist_ok=False)
Q = JOBS + '/ptp-native-baseline-20261110-v1/runtime-dev/queries-ta.jsonl'
P = JOBS + '/ptp-sg-r4-materialization-20261111-v1/corpus.jsonl'
QS, PS = '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a', '42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d'
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
code = JOBS + '/ptp-auto-graph-census-20261112-v1/code/src'
h = journal(code, "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4]}))\n")
assert h['active'] is None and h['ledger_sha256'] == lsha, h
blobs, pins = package(['supervise_automatic_grammar.py', 'supervise_graph_census.py', 'supervise_graph_extractor_v3.py', 'run_graph_extractor_v3.py'])
package_sha = package_identity(pins)
seg = segment_booking(14, lsha)
mid = copy.deepcopy(ledger); mid['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
b = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': sha((A/'owner-parallel-round2-approval.json').read_bytes()),
     'evidence_sha256': package_sha, 'booking_id': NAME, 'location': 'remote', 'conservative_cpu_seconds': 300,
     'basis': 'upper bound: worker RLIMIT_CPU 270 s + controller 30 s on 1 core, wall stop 290 s; no refund',
     'prior_ledger_sha256': document_hash(mid)}
end = copy.deepcopy(mid); end['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 300
d = {'run_id': NAME, 'kind': 'graph-extractor-v3', 'model_calls': 0, 'gpu_seconds': 0, 'retry': False, 'cpu_seconds': 270,
     'wall_stop_seconds': 290, 'files_sha256': pins, 'package_sha256': package_sha, 'source_commit': git('rev-parse', 'HEAD').decode().strip(),
     'queries_sha256': QS, 'corpus_sha256': PS, 'cpu_booking_sha256': document_hash(b), 'qrels_used': False,
     'protocol': 'docs/healthtech/research/plans/GRAPH-EXTRACTOR-V3-20261112.md'}
raw = json.dumps(d, indent=2).encode() + b'\n'
for n, v in (('segment14-booking.json', seg), ('extractor-booking.json', b)): (OUT/n).write_text(json.dumps(v, indent=2) + '\n')
(OUT/'declaration.json').write_bytes(raw)
out = book(code, [seg, b], h['generation']); assert document_hash(out['ledger']) == document_hash(end); write_ledger(out['ledger'])
files = {'code/' + n: x for n, x in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_graph_extractor_v3.py', 'supervise_graph_census.py', 'supervise_automatic_grammar.py', 'supervise_r3_engine_v2.py', 'r3_engine_client.py')})
files['declaration.json'] = raw
transport = stage(NAME, files)
ssh(f"""import os,hashlib,json
from pathlib import Path
p=Path('{JOBS}/{NAME}')
os.link('{Q}',p/'queries.jsonl');os.link('{P}',p/'corpus.jsonl')
assert hashlib.sha256((p/'queries.jsonl').read_bytes()).hexdigest()=='{QS}' and hashlib.sha256((p/'corpus.jsonl').read_bytes()).hexdigest()=='{PS}'
print('{{}}')
""")
summary = {'jobs': {'census': {'job': NAME, 'supervisor': 'supervise_graph_extractor_v3.py', 'declaration_sha256': sha(raw), 'transport': transport}},
           'generation': h['generation'] + 2, 'ledger_sha256': document_hash(end),
           'cpu_remaining_seconds': cpu_cap(end['r6_phase0_cpu']) - cpu_used(end['r6_phase0_cpu'])}
(OUT/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
