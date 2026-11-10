"""Local regression against immutable CPU-003 commit; no tokenizer or dispatch."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('packager', root / 'scripts/healthtech/package_sacr_cpu_archive.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
commit = 'a9c1d640d0c950fc0c032339fac87a29fd622ab2'
prefix = 'docs/healthtech/audits/ptp-method-first-escape-cpu-declaration-20261110/'
declaration, payload = prefix + 'declaration.json', prefix + 'authored-fixtures.json'
paths = ['src', 'scripts/healthtech/probe_sacr_escape_candidate.py', declaration, payload]
raw = module.git('-c', 'core.autocrlf=false', '-c', 'core.eol=lf', 'archive', commit, *paths)
receipt = module.verify(raw, commit, declaration, payload)
cases = [{'case': 'exact_archive_accepts_all_five_pins_and_declaration', 'pass': True}]


def rejected(name, data):
    try:
        module.verify(data, commit, declaration, payload)
    except ValueError as exc:
        cases.append({'case': name, 'pass': True, 'reason': str(exc)})
    else:
        raise AssertionError('accepted invalid archive: ' + name)


rejected('windows_crlf_archive_rejected', module.git('-c', 'core.autocrlf=true',
         'archive', commit, *paths))
for mutation in ('payload_changed', 'code_changed', 'payload_missing', 'payload_duplicate'):
    stream = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as source:
        with tarfile.open(fileobj=stream, mode='w:') as target:
            for member in source.getmembers():
                if mutation == 'payload_missing' and member.name == payload:
                    continue
                content = source.extractfile(member).read() if member.isfile() else None
                if ((mutation == 'payload_changed' and member.name == payload) or
                    (mutation == 'code_changed' and member.name.endswith('/sacr_escape_callback.py'))):
                    content += b' '
                    member.size = len(content)
                target.addfile(member, io.BytesIO(content) if content is not None else None)
                if mutation == 'payload_duplicate' and member.name == payload:
                    target.addfile(member, io.BytesIO(content))
    rejected(mutation, stream.getvalue())
result = {'status': 'PASS', 'cases': cases, 'verified_archive': receipt,
          'model_calls': 0, 'remote_execution': 'NOT_RUN'}
Path(__file__).with_name('verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
