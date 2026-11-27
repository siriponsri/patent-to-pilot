# CP4 | Development metric illustration

## Before scoring

Recommendation and family recorded in the opening of [the design](../CP4-METRIC-REDESIGN.md). Use the retained K07 primary split, frozen T1 TRAIN sigmoids for M1/M3 and an analogous five-drug-fold TRAIN sigmoid for B1. At each validation cutoff take floor(0.20 N) rows by decreasing entry probability. Fractionally allocate the final tied score block to give its exact expected yield under a uniform lottery. Micro-pool event capture and queue precision. Candidate two is pooled non-interpolated average precision with grouped ties. Candidate three is per-row decision loss at FN:FP:review = 10:1:0.5, applying lo=0.05, hi=0.5 with M3's existing BLOCKED override. Charge every referral and assume perfect adjudication for this illustrative loss. Do not tune settings on validation. Use 2,000 paired drug-cluster bootstrap draws, seed 20261127 per horizon, reapplying capacities to the resampled cutoffs. Report percentile 95% intervals for levels and paired differences, missing-denominator counts and class/action counts. No test scoring or lock.
## Reproduction on local CPU

**PASS, DEVELOPMENT_ONLY.** Executed at base `d2c8b21eb8398580eb2177a1a99e416ce349d287` with Python 3.12.10 and NumPy 2.5.4. K20 remains rejected. The inputs function verifies the pinned source files and applies the merged T4b byte-level ANDA projector before outcome decoding, with final observation 2016-01-01. No cutoff after 2015 was scored. Local CPU only, no paid or remote compute. Git-normalized LF SHA-256 of [CP4 validation](../../../loe-bench/data/CP4_validation.json) is `e5a37f40a6fbb0bf073ddefc5e4154044fb591aad78e699c275ec860b120fdbc`. See `horizons.{12,24}` for denominators, intervals and class/action counts.

The first run completed all predeclared endpoints. B1's low 12-month recall prompted a second run adding native-B1 ranking and TRAIN slope diagnostics. Its negative TRAIN slope explained the reversed queue. This follow-up was selected after development scoring. Both runs passed the entry and exit seal checks. The 2,000 paired draws had zero undefined draws per horizon. Independent arithmetic checks reconciled row and event totals by action, capture from both recall and precision, per-row loss and every predeclared contrast. A hand-checkable five-row fixture passed fractional boundary ties, AP and repeated-drug weights. No executable repository module changed. Full repository pytest was not run on this documentation card.

Inputs are identified by base revision above and the following LF SHA-256 values. Exact source file identities and locators are in the linked manifests.

| Evidence | SHA-256 |
|---|---|
| [K20T1, horizons / arms / calibrator](../../../loe-bench/data/K20T1_frozen_config.json) | `880c3293b8e4250c2bea7c22c73fa4e5e3111362b8ee1afa1bd165d15b2b0ee1` |
| [S0, files / raw_file / sha256](../../../loe-bench/data/S0_INPUT_MANIFEST.json) | `7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d` |
| [Historical Orange Book editions](../../../loe-bench/data/OB_EDITIONS.json) | `6b59c08899ab4b5b7c514544e5c9aebcf93fd6775a61502f25f9086a41e77103` |
| [PIV editions](../../../loe-bench/data/PIV_EDITIONS.json) | `f99562f2dd3344279ff788a20fae836cacc6c0acc87b540d0e94984175bc8352` |
| [E7, rai and corroborating_documents](../../../loe-bench/data/E7_sources.json) | `c2e7ad988d860fb684cffffb4607ba1d1aca575f8209e4fc18d8ee47d3709c6f` |

Main planner reviews the proposed estimand, comparator correction and three-action gates with the owner before assigning T1 and T4. T5 and confirmatory scoring remain pending.

Both cited papers were opened on 27 November 2026. For Saito and Rehmsmeier the publisher printable PDF SHA-256 was `8ae56333b46ffae705ec463b6a3dd1d81bc4fe5934e5e13a635e4bbf401d1a97` (Fig. 2B and the PRC baseline subsection). For Traub et al. the proceedings abstract HTML SHA-256 was `13002b9bb8f96af7a493ae1cf6604c47649ff143cbd3ed98d61d1b9a1c84ca56`. The proceedings PDF was also opened at Fig. 1 and §2.2. A bounded local PDF download timed out after 159,648 bytes and supplied no file digest. The full publisher download completed separately (2,523,391 bytes), SHA-256 2b5e3115c34a9c05d737306cfdd337297709b29e9052841812f753835124bc7c. [PLOS printable edition](https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0118432&type=printable) · [NeurIPS publication record](https://proceedings.neurips.cc/paper_files/paper/2024/hash/047c84ec50bd8ea29349b996fc64af4b-Abstract-Conference.html)

```powershell
rtk proxy python -B -c "from pathlib import Path; s=Path('docs/loe-bench/receipts/CP4.md').read_text(encoding='utf-8'); f=chr(96)*3; exec(s.split(f+'python\n')[1].split(f)[0])"
```

Run the Python block below from the repository root with Python in no-bytecode mode. It writes one aggregate JSON file. Inputs and verification hooks are those of the merged K20T1 runner.

```python
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path("loe-bench/scripts").resolve()))
import k20t1_run as pipeline
import numpy as np
from loe_bench.baselines import AgeHazardTable, Logistic

r = pipeline.replay
assert not r.LOCK_PATH.exists() and r.ENV_NAME not in os.environ
assert r.DEVELOPMENT_END.isoformat() == "2016-01-01"
ob = Path(r.DEFAULT_DIR)
base = ob.parent
entities, builder, _ = r.inputs(base / "raw-20261127", ob, base / "piv", base / "challenge")
config = json.loads((pipeline.ROOT / "data/K20T1_frozen_config.json").read_text())
arms = ("B1", "M1", "M3")

def bins(score):
    levels, ascending = np.unique(score, return_inverse=True)
    return len(levels) - 1 - ascending

def evaluate(layout, y, loss, w):
    allbins, groups = layout
    positive = w * y
    ne = positive.sum()
    sizes = np.bincount(allbins, weights=w)
    events = np.bincount(allbins, weights=positive)
    precision = events.cumsum() / np.maximum(1, sizes.cumsum())
    captured = slots = 0
    for idx, rank in groups:
        size = np.bincount(rank, weights=w[idx])
        hits = np.bincount(rank, weights=positive[idx])
        k = int(size.sum()) // 5
        fraction = np.clip(k - size.cumsum() + size, 0, size) / np.maximum(size, 1)
        captured += hits @ fraction
        slots += k
    return [captured / ne if ne else np.nan, captured / slots if slots else np.nan,
            events @ precision / ne if ne else np.nan, w @ loss / w.sum()]

def calibration(train, h, name):
    fit = Logistic(feats=("logit",))
    if name == "B1":
        folds = np.array([pipeline.t2._fold(row["key"]) for row in train])
        oof = np.empty(len(train))
        for fold in np.unique(folds):
            held = folds == fold
            model = AgeHazardTable().fit([row for i,row in enumerate(train) if not held[i]])
            oof[held] = model.predict([row for i,row in enumerate(train) if held[i]])
        return fit.fit(pipeline.t2._with_labels(pipeline.calibrator_inputs(oof), train))
    pars = config["horizons"][str(h)]["arms"][name]["calibrator"]
    fit.mu, fit.sd, fit.w, fit.b = [pars["mean"]], [pars["scale"]], [pars["weight"]], pars["intercept"]
    return fit

def interval(points, samples):
    return [[float(x), *np.nanpercentile(s, [2.5,97.5]).tolist()] for x,s in zip(points,samples.T)]

out = {"role":"DEVELOPMENT_ONLY", "metric_order":["recall20","precision20","AP","loss"], "horizons":{}}
for h,(td, vd) in r.PRIMARY.items():
    pipeline.verify_windows(td, vd, h)
    pipeline.t2.require_development_cutoffs([*td,*vd])
    assert len(td) == 1
    train = r.partition(entities,builder,td,h,training=True)
    val = r.partition(entities,builder,vd,h)
    models, age = pipeline.devx.raw_predictions(train,val,h,pipeline.FLAGS,min(vd)-timedelta(days=1))
    models["B1"] = age
    ids, groups = np.unique([row["key"] for row in val], return_inverse=True)
    times = np.array([row["t"] for row in val])
    y = np.array([row["y"] for row in val])
    blocked = np.array([row["asof"].verdict == "BLOCKED" for row in val])
    layouts, losses, counts, slopes = [], [], {}, {}
    for arm in arms:
        sigmoid = calibration(train,h,arm)
        slopes[arm] = sigmoid.w[0]
        p = np.array(sigmoid.predict(pipeline.calibrator_inputs(models[arm])))
        by_date = []
        for day in vd:
            idx = np.flatnonzero(times == day)
            by_date.append((idx, bins(p[idx])))
        layouts.append((bins(p),by_date))
        override = blocked & (arm == "M3")
        flag = (p >= .5) & ~override
        clear = (p <= .05) | (override & (p < .5))
        refer = ~(clear | flag)
        losses.append(10*(clear*y) + flag*(1-y) + .5*refer)
        counts[arm] = {action:[int(mask.sum()),int(y[mask].sum())] for action,mask in
                       [("clear",clear),("flag",flag),("refer",refer)]}
    def score(weights):
        return np.array([evaluate(layout,y,loss,weights) for layout,loss in zip(layouts,losses)])
    point = score(np.ones(len(val)))
    rng = np.random.default_rng(20261127)
    samples = np.array([score(np.bincount(rng.integers(len(ids),size=len(ids)),minlength=len(ids))[groups])
                        for _ in range(2000)])
    result = {"levels":{}, "differences":{}, "action_rows_and_events":counts,
              "rows":len(y), "events":int(y.sum()), "drugs":len(ids),
              "event_drugs":len(np.unique(groups[y==1])),
              "slots":sum(int((times==d).sum())//5 for d in vd),
              "invalid_draws":int((~np.isfinite(samples).all(axis=(1,2))).sum())}
    for j,arm in enumerate(arms):
        result["levels"][arm] = interval(point[j],samples[:,j])
    for j,k in [(2,0),(2,1),(1,0)]:
        result["differences"][arms[j]+"-"+arms[k]] = interval(point[j]-point[k],samples[:,j]-samples[:,k])
    # Follow-up diagnostic after observing B1's low 12-month recall.
    # Replay the same draws and compare M3 against B1's native hazard ordering.
    native = np.asarray(age)
    raw_layout = (bins(native), [(idx,bins(native[idx])) for idx,_ in layouts[0][1]])
    def raw_rank(weights):
        return np.array(evaluate(raw_layout,y,losses[0],weights)[:3])
    raw_point = raw_rank(np.ones(len(val)))
    rng = np.random.default_rng(20261127)
    raw_draws = np.array([raw_rank(np.bincount(rng.integers(len(ids),size=len(ids)),minlength=len(ids))[groups])
                          for _ in range(2000)])
    result["train_sigmoid_standardized_slopes"] = slopes
    result["native_B1_ranking_sensitivity"] = interval(raw_point,raw_draws)
    result["M3_minus_native_B1_ranking_sensitivity"] = interval(point[2,:3]-raw_point,samples[:,2,:3]-raw_draws)
    out["horizons"][str(h)] = result
assert not r.LOCK_PATH.exists() and r.ENV_NAME not in os.environ
(pipeline.ROOT/"data/CP4_validation.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
```
