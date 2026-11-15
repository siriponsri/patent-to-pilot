"""Apply owner disk cap link 40 GiB -> 52 GiB ONCE (owner-disk-cap-approval.json). The module's chain check refuses a second run."""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeover_lib import *
GIB = 1024**3
ledger = json.loads(L.read_bytes()); lsha = document_hash(ledger)
assert ledger['disk_limit_bytes_combined_incremental'] == 40 * GIB and not ledger.get('disk_cap_amendments'), 'already amended'
module = blob('src/patent_to_pilot/research/automatic_disk_cap.py').replace(b'\r\n', b'\n').decode()
receipt = {'kind': 'DISK_CAP_AMENDMENT', 'owner_approval_sha256': sha((A/'owner-disk-cap-approval.json').read_bytes()),
           'model_calls': 0, 'gpu_seconds': 0, 'from_bytes': 40 * GIB, 'to_bytes': 52 * GIB, 'prior_ledger_sha256': lsha,
           'module_sha256_lf': hashlib.sha256(module.encode()).hexdigest(), 'journal_identity': IDENTITY}
(A/'disk-cap-amendment-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
payload = {'module': module, 'receipt': receipt}
out = journal(JOBS + '/ptp-auto-paper1-gr-pilot-retrieval-20261113-v1/code/src',
    "import importlib.util,hashlib\nimport patent_to_pilot.research\n"
    "pl=json.loads(" + repr(json.dumps(payload)) + ")\n"
    "assert hashlib.sha256(pl['module'].encode()).hexdigest()==pl['receipt']['module_sha256_lf']\n"
    "spec=importlib.util.spec_from_loader('patent_to_pilot.research.automatic_disk_cap',loader=None)\n"
    "m=importlib.util.module_from_spec(spec);m.__package__='patent_to_pilot.research'\n"
    "exec(compile(pl['module'],'automatic_disk_cap.py','exec'),m.__dict__)\n"
    "h,at=head()\nassert h[4] is None and json.loads(h[3])['automatic_study']['status']=='IDLE' and document_hash(json.loads(h[2]))==pl['receipt']['prior_ledger_sha256']\n"
    "m.amend_disk_cap(DispatchJournal(path,h[0]),expected_generation=h[1],receipt=pl['receipt'],receipt_sha256=document_hash(pl['receipt']))\n"
    "h,at=head()\nprint(json.dumps({'generation':h[1],'ledger':json.loads(h[2])}))\n")
new = out['ledger']
assert new['disk_limit_bytes_combined_incremental'] == 52 * GIB
rest = dict(new); rest.pop('disk_limit_bytes_combined_incremental'); rest.pop('disk_cap_amendments')
old = dict(ledger); old.pop('disk_limit_bytes_combined_incremental')
assert document_hash(rest) == document_hash(old), 'other ledger fields changed'
write_ledger(new)
res = {'status': 'DISK_CAP_AMENDED', 'generation': out['generation'], 'from_bytes': 40 * GIB, 'to_bytes': 52 * GIB,
       'ledger_sha256': document_hash(new), 'receipt_sha256': document_hash(receipt), 'other_fields_unchanged': True}
(A/'disk-cap-amendment-result.json').write_text(json.dumps(res, indent=2) + '\n'); print(json.dumps(res))
