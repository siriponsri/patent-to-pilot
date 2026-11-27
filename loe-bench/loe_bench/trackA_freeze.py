"""Freeze Track A predictions from a verified S0 input snapshot.

The caller supplies the exact arm list. The CLI exposes implemented baselines.
Use freeze_predictions to supply additional arms once their methods are locked.
The prediction file and its digest can then be externally timestamped.
"""
import argparse
import csv
import hashlib
import json
import math
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .baselines import AgeHazardTable, BaseRate, Logistic, exclusivity_rule_score
from .dataset import build_entities, build_samples, features_at, snapshot_features

REQUIRED_INPUTS = {"df_nda.jsonl", "df_anda.jsonl", "ob_nda.jsonl"}
ROW_FIELDS = ("entity", "t0", "horizon_months")
ArmPredictor = Callable[[list, list, date, int], Sequence[float]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_manifest(raw: Path, manifest: Path, t0: date, out: Path) -> date:
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        snapshot_date = date.fromisoformat(payload["t0"])
        fetched_date = snapshot_date
        if "fetched_at_utc" in payload:
            fetched = datetime.fromisoformat(payload["fetched_at_utc"])
            if fetched.utcoffset() is None:
                raise ValueError("fetched_at_utc must include a timezone")
            fetched_date = fetched.astimezone(timezone.utc).date()
        entries = payload["files"]
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid S0 input manifest: {exc}") from exc
    if max(snapshot_date, fetched_date) > t0:
        raise ValueError("S0 input manifest or fetch date is after t0")
    if not isinstance(entries, list):
        raise ValueError("invalid S0 input manifest files list")
    if out.resolve() == manifest.resolve():
        raise ValueError("prediction output must differ from the S0 manifest")

    seen = set()
    present = set()
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError("invalid S0 manifest file entry")
        name, expected = item.get("raw_file"), item.get("sha256")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", name):
            raise ValueError("invalid S0 manifest raw_file")
        if name.casefold() in seen:
            raise ValueError(f"duplicate S0 manifest file: {name}")
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
            raise ValueError(f"invalid SHA-256 for {name}")
        path = raw / name
        if path.resolve().parent != raw.resolve() or path.is_symlink():
            raise ValueError(f"S0 input must be a file inside the raw directory: {name}")
        if out.resolve() == path.resolve():
            raise ValueError("prediction output must differ from S0 inputs")
        try:
            actual = _sha256(path)
        except OSError as exc:
            raise ValueError(f"cannot read S0 input: {name}") from exc
        if actual != expected.lower():
            raise ValueError(f"S0 input SHA-256 mismatch: {name}")
        seen.add(name.casefold())
        present.add(name)
    missing = REQUIRED_INPUTS - present
    if missing:
        raise ValueError(f"S0 manifest is missing required input: {', '.join(sorted(missing))}")
    return min(snapshot_date, fetched_date, t0)


def _model_predictor(model_factory) -> ArmPredictor:
    def predict(train, rows, _t, _h):
        if not train:
            raise ValueError("model fit requires at least one fully observed training row")
        return model_factory().fit(train).predict(rows)
    return predict


def _rule_predict(train, rows, t, h):
    return [exclusivity_rule_score(row["snapshot"], t, h) for row in rows]


BASELINE_ARMS = {
    "B0": _model_predictor(BaseRate),
    "B1": _model_predictor(AgeHazardTable),
    "B2": _model_predictor(Logistic),
    "B3": _rule_predict,
}


def freeze_predictions(raw: Path, manifest: Path, out: Path, t0: date,
                       arm_predictors: Mapping[str, ArmPredictor]) -> tuple[int, str]:
    """Write one probability column per declared arm, in the supplied order.

    Each predictor receives fully observed training rows, unlabelled prediction
    rows with S0 evidence, the freeze date and the horizon in months.
    """
    raw, manifest, out = Path(raw), Path(manifest), Path(out)
    data_end = _verify_manifest(raw, manifest, t0, out)
    if not arm_predictors or any(not name or name in ROW_FIELDS for name in arm_predictors):
        raise ValueError("declare at least one arm with a distinct non-reserved name")
    ents = build_entities(raw)
    snaps = snapshot_features(raw, t0, ents)
    rows = [{"key": key, "x": features_at(ents[key], t0), "snapshot": snap}
            for key, snap in sorted(snaps.items()) if ents[key].flag_at("nme", t0)]
    cutoffs = [date(year, 1, 1) for year in range(1995, data_end.year + 1)]
    output = []
    for h in (12, 24, 36):
        if not rows:
            break
        train = build_samples(ents, cutoffs, h, data_end, only_nme=True)
        predicted = {}
        for name, predictor in arm_predictors.items():
            probabilities = list(predictor(train, rows, t0, h))
            if len(probabilities) != len(rows) or any(
                isinstance(p, bool) or not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities
            ):
                raise ValueError(f"{name} must return one probability in [0, 1] per row")
            predicted[name] = [float(p) for p in probabilities]
        for i, row in enumerate(rows):
            output.append({"entity": row["key"], "t0": t0.isoformat(), "horizon_months": h,
                           **{name: probabilities[i] for name, probabilities in predicted.items()}})
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", dir=out.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=[*ROW_FIELDS, *arm_predictors])
            writer.writeheader()
            writer.writerows(output)
        digest = _sha256(temporary)
        temporary.replace(out)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return len(output), digest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path("data/raw"))
    ap.add_argument("--manifest", type=Path, default=Path("data/S0_INPUT_MANIFEST.json"))
    ap.add_argument("--out", type=Path, default=Path("data/trackA_S0.csv"))
    ap.add_argument("--t0", type=date.fromisoformat, required=True)
    ap.add_argument("--arm", action="append", choices=tuple(BASELINE_ARMS), required=True,
                    help="declared output arm; repeat in column order")
    args = ap.parse_args(argv)
    if len(set(args.arm)) != len(args.arm):
        ap.error("each arm must be declared once")
    try:
        count, digest = freeze_predictions(args.raw, args.manifest, args.out, args.t0,
                                            {name: BASELINE_ARMS[name] for name in args.arm})
    except ValueError as exc:
        ap.error(str(exc))
    print(f"wrote {count} rows to {args.out}\nsha256={digest}")


if __name__ == "__main__":
    main()
