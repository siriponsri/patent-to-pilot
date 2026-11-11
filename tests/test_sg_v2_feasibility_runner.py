import importlib.util
import json
from pathlib import Path

import pytest


def test_failure_keeps_elapsed_progress_and_blocks_replay(tmp_path,monkeypatch):
    path=Path(__file__).resolve().parents[1]/'scripts/healthtech/run_sg_v2_feasibility.py'
    spec=importlib.util.spec_from_file_location('sg_runner',path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    audit=tmp_path/'audit'; audit.mkdir()
    (audit/'declaration.json').write_text(json.dumps({'sample_sha256':'a'*64,
        'corpus_sha256':'b'*64,'code_sha256':'c'*64}))
    monkeypatch.setattr(m,'AUDIT',audit); monkeypatch.setattr(m,'OUTPUT',tmp_path/'out')
    calls=[]
    def fail(progress):
        calls.append(1); m.OUTPUT.mkdir()
        progress.update(stage='CORPUS_SCAN',corpus_rows=42,output_created=True)
        raise TimeoutError('authored timeout')
    monkeypatch.setattr(m,'run',fail)
    with pytest.raises(TimeoutError): m.main()
    result=json.loads((audit/'failure.json').read_bytes())
    assert result['wall_seconds']>=0 and result['progress']['corpus_rows']==42
    assert result['model_calls']==result['gpu_seconds']==0 and result['retry'] is False
    with pytest.raises(FileExistsError): m.main()
    assert len(calls)==1
