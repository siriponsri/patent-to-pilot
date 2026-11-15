"""SACR repaired-worker CPU fixture v8 (owner decision 2026-11-15 'A: ขยายกติกา': refusal + dead end): freeze + book + stage ONCE (no launch).
Bookings: next segment (local metered + 100 s) + 120 s remote upper bound (no refund), from the live generation.
Scope: actual run_automatic_native worker; 3 authored queries; LMFE fallback-EOS state injected in query 2 marking and
a grammar dead end in query 3 review; expected 5 calls, 1 screened + 1 GRAMMAR_REFUSED + 1 GRAMMAR_NO_CONTINUATION."""
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

NAME = 'ptp-auto-native-fixture-20261115-v8'
SEG = 1 + max(int(re.fullmatch(r'segment(\d+)-booking\.json', q.name).group(1)) for q in A.rglob('segment*-booking.json'))
CODE = JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src'
OUT = A/'native-fixture-v8'; OUT.mkdir(exist_ok=False)
ledger = json.loads(L.read_bytes()); ledger_sha = document_hash(ledger)
h = journal(CODE, "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4],"
                  "'status':json.loads(h[3])['automatic_study']['status']}))\n")
assert h['active'] is None and h['ledger_sha256'] == ledger_sha and h['status'] == 'IDLE', h
gen = h['generation']
blobs, pins = package(['supervise_automatic_grammar.py', 'supervise_automatic_pipeline_fixture.py', 'supervise_automatic_native_fixture.py',
                       'qualify_automatic_native_pipeline.py', 'run_automatic_native.py'])
package_sha = package_identity(pins)
remote_tok = ssh("import hashlib,json\nfrom pathlib import Path\nm=Path('" + JOBS + "/research-product-o1-o4-20261031/models/qwen3-8b')\n"
                 "print(json.dumps({n:hashlib.sha256((m/n).read_bytes()).hexdigest() for n in ('tokenizer.json','tokenizer_config.json','config.json','vocab.json','merges.txt','generation_config.json')}))\n")
assert remote_tok['tokenizer.json'] == 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4'
lmfe = json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())['lmfe_source_sha256']
authority = sha((A/'owner-sacr-s4-dead-end-approval.json').read_bytes())
seg = segment_booking(SEG, ledger_sha)
expected = copy.deepcopy(ledger); expected['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
b = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': authority, 'evidence_sha256': package_sha,
     'booking_id': NAME, 'location': 'remote', 'conservative_cpu_seconds': 120,
     'basis': 'upper bound: worker RLIMIT_CPU 90 s + controller 30 s on 1 core, wall stop 110 s; no refund',
     'prior_ledger_sha256': document_hash(expected)}
expected = copy.deepcopy(expected); expected['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 120
bookings = [seg, b]
assert cpu_used(expected['r6_phase0_cpu']) <= cpu_cap(expected['r6_phase0_cpu'])
d = {'run_id': NAME, 'kind': 'automatic-native-pipeline-fixture', 'model_calls': 0, 'gpu_seconds': 0,
     'retry': False, 'cpu_seconds': 90, 'wall_stop_seconds': 110, 'cpu_threads': 1, 'files_sha256': pins,
     'package_sha256': package_sha, 'source_commit': git('rev-parse', 'HEAD').decode().strip(), 'tokenizer_files_sha256': remote_tok,
     'km_sha256': pins[KM], 'lmfe_source_sha256': lmfe, 'cpu_booking_sha256': document_hash(b),
     'owner_authority_sha256': authority, 'expected_cases_or_invocations': 5,
     'qualification_scope': 'v8 (owner decisions 2026-11-15): actual run_automatic_native worker; 3 authored queries; LMFE fallback-EOS state injected in query 2 marking (REAL EOS guard refuses -> GRAMMAR_REFUSED) and an LMFE dead-end state in query 3 review (REAL guard raises grammar has no continuation -> GRAMMAR_NO_CONTINUATION), both classified from real private diagnostics; falls back and continues; authored CPU model double; no weights/GPU/model calls'}
raw = json.dumps(d, indent=2).encode() + b'\n'
(OUT/'bookings.json').write_text(json.dumps(bookings, indent=2) + '\n'); (OUT/'fixture-declaration.json').write_bytes(raw)
(OUT/('segment%d-booking.json' % SEG)).write_text(json.dumps(seg, indent=2) + '\n')
out = book(CODE, bookings, gen)
assert document_hash(out['ledger']) == document_hash(expected); write_ledger(out['ledger'])
files = {'code/' + n: x for n, x in blobs.items()}
files.update({n: blobs['scripts/healthtech/' + n] for n in ('supervise_automatic_native_fixture.py', 'supervise_automatic_pipeline_fixture.py',
                                                            'supervise_automatic_grammar.py', 'supervise_r3_engine_v2.py', 'r3_engine_client.py')})
files['declaration.json'] = raw
summary = {'generation': gen + len(bookings), 'ledger_sha256': document_hash(expected),
           'cpu_remaining_seconds': cpu_cap(expected['r6_phase0_cpu']) - cpu_used(expected['r6_phase0_cpu']),
           'segment': SEG, 'segment_seconds': seg['conservative_cpu_seconds'], 'package_sha256': package_sha,
           'jobs': {'fixture': {'job': NAME, 'supervisor': 'supervise_automatic_native_fixture.py', 'declaration_sha256': sha(raw),
                                'transport': stage(NAME, files)}}}
(OUT/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
