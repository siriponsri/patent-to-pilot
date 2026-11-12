"""Freeze + book + stage BOTH v3 CPU jobs (grammar, pipeline fixture) ONCE; no launch.
Bookings: segment 11 (local) + 600 s per job (remote, no refund), from the live generation."""
import copy, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.r6_dispatch_files import package_identity
from patent_to_pilot.research.automatic_cpu_booking import cpu_used, cpu_cap

JOBS_V2 = {'grammar': ('ptp-auto-grammar-20261112-v5', 'supervise_automatic_grammar.py', 'automatic-grammar-only',
                       ['supervise_automatic_grammar.py'], 9,
                       'actual tokenizer + R6Backend grammar/EOS replay of 8 authored cases (marking v4, review v2 literal-span quotes; paraphrase rejected); grammar mechanics only'),
           'fixture': ('ptp-auto-pipeline-fixture-20261112-v5', 'supervise_automatic_pipeline_fixture.py', 'automatic-synthetic-pipeline-fixture',
                       ['supervise_automatic_pipeline_fixture.py', 'supervise_automatic_grammar.py'], 2,
                       'actual run_automatic_synthetic main (marking v4, review v2) with authored CPU model double; no weights/GPU/model calls')}
OUT = A/'cpu-v5'; OUT.mkdir(exist_ok=False)
ledger = json.loads(L.read_bytes()); ledger_sha = document_hash(ledger)
h = journal(JOBS + '/ptp-auto-synthetic-20261112-v4/code/src',
            "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger_sha256':document_hash(json.loads(h[2])),'active':h[4]}))\n")
assert h['active'] is None and h['ledger_sha256'] == ledger_sha, h
gen = h['generation']
blobs, pins = package(['supervise_automatic_grammar.py', 'qualify_automatic_grammar.py', 'run_automatic_synthetic.py',
                       'supervise_automatic_pipeline_fixture.py', 'qualify_automatic_synthetic_pipeline.py'])
package_sha = package_identity(pins)
remote_tok = ssh("import hashlib,json\nfrom pathlib import Path\nm=Path('" + JOBS + "/research-product-o1-o4-20261031/models/qwen3-8b')\n"
                 "print(json.dumps({n:hashlib.sha256((m/n).read_bytes()).hexdigest() for n in ('tokenizer.json','tokenizer_config.json','config.json','vocab.json','merges.txt','generation_config.json')}))\n")
assert remote_tok['tokenizer.json'] == 'aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4'
old = json.loads((R/'docs/healthtech/audits/ptp-r6-phase0-execution-20261111/critic-declaration.json').read_bytes())
authority = sha((A/'owner-long-run-authority.json').read_bytes())
seg = segment_booking(11, ledger_sha)
expected = copy.deepcopy(ledger); expected['r6_phase0_cpu']['local_cpu_conservative_charged_seconds'] += seg['conservative_cpu_seconds']
bookings = [seg]; decls = {}
for kind, (name, sup, k, roots, cases, scope) in JOBS_V2.items():
    b = {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': authority, 'evidence_sha256': package_sha,
         'booking_id': name, 'location': 'remote', 'conservative_cpu_seconds': 120,
         'basis': 'upper bound: worker RLIMIT_CPU 90 s + controller 30 s on 1 core, wall stop 110 s; no refund',
         'prior_ledger_sha256': document_hash(expected)}
    expected = copy.deepcopy(expected); expected['r6_phase0_cpu']['remote_cpu_charged_seconds'] += 120
    bookings.append(b)
    tok = {n: v for n, v in remote_tok.items() if kind == 'fixture' or n != 'generation_config.json'}
    d = {'run_id': name, 'kind': k, 'model_calls': 0, 'gpu_seconds': 0, 'retry': False, 'cpu_seconds': 90,
         'wall_stop_seconds': 110, 'cpu_threads': 1, 'files_sha256': pins, 'package_sha256': package_sha,
         'source_commit': git('rev-parse', 'HEAD').decode().strip(), 'tokenizer_files_sha256': tok,
         'km_sha256': pins[KM], 'lmfe_source_sha256': old['lmfe_source_sha256'], 'cpu_booking_sha256': document_hash(b),
         'owner_authority_sha256': authority, 'expected_cases_or_invocations': cases, 'qualification_scope': scope}
    decls[kind] = (name, sup, roots, json.dumps(d, indent=2).encode() + b'\n')
assert cpu_used(expected['r6_phase0_cpu']) <= cpu_cap(expected['r6_phase0_cpu'])
for n, v in (('bookings.json', bookings),): (OUT/n).write_text(json.dumps(v, indent=2) + '\n')
for kind, (name, sup, roots, raw) in decls.items(): (OUT/(kind + '-declaration.json')).write_bytes(raw)
out = book(JOBS + '/ptp-auto-synthetic-20261112-v4/code/src', bookings, gen)  # v1 staged code holds book_cpu with cpu_cap
assert document_hash(out['ledger']) == document_hash(expected); write_ledger(out['ledger'])
summary = {'generation': gen + len(bookings), 'ledger_sha256': document_hash(expected),
           'cpu_remaining_seconds': cpu_cap(expected['r6_phase0_cpu']) - cpu_used(expected['r6_phase0_cpu']),
           'segment11_seconds': seg['conservative_cpu_seconds'], 'package_sha256': package_sha, 'jobs': {}}
for kind, (name, sup, roots, raw) in decls.items():
    files = {'code/' + n: b for n, b in blobs.items()}
    files.update({n: blobs['scripts/healthtech/' + n] for n in roots + ['supervise_r3_engine_v2.py', 'r3_engine_client.py']})
    files['declaration.json'] = raw
    summary['jobs'][kind] = {'job': name, 'supervisor': sup, 'declaration_sha256': sha(raw), 'transport': stage(name, files)}
(OUT/'freeze-summary.json').write_text(json.dumps(summary, indent=2) + '\n'); print(json.dumps(summary))
