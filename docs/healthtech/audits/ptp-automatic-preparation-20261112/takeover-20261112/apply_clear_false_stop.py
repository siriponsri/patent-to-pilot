"""Apply the owner-approved CLEAR_FALSE_CPU_OVERRUN once to the live journal (generation 92 -> 93).

Executes the committed automatic_dispatch_journal module (hash-checked) against the remote journal,
then mirrors the ledger locally. If the stop is already cleared it only verifies; never re-applies.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import A, IDENTITY, JOBS, blob, document_hash, journal, sha, write_ledger

ATTEMPT = 'ptp-auto-sacr-pilot-retrieval-20261113-v1'
CODE = JOBS + '/ptp-auto-native-sacr-fulldev-b1-20261113-v1/code/src'
approval = (A/'owner-false-cpu-stop-approval.json').read_bytes()
evidence = (A/'sacr-pilot-retrieval/terminal-evidence.json').read_bytes()
receipt = {'kind': 'CLEAR_FALSE_CPU_OVERRUN', 'attempt_id': ATTEMPT, 'container_cpus': 8,
           'container_cpus_basis': 'supervise_sacr_pilot_retrieval uses base configuration smoke: NanoCpus 8e9',
           'isolation_evidence_sha256': sha(evidence), 'owner_approval_sha256': sha(approval),
           'evidence': 'takeover-20261112/sacr-pilot-retrieval/terminal-evidence.json (Docker exited 0, wall 25.672 s)'}
module = blob('src/patent_to_pilot/research/automatic_dispatch_journal.py').decode()
out = journal(CODE, "import importlib.util,hashlib\nimport patent_to_pilot.research\n"
    "src=" + repr(module) + "\nassert hashlib.sha256(src.encode()).hexdigest()=='" + sha(module.encode()) + "'\n"
    "spec=importlib.util.spec_from_loader('patent_to_pilot.research.automatic_dispatch_journal',loader=None)\n"
    "m=importlib.util.module_from_spec(spec);m.__package__='patent_to_pilot.research'\n"
    "exec(compile(src,'automatic_dispatch_journal.py','exec'),m.__dict__)\n"
    "r=json.loads(" + repr(json.dumps(receipt)) + ")\n"
    "h,at=head();status=json.loads(h[3])['automatic_study']['status'];applied=False\n"
    "if status=='RESOURCE_OVERRUN_STOP':\n"
    " assert h[1]==92 and h[4] is None,'unexpected generation'\n"
    " m.AutomaticDispatchJournal(path,'" + IDENTITY + "').clear_false_cpu_overrun(expected_generation=92,receipt=r,receipt_sha256=document_hash(r));applied=True\n"
    "h,at=head();s=json.loads(h[3])['automatic_study']\n"
    "assert s['status']=='IDLE' and h[4] is None\n"
    "with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:tr=db.execute(\"SELECT generation,kind FROM automatic_transitions WHERE kind='CLEAR_FALSE_CPU_OVERRUN'\").fetchall()\n"
    "assert len(tr)==1\n"
    "print(json.dumps({'applied_now':applied,'generation':h[1],'status':s['status'],'transition':tr,"
    "'cost':s['stage_costs']['" + ATTEMPT + "'],'ledger':json.loads(h[2]),'scope_sha256':document_hash(json.loads(h[3]))}))\n")
ledger = out.pop('ledger')
write_ledger(ledger)
out.update(receipt=receipt, receipt_sha256=document_hash(receipt), ledger_sha256=document_hash(ledger))
(A/'clear-false-stop-receipt.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k: out[k] for k in ('applied_now', 'generation', 'status', 'transition', 'cost', 'ledger_sha256')}, indent=2))
