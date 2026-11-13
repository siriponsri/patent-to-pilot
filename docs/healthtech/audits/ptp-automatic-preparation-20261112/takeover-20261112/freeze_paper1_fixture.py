"""Paper 1: freeze + book + stage the FA/GR rewrite-worker CPU fixture ONCE (no launch).
Bookings: segment 30 (local metered + 100 s) + 120 s remote upper bound (no refund), from the live generation."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

NAME = 'ptp-auto-paper1-rewrite-fixture-20261113-v1'
CODE = JOBS + '/ptp-auto-native-sacr-fulldev-b1-20261113-v1/code/src'
OUT = A/'paper1-fixture'; OUT.mkdir(exist_ok=False)
ledger = json.loads(L.read_bytes()); ledger_sha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':json.loads(h[3])['automatic_study']['status']}))\n")
assert h['active'] is None and h['ledger_sha256'] == ledger_sha and h['status'] == 'IDLE', h
gen = h['generation']
blobs, pins = package(['supervise_automatic_grammar.py', 'supervise_paper1_rewrite_fixture.py', 'qualify_paper1_rewrite_pipeline.py', 'run_paper1_rewrite.py'])
package_sha = package_identity(pins)
remote_tok = ssh("import hashlib,json\nfrom pathlib import Path\nm=Path('" + JOBS + "/research-product-o1-o4-20261031/models/qwen3-8b')\n"
                 "print(json.dumps({n:hashlib.sha256((m/n).read_bytes()).hexdigest() for n in ('tokenizer.json','tokenizer_config.json','config.json','vocab.json','merges.txt','generation_config.json')}))\n")
assert remote_tok['tokenizer.json'] == 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4'
freeze = json.loads((A/'paper1-freeze/freeze-manifest.json').read_bytes())
for f in ('src/patent_to_pilot/research/paper1_rewrite_arms.py', 'src/patent_to_pilot/research/r6_backend.py'):
    assert pins[f] == freeze['files_sha256'][f], 'frozen file changed: ' + f
authority = sha((A/'owner-paper1-freeze-approval.json').read_bytes())
seg = segment_booking(30, ledger_sha)
expected = copy.deepcopy(ledger); expected['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
b = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': authority, 'evidence_sha256': package_sha,
     'booking_id': NAME, 'location': 'remote', 'conservative_cpu_seconds': 120,
     'basis': 'upper bound: worker RLIMIT_CPU 90 s + controller 30 s on 1 core, wall stop 110 s; no refund',
     'prior_ledger_sha256': document_hash(expected)}
expected = copy.deepcopy(expected); expected['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 120
bookings = [seg, b]
assert cpu_used(expected['r6_phase0_cpu']) <= cpu_cap(expected['r6_phase0_cpu'])
d = {'run_id': NAME, 'kind': 'paper1-rewrite-pipeline-fixture', 'model_calls': 0, 'gpu_seconds': 0,
     'retry': False, 'cpu_seconds': 90, 'wall_stop_seconds': 110, 'cpu_threads': 1, 'files_sha256': pins,
     'package_sha256': package_sha, 'source_commit': git('rev-parse', 'HEAD').decode().strip(), 'tokenizer_files_sha256': remote_tok,
     'km_sha256': pins[KM], 'lmfe_source_sha256': freeze['generation_runtime']['lmfe_source_sha256'],
     'cpu_booking_sha256': document_hash(b), 'owner_authority_sha256': authority, 'expected_cases_or_invocations': 4,
     'max_consecutive_whitespaces': freeze['generation_runtime']['max_consecutive_whitespaces'],
     'force_json_field_order': freeze['generation_runtime']['force_json_field_order'],
     'paper1_freeze_manifest_sha256': sha((A/'paper1-freeze/freeze-manifest.json').read_bytes()),
     'qualification_scope': 'actual run_paper1_rewrite worker (FA then GR, 2 authored queries each, incl. blank-field fallback) with authored CPU model double; no weights/GPU/model calls'}
raw = json.dumps(d, indent=2).encode() + b'\n'
(OUT/'bookings.json').write_text(json.dumps(bookings, indent=2) + '\n'); (OUT/'fixture-declaration.json').write_bytes(raw)
out = book(CODE, bookings, gen)
assert document_hash(out['ledger']) == document_hash(expected); write_ledger(out['ledger'])
files = {'code/' + n: x for n, x in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_paper1_rewrite_fixture.py', 'supervise_automatic_grammar.py', 'supervise_r3_engine_v2.py', 'r3_engine_client.py')})
files['declaration.json'] = raw
summary = {'generation': gen + len(bookings), 'ledger_sha256': document_hash(expected),
           'cpu_remaining_seconds': cpu_cap(expected['r6_phase0_cpu']) - cpu_used(expected['r6_phase0_cpu']),
           'segment30_seconds': seg['conservative_cpu_seconds'], 'package_sha256': package_sha,
           'jobs': {'fixture': {'job': NAME, 'supervisor': 'supervise_paper1_rewrite_fixture.py', 'declaration_sha256': sha(raw),
                                'transport': stage(NAME, files)}}}
(OUT/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
