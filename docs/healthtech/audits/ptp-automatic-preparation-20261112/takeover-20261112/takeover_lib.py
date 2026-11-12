"""Shared one-shot helpers for takeover staging (git blobs, remote journal, bookings, transport)."""
from pathlib import Path
import copy, hashlib, io, json, math, re, subprocess, sys, tarfile
R = Path('C:/Users/User/Desktop/myProject/patent-to-pilot'); sys.path.insert(0, str(R/'src'))
A = R/'docs/healthtech/audits/ptp-automatic-preparation-20261112/takeover-20261112'
L = R/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json'
from patent_to_pilot.research.r6_dispatch_journal import document_hash
HOST = 'chaw@100.77.149.83'; JOBS = '/home/chaw/patent-to-pilot-jobs'
IDENTITY = '2b7c2aae40fafff474721b87ff1531569aeaa29990f8234bea32ac2d6b744db4'
VENV = JOBS + '/research-product-o1-o4-20261031/venv/lib/python3.12/site-packages'
sha = lambda b: hashlib.sha256(b).hexdigest()
COMMON_SCRIPTS = ['r3_engine_client.py', 'supervise_r3_engine_v2.py', 'supervise_sacr_r5_engine.py', 'run_r6_calibration.py',
                  'supervise_r6_calibration.py', 'inspect_qwen_weight_identity.py', 'run_r7_calibration.py', 'supervise_r7_calibration.py']
KM = 'docs/healthtech/research/plans/PATENT-STRUCTURE-KM.md'
IDENT = 'docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json'


def git(*a): return subprocess.run(['git', *a], cwd=R, capture_output=True, check=True).stdout
def blob(p): return git('show', 'HEAD:' + p)


def ssh(code, timeout=120):
    r = subprocess.run(['ssh', '-o', 'BatchMode=yes', HOST, 'python3 -'], input=code.encode(), capture_output=True, timeout=timeout)
    if r.returncode: print(r.stderr.decode()[-3000:]); r.check_returncode()
    return json.loads(r.stdout)


def journal(code_src, body):
    """Run body on the remote journal with the given staged code; body may call head()."""
    return ssh("import json,sys,sqlite3\nfrom pathlib import Path\nsys.path[:0]=['" + code_src + "','" + VENV + "']\n"
               "from patent_to_pilot.research.r6_dispatch_journal import document_hash,DispatchJournal\n"
               "path=Path('" + JOBS + "/ptp-r6-control/dispatch.sqlite')\n"
               "def head():\n with sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True) as db:\n"
               "  h=db.execute('SELECT identity,generation,ledger,scope,active FROM head').fetchone()\n"
               "  at=db.execute('SELECT id,declaration,terminal FROM attempts ORDER BY id').fetchall()\n"
               " return h,at\n" + body)


def package(scripts):
    assert not git('status', '--porcelain', '--', 'src', 'scripts/healthtech').strip(), 'uncommitted package source'
    names = [p for p in git('ls-files', 'src').decode().split() if p.endswith('.py')]
    names += ['scripts/healthtech/' + n for n in COMMON_SCRIPTS + scripts] + [KM, IDENT]
    blobs = {n: blob(n) for n in names}
    return blobs, {n: sha(b) for n, b in blobs.items()}


def next_segment():
    """Metered lines not yet covered by any segment booking receipt."""
    covered = 0
    for p in A.rglob('segment*-booking.json'):
        m = re.search(r'lines (\d+)\.\.(\d+)', json.loads(p.read_bytes())['basis']); covered = max(covered, int(m.group(2)))
    meas = (A/'local-cpu-measurements.jsonl').read_bytes(); lines = meas.decode().splitlines()
    measured = sum(json.loads(x)['cpu_seconds'] for x in lines[covered:])
    return meas, covered + 1, len(lines), measured


def segment_booking(number, prior_ledger_sha):
    meas, first, last, measured = next_segment()
    return {'model_calls': 0, 'gpu_seconds': 0, 'owner_approval_sha256': sha((A/'owner-cpu-amendment.json').read_bytes()),
            'evidence_sha256': sha(meas), 'booking_id': 'takeover-20261112-segment%d' % number, 'location': 'local',
            'conservative_cpu_seconds': math.ceil(measured + 100),
            'basis': 'metered lines %d..%d (%.6f s) + 100 s conservative unmetered shell/inspection allowance' % (first, last, measured),
            'prior_ledger_sha256': prior_ledger_sha}


def book(code_src, bookings, generation):
    """Apply CPU bookings in order from `generation`; returns new head ledger."""
    out = journal(code_src, "from patent_to_pilot.research.automatic_cpu_booking import book_cpu\n"
        "bs=json.loads(" + repr(json.dumps(bookings)) + ")\nj=DispatchJournal(path,'" + IDENTITY + "')\n"
        "for i,b in enumerate(bs):book_cpu(j,expected_generation=" + str(generation) + "+i,receipt=b,receipt_sha256=document_hash(b))\n"
        "h,at=head()\nassert h[1]==" + str(generation + len(bookings)) + " and h[4] is None\n"
        "print(json.dumps({'ledger':json.loads(h[2]),'scope_sha256':document_hash(json.loads(h[3])),'attempts_sha256':document_hash(at)}))\n")
    return out


def write_ledger(new):
    old = json.loads(L.read_bytes())
    def order(ref, val):
        if isinstance(ref, dict) and isinstance(val, dict):
            o = {k: order(ref[k], val[k]) for k in ref if k in val}; o.update({k: x for k, x in val.items() if k not in ref}); return o
        if isinstance(ref, list) and isinstance(val, list) and len(ref) == len(val): return [order(a, b) for a, b in zip(ref, val)]
        return val
    L.write_text(json.dumps(order(old, new), indent=2) + '\n')
    assert document_hash(json.loads(L.read_bytes())) == document_hash(new)


def stage(name, files):
    """files: {archive_path: bytes}. Creates the job dir (must not exist), transfers, verifies, extracts."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tar:
        for arc, data in files.items():
            i = tarfile.TarInfo(arc); i.size = len(data); i.mode = 0o644; i.mtime = 0; tar.addfile(i, io.BytesIO(data))
    data = buf.getvalue(); transport = {'bytes': len(data), 'sha256': sha(data), 'files': len(files)}
    tmp = Path('C:/Users/User/AppData/Local/Temp/' + name + '.tar'); tmp.write_bytes(data); job = JOBS + '/' + name
    ssh("from pathlib import Path\np=Path('" + job + "')\nassert not p.exists()\np.mkdir()\nprint('{}')\n")
    subprocess.run(['scp', '-q', str(tmp), HOST + ':' + job + '/transport.tar'], check=True, timeout=120)
    ssh(f"""from pathlib import Path
import tarfile,hashlib
p=Path('{job}');t=p/'transport.tar'
assert hashlib.sha256(t.read_bytes()).hexdigest()=='{transport['sha256']}'
with tarfile.open(t) as a:
 assert all(not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in a.getmembers())
 a.extractall(p,filter='data')
print('{{}}')
""")
    return transport
