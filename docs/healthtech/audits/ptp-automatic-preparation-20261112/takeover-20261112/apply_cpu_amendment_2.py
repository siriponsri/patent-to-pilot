"""Apply owner CPU cap link 57600 -> 86400 ONCE (no booking). Idempotent via chain check."""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
from patent_to_pilot.research.automatic_cpu_booking import cpu_cap, cpu_used
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
module = (R/'src/patent_to_pilot/research/automatic_cpu_booking.py').read_bytes().replace(b'\r\n', b'\n').decode()
receipt = {'kind': 'CPU_CAP_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-cpu-amendment-2.json').read_bytes()),
           'model_calls': 0, 'from_seconds': 57600, 'to_seconds': 86400, 'prior_ledger_sha256': lsha,
           'module_sha256_lf': hashlib.sha256(module.encode()).hexdigest(), 'journal_identity': IDENTITY}
(A/'cpu-amendment-2-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
payload = {'module': module, 'receipt': receipt}
out = journal(JOBS + '/ptp-auto-graph-extractor-v3-20261112-v1/code/src',
    "import importlib.util,hashlib\nimport patent_to_pilot.research\n"
    "pl=json.loads(" + repr(json.dumps(payload)) + ")\n"
    "assert hashlib.sha256(pl['module'].encode()).hexdigest()==pl['receipt']['module_sha256_lf']\n"
    "spec=importlib.util.spec_from_loader('patent_to_pilot.research.automatic_cpu_booking',loader=None)\n"
    "m=importlib.util.module_from_spec(spec);m.__package__='patent_to_pilot.research'\n"
    "exec(compile(pl['module'],'automatic_cpu_booking.py','exec'),m.__dict__)\n"
    "h,at=head()\nassert h[4] is None and document_hash(json.loads(h[2]))==pl['receipt']['prior_ledger_sha256']\n"
    "m.amend_cpu_cap(DispatchJournal(path,h[0]),expected_generation=h[1],receipt=pl['receipt'],receipt_sha256=document_hash(pl['receipt']))\n"
    "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger':json.loads(h[2])}))\n")
write_ledger(out['ledger']); c = out['ledger']['r6_phase0_cpu']
print(json.dumps({'generation': out['generation'], 'cap': cpu_cap(c), 'used': cpu_used(c), 'remaining': cpu_cap(c) - cpu_used(c)}))
