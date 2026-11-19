import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech'))
import bridgeret_select_sstar as ss  # noqa: E402


def test_tie_goes_to_simpler_recipe_then_smaller_grid_value():
    assert ss.select({'S3-t0.02-w1.5': 0.3005, 'S2-t0.02': 0.2998, 'S1-t0.02': 0.2900})[0] == 'S2-t0.02'
    assert ss.select({'S2-t0.05': 0.3000, 'S2-t0.02': 0.2995})[0] == 'S2-t0.02'
    assert ss.select({'S4rule-t0.02': 0.31, 'S1-t0.02': 0.2989})[0] == 'S4rule-t0.02'   # 0.0111 apart: no tie
    assert ss.select({'S2-t0.02': 0.3000, 'S1-t0.02': 0.2990})[0] == 'S1-t0.02'         # exactly 0.001: tied


def test_rejects_unknown_names():
    with pytest.raises(SystemExit):
        ss.parse_cfg('S5-t0.02')


def _write(p, block, out):
    p.parent.mkdir(parents=True, exist_ok=True)
    m = {k: {'mean': out, 'n': 10} for k in ss.COLS}
    p.write_text(json.dumps({'block': block, 'metrics': m}), encoding='utf-8')


def test_end_to_end_table(tmp_path):
    for c, v in (('S2-t0.02', 0.30), ('S1-t0.02', 0.28)):
        for b in ('P1-DEV', 'VAL'):
            _write(tmp_path / f'ft-{c}' / f'eval-{b}.json', b, v)
    for b in ('P1-DEV', 'VAL'):
        _write(tmp_path / 'z-qwen3' / f'eval-{b}.json', b, 0.2741)
    ss.main([str(tmp_path), str(tmp_path / 's.json'), str(tmp_path / 's.md'), 'S2-t0.02', 'S1-t0.02'])
    r = json.loads((tmp_path / 's.json').read_text())
    assert r['S_star'] == 'S2-t0.02'
    assert r['S_star_minus_z_qwen3_DEV_OUT_R@200'] == pytest.approx(0.0259)
    assert '**(S\\*)**' in (tmp_path / 's.md').read_text(encoding='utf-8')
