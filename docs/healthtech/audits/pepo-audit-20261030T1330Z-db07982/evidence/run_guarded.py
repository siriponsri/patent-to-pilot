"""Inspected all-suite in exact Git archive; extra no-network/no-secret guards."""
from pathlib import Path
import os
import runpy
import sys

sys.dont_write_bytecode=True
base=Path(__file__).resolve().parent
snapshot=base/(sys.argv[1] if len(sys.argv)>1 else 'snapshot')
audit_output=base/(sys.argv[2] if len(sys.argv)>2 else 'guarded-suite')
assert snapshot.resolve().is_relative_to(base) and audit_output.resolve().is_relative_to(base)
for key in list(os.environ):
    if key.endswith(('API_KEY','ACCESS_TOKEN','SECRET_KEY')):
        del os.environ[key]
def guard(event,args):
    if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
        p=Path(os.fsdecode(args[0])).resolve()
        if p.name.startswith('.env') and p.name!='.env.example':
            # Authored fake key fixtures under this audit's test tmp are allowed.
            if not p.is_relative_to(audit_output):
                raise RuntimeError('audit: actual/outside credential path forbidden')
        if any(x in p.parts for x in ('.ssh','.aws')):
            raise RuntimeError('audit: private configuration forbidden')
sys.addaudithook(guard)
os.chdir(snapshot)
sys.argv=['verify_offline.py',str(audit_output),'--suite','all']
runpy.run_path(str(snapshot/'scripts/healthtech/verify_offline.py'),run_name='__main__')
