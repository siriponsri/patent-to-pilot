import importlib.util
from pathlib import Path

import pytest

path=Path(__file__).resolve().parents[1]/'scripts/healthtech/summarize_native_baseline_exposure.py'
spec=importlib.util.spec_from_file_location('exposure',path)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def row(a,b,c): return {'Recall@10':a,'Recall@100':b,'Recall@200':c}


def test_coarse_exposure_bins_cover_every_eligible_query():
    data={'OUT':{'a':row(.5,1,1),'b':row(0,.1,.2),'c':row(0,0,.25),'d':row(0,0,0)}}
    result=m.summarize(data,{'OUT':4})['OUT']
    assert result['first_known_positive_rank_bin']=={'1-10':1,'11-100':1,'101-200':1,'not_exposed_at_200':1}
    assert result['exposed_queries_at_200']==3
    assert result['mean_recall_check']['200']==.3625


@pytest.mark.parametrize('bad',[row(0,.5,.1),row(0,0,float('nan')),row(0,0,1.1)])
def test_invalid_or_nonmonotonic_metrics_refused(bad):
    with pytest.raises(ValueError): m.summarize({'OUT':{'q':bad}},{'OUT':1})
