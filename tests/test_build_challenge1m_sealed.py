"""Synthetic test of the Challenge-1M sealed builder (tiny SIZE, authored rows only)."""
import importlib.util, json, pathlib, zipfile


def _z(d, name, rows):
    with zipfile.ZipFile(d / f'{name}.tsv.zip', 'w') as z:
        z.writestr(f'{name}.tsv', '\n'.join('\t'.join(r) for r in rows) + '\n')


def test_tiers_isolation_and_units(tmp_path, monkeypatch):
    p = pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'healthtech' / 'build_challenge1m_sealed.py'
    spec = importlib.util.spec_from_file_location('c1m', p); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    monkeypatch.setattr(mod, 'SIZE', 6)
    pv = tmp_path / 'pv'; pv.mkdir()
    _z(pv, 'g_application', [('application_id', 'patent_id'), ('10000001', '7000001'), ('10000002', 'RE045000')])
    _z(pv, 'g_patent', [('patent_id', 'patent_date'), ('7000001', '2008-01-01'), ('RE045000', '2010-01-01'),
                        ('7000003', '2005-01-01'), ('7000004', '2006-01-01'), ('7000005', '2007-01-01'),
                        ('7000006', '2007-02-01'), ('7000007', '2014-01-01'), ('3000000', '1970-01-01')])
    _z(pv, 'pg_published_application', [('pgpub_id', 'application_id', 'patent_type', 'published_date'),
                                         ('20070000001', '10000001', 'utility', '2007-06-01'),
                                         ('20070000009', '19999999', 'plant', '2007-06-01')])
    pairs = tmp_path / 'pairs.tsv'
    pairs.write_text('app_id\tcited\tbasis\tdom_ipc3\tdom_ipc4\tsection\n'
                     'T1\tP7000001\t103\tOUT3\tOUT4\tSECMIS\n'      # P1-TEST -> tier1 (unit A:10000001)
                     'T1\tPG20070000001\t103\tOUT3\tOUT4\tSECMIS\n'  # same unit, earliest doc = pgpub
                     'D1\tPRE45000\t102\tIN3\tIN4\tSAMESEC\n'        # P1-DEV -> tier1
                     'X1\tP7000003\t103\tIN3\tIN4\tSAMESEC\n'        # P2-TEST -> tier2
                     'X1\tP7000007\t103\tIN3\tIN4\tSAMESEC\n'        # outside window
                     'R1\tP7000004\t103\tOUT3\tOUT4\tSECMIS\n')      # TRAIN -> tier2, dev-visible
    man = {'frozen': True, 'manifest_sha256': 'x', 'blocks': {'P1-TEST': ['T1'], 'P1-DEV': ['D1'], 'P2-TEST': ['X1'], 'TRAIN': ['R1']}}
    mp = tmp_path / 'm.json'; mp.write_text(json.dumps(man))
    mod.main([str(pv), str(pairs), str(mp), str(tmp_path / 'out')])
    rep = json.loads((tmp_path / 'out' / 'report.json').read_text())
    assert rep['size'] == 6 and rep['tier1_units'] == 2 and rep['tier2_units_kept'] == 2 and rep['tier3_units'] == 2
    corpus = (tmp_path / 'out' / 'corpus-units.tsv').read_text().splitlines()[1:]
    units = {l.split('\t')[0]: l.split('\t')[1] for l in corpus}
    assert units['A:10000001'] == 'PG20070000001' and 'A:10000002' in units
    assert 'D:P7000007' not in units and 'D:P3000000' not in units       # outside 1976..2012
    dev = (tmp_path / 'out' / 'pairs-dev.tsv').read_text()
    assert 'D1' in dev and 'R1' in dev and 'T1' not in dev and 'X1' not in dev
    sealed = (tmp_path / 'out' / 'sealed' / 'qrels-p1-test.tsv').read_text()
    assert sealed.count('A:10000001') == 2
