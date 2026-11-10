"""Build and check a local CPU-probe archive; never launch a remote job."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile


def git(*args):
    return subprocess.check_output(['git', *args])


def verify(raw, commit, declaration_path, payload_path):
    """Require declared bytes and immutable Git blobs, not normalized equivalents."""
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        def read(name):
            matches = [m for m in archive.getmembers() if m.name == name]
            if len(matches) != 1 or not matches[0].isfile():
                raise ValueError('missing, duplicate or nonregular pinned member: ' + name)
            return archive.extractfile(matches[0]).read()

        declaration_raw = read(declaration_path)
        if declaration_raw != git('show', commit + ':' + declaration_path):
            raise ValueError('declaration differs from committed bytes')
        declaration = json.loads(declaration_raw)
        expected = dict(declaration['code_files_sha256'])
        if payload_path in expected:
            raise ValueError('payload/code path collision')
        expected[payload_path] = declaration['payload_sha256']
        rows = []
        for name, digest in expected.items():
            data = read(name)
            actual = hashlib.sha256(data).hexdigest()
            if actual != digest or data != git('show', commit + ':' + name):
                raise ValueError('archive identity mismatch: ' + name)
            rows.append({'path': name, 'sha256': actual, 'bytes': len(data)})
    return {'commit': commit, 'archive_sha256': hashlib.sha256(raw).hexdigest(),
            'archive_bytes': len(raw), 'pinned_files': rows,
            'declaration_sha256': hashlib.sha256(declaration_raw).hexdigest(),
            'status': 'LOCAL_ARCHIVE_VERIFIED', 'remote_execution': 'NOT_RUN'}


def package(commit, declaration_path, payload_path, output):
    commit = git('rev-parse', '--verify', commit + '^{commit}').decode().strip()
    # Per-command settings only: do not alter repository/global Git configuration.
    raw = git('-c', 'core.autocrlf=false', '-c', 'core.eol=lf', 'archive',
              '--format=tar', commit, 'src',
              'scripts/healthtech/probe_sacr_escape_candidate.py',
              declaration_path, payload_path)
    receipt = verify(raw, commit, declaration_path, payload_path)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'code.tar').write_bytes(raw)
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--declaration', required=True)
    parser.add_argument('--payload', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.commit, args.declaration, args.payload, args.output), indent=2))
