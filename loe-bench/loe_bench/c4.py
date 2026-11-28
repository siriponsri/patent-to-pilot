"""C4 development-only Medicaid SDUD ingestion, forecasts and paired scoring."""

import argparse
import calendar
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path
from statistics import fmean

from .moiety import registry_for

AS_OF = "AS_OF_PROVEN"
RETROSPECTIVE = "RETROSPECTIVE_VINTAGE_UNCONTROLLED"
DEV_END = date(2017, 1, 1)
HISTORY = 8
HORIZON = 4
NDC11 = re.compile(r"[0-9]{11}")
SHA256 = re.compile(r"[a-f0-9]{64}")
TYPES = ("FFSU", "MCOU")
FIELDS = ("State", "NDC", "Year", "Quarter", "Utilization Type",
          "Suppression Used", "Number of Prescriptions")
REIMBURSEMENT_FIELD = "Total Amount Reimbursed"
USD = re.compile(r"([0-9]+)(?:\.([0-9]{1,2}))?")


def quarter(year, number):
    if not 1 <= number <= 4:
        raise ValueError(f"Invalid quarter {year}Q{number}")
    return 4 * year + number - 1


def quarter_label(value):
    year, index = divmod(value, 4)
    return f"{year}Q{index + 1}"


def quarter_end(value):
    year, index = divmod(value, 4)
    month = 3 * (index + 1)
    return date(year, month, calendar.monthrange(year, month)[1])


def dev_origin(value):
    if value >= DEV_END:
        raise ValueError("C4 development origin must precede 2017-01-01")
    index = quarter(value.year, (value.month + 2) // 3)
    if value != quarter_end(index):
        raise ValueError("C4 origins must be calendar quarter ends")
    return index


def package_ndc11(value):
    parts = value.split("-")
    widths = tuple(map(len, parts))
    if widths not in {(4, 4, 2), (5, 3, 2), (5, 4, 1), (5, 4, 2)}:
        return None
    padded = "".join(part.zfill(width) for part, width in zip(parts, (5, 4, 2)))
    return padded if NDC11.fullmatch(padded) else None


def ingredient_name(value):
    return " ".join(value.upper().split())


@dataclass(frozen=True)
class Package:
    ingredients: frozenset[str]
    first_listed: date


def build_crosswalk(products):
    """Resolve exact package NDCs and quarantine missing or conflicting identities."""
    candidates = defaultdict(dict)
    invalid = set()
    for product in products:
        names = [ingredient_name(row.get("name") or "")
                 for row in product.get("active_ingredients") or []]
        ingredients = frozenset(names)
        for item in product.get("packaging") or []:
            ndc = package_ndc11(item.get("package_ndc") or "")
            if ndc is None:
                continue
            starts = (product.get("marketing_start_date"), item.get("marketing_start_date"))
            try:
                start = max(datetime.strptime(value, "%Y%m%d").date()
                            for value in starts if value)
            except ValueError:
                invalid.add(ndc)
                continue
            if not ingredients or "" in ingredients:
                invalid.add(ndc)
                continue
            by_identity = candidates[ndc]
            by_identity[ingredients] = min(start, by_identity.get(ingredients, start))
    return {ndc: Package(*next(iter(choices.items())))
            for ndc, choices in candidates.items() if len(choices) == 1 and ndc not in invalid}


def load_crosswalk(path, member, expected_vintage):
    with zipfile.ZipFile(path) as archive, archive.open(member) as stream:
        data = json.load(stream)
    if data["meta"]["last_updated"] != expected_vintage:
        raise ValueError(f"Crosswalk vintage mismatch in {path.name}")
    return build_crosswalk(data["results"])


@dataclass
class DrugQuarter:
    national: dict[str, tuple[int | None, str]] = field(default_factory=dict)
    state_types: set[str] = field(default_factory=set)
    suppressed_rows: int = 0
    national_rows: int = 0
    reimbursed_cents: dict[str, int | None] = field(default_factory=dict)


def parse_count(flag, count):
    flag, count = flag.strip().lower(), count.strip()
    if flag in {"true", "1", "y", "yes", "*"} or count == "*":
        return None, "suppressed"
    if flag in {"false", "0", "n", "no"} and re.fullmatch(r"[0-9]+", count):
        return int(count), "known"
    return None, "unknown_count"


def parse_reimbursement(flag, amount):
    match = USD.fullmatch(amount.strip())
    if flag.strip().lower() not in {"false", "0", "n", "no"} or match is None:
        return None
    return 100 * int(match[1]) + int((match[2] or "0").ljust(2, "0"))


def read_sdud(path, year, *, include_reimbursement=False):
    """Use XX values only. State rows supply evidence that a package/type exists."""
    quarters = defaultdict(dict)
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = [name.strip() for name in next(reader)]
        state_i, ndc_i, year_i, q_i, type_i, flag_i, count_i = [
            header.index(name) for name in FIELDS
        ]
        amount_i = header.index(REIMBURSEMENT_FIELD) if include_reimbursement else None
        for row in reader:
            if len(row) != len(header) or row[year_i] != str(year):
                raise ValueError(f"{path.name}:{reader.line_num}: invalid row or year")
            value = quarter(year, int(row[q_i]))
            ndc, kind = row[ndc_i].strip(), row[type_i].strip().upper()
            by_ndc = quarters[value]
            if ndc not in by_ndc:
                by_ndc[ndc] = DrugQuarter()
            drug = by_ndc[ndc]
            if row[state_i].strip().upper() != "XX":
                drug.state_types.add(kind)
                continue
            count, status = parse_count(row[flag_i], row[count_i])
            drug.national_rows += 1
            drug.suppressed_rows += status == "suppressed"
            if kind in drug.national:
                drug.national[kind] = (None, "duplicate_national_key")
                if include_reimbursement:
                    drug.reimbursed_cents[kind] = None
            else:
                drug.national[kind] = (count, status)
                if include_reimbursement and status != "suppressed":
                    drug.reimbursed_cents[kind] = parse_reimbursement(row[flag_i], row[amount_i])
    return quarters


@dataclass
class IngredientQuarter:
    counts: dict[str, int | None] = field(default_factory=dict)
    issues: Counter = field(default_factory=Counter)
    reimbursed_cents: dict[str, int | None] = field(default_factory=dict)
    mapped_packages: Counter = field(default_factory=Counter)
    count_complete_packages: Counter = field(default_factory=Counter)
    amount_complete_packages: Counter = field(default_factory=Counter)
    joint_complete_packages: Counter = field(default_factory=Counter)

    @property
    def frame_complete(self):
        return bool(self.issues["national_rows"]) and not self.issues["unresolved_packages"]


def aggregate(period, rows, crosswalk, *, include_reimbursement=False):
    result = IngredientQuarter()
    totals = Counter()
    incomplete = set()
    amounts = Counter()
    incomplete_amount = set()
    required = set(TYPES if period >= quarter(2010, 1) else TYPES[:1])
    end = quarter_end(period)
    for ndc, drug in rows.items():
        result.issues["packages"] += 1
        result.issues["national_rows"] += drug.national_rows
        result.issues["suppressed_national_rows"] += drug.suppressed_rows
        package = crosswalk.get(ndc) if NDC11.fullmatch(ndc) else None
        if package is None or package.first_listed > end:
            result.issues["unresolved_packages"] += 1
            if not NDC11.fullmatch(ndc):
                result.issues["invalid_ndc11"] += 1
            continue
        structural_problems = set()
        if (drug.national.keys() | drug.state_types) - required:
            structural_problems.add("unexpected_utilization_type")
        if required - drug.national.keys():
            structural_problems.add("missing_national_type")
        if not drug.national:
            structural_problems.add("state_only_package")
        problems = structural_problems | ({status for _, status in drug.national.values()} - {"known"})
        if problems:
            result.issues.update(problems)
            incomplete.update(package.ingredients)
        else:
            count = sum(drug.national[kind][0] for kind in required)
            totals.update({ingredient: count for ingredient in package.ingredients})
        if include_reimbursement:
            reported = [drug.reimbursed_cents.get(kind) for kind in required]
            result.mapped_packages.update(package.ingredients)
            if not problems:
                result.count_complete_packages.update(package.ingredients)
            if structural_problems or None in reported:
                incomplete_amount.update(package.ingredients)
            else:
                result.amount_complete_packages.update(package.ingredients)
                if not problems:
                    result.joint_complete_packages.update(package.ingredients)
                amounts.update({ingredient: sum(reported) for ingredient in package.ingredients})
    result.counts = dict(totals)
    result.counts.update(dict.fromkeys(incomplete))
    result.reimbursed_cents = dict(amounts)
    result.reimbursed_cents.update(dict.fromkeys(incomplete_amount))
    return result


def project_quarters(history, lag):
    if len(history) != HISTORY or any(value is None or value < 0 for value in history):
        raise ValueError("Forecast requires eight consecutive observed nonnegative counts")
    if lag < 0:
        raise ValueError("Forecast anchor must not follow the origin")
    slope = (history[-1] - history[0]) / (HISTORY - 1)
    return {
        "carry_forward": [history[-1]] * HORIZON,
        "drift": [max(0, history[-1] + step * slope)
                  for step in range(lag + 1, lag + HORIZON + 1)],
    }


def forecast(history, lag):
    return {arm: sum(values) for arm, values in project_quarters(history, lag).items()}


def score_origin(origin, anchor, training, outcomes):
    """Pair annual errors. The mapped-only diagnostic cannot certify the full frame."""
    origin = dev_origin(origin)
    if anchor > origin:
        raise ValueError("Training anchor follows the forecast origin")
    fit_quarters = range(anchor - HISTORY + 1, anchor + 1)
    target_quarters = range(origin + 1, origin + HORIZON + 1)
    fit = [training.get(value, IngredientQuarter()) for value in fit_quarters]
    target = [outcomes.get(value, IngredientQuarter()) for value in target_quarters]
    ingredients = set().union(*(item.counts for item in fit))
    complete_frame = all(item.frame_complete for item in fit + target)
    primary, diagnostic, missing = [], [], Counter()
    for ingredient in sorted(ingredients):
        history = [item.counts.get(ingredient) for item in fit]
        actual = [item.counts.get(ingredient) for item in target]
        if None in history:
            missing["incomplete_history"] += 1
        elif None in actual:
            missing["incomplete_outcome"] += 1
        else:
            predicted = forecast(history, origin - anchor)
            row = (ingredient, predicted["carry_forward"] - sum(actual), predicted["drift"] - sum(actual))
            diagnostic.append(row)
            if complete_frame:
                primary.append(row)
    return ingredients, primary, diagnostic, dict(missing)


def metrics(rows):
    if not rows:
        return {"status": "NOT_ESTIMABLE", "paired_rows": 0, "ingredients": 0}
    return {
        "status": "ESTIMATED",
        "paired_rows": len(rows),
        "ingredients": len({row[0] for row in rows}),
        "carry_forward_mae": fmean(abs(row[1]) for row in rows),
        "drift_mae": fmean(abs(row[2]) for row in rows),
        "paired_mae_difference_drift_minus_carry": fmean(abs(row[2]) - abs(row[1]) for row in rows),
        "carry_forward_bias": fmean(row[1] for row in rows),
        "drift_bias": fmean(row[2] for row in rows),
    }


def coverage(periods, series):
    info = Counter(packages=0, unresolved_packages=0, national_rows=0, suppressed_national_rows=0)
    for value in periods:
        info.update(series.get(value, IngredientQuarter()).issues)
    info["quarters"] = len(periods)
    info["quarters_with_national_rows"] = sum(
        bool(series.get(value, IngredientQuarter()).issues["national_rows"]) for value in periods
    )
    info["complete_frame_quarters"] = sum(
        series.get(value, IngredientQuarter()).frame_complete for value in periods
    )
    return dict(info)


def verify_file(path, expected):
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch: {path.name}")
    return path


def lock_bytes(path):
    """Use the Git blob's LF convention for tracked locks on Windows checkouts."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def proven_before(record, origin):
    evidence = record.get("availability") or {}
    if (evidence.get("method") not in {"official_immutable_release", "archive_payload_replay"}
            or not evidence.get("url")
            or not SHA256.fullmatch(evidence.get("sha256") or "")
            or evidence["sha256"] != record["sha256"]
            or not evidence.get("available_utc")):
        return False
    timestamp = datetime.fromisoformat(evidence["available_utc"])
    return (timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)
            and timestamp.date() < origin)


def pilot_origins(spec, manifest):
    origins = {}
    for entry in manifest["origins"]:
        origin = date.fromisoformat(entry["origin"])
        index = dev_origin(origin)
        if index in origins:
            raise ValueError("Duplicate C4 origin")
        if entry["verdict"] not in {AS_OF, RETROSPECTIVE}:
            raise ValueError("Unknown C4 vintage verdict")
        origins[index] = entry
    if list(origins) != [dev_origin(date.fromisoformat(value)) for value in spec["development_origins"]]:
        raise ValueError("Origin manifest differs from the frozen C4 protocol")
    return origins


def pilot_windows(spec, manifest, root, *, include_reimbursement=False):
    # Validate every origin before opening any SDUD or FDA payload.
    origins = pilot_origins(spec, manifest)
    files = manifest["files"]
    outcome_lock = manifest["outcome_freeze"]

    @lru_cache(maxsize=None)
    def checked(file_id):
        record = files[file_id]
        name = record["file"]
        if Path(name).name != name:
            raise ValueError("C4 manifest files must be flat names under the input directory")
        return verify_file(root / name, record["sha256"])

    @lru_cache(maxsize=None)
    def quarter_series(file_id, map_id):
        file = files[file_id]
        source = read_sdud(checked(file_id), file["year"], include_reimbursement=include_reimbursement)
        return {period: aggregate(period, rows, crosswalk(map_id),
                                  include_reimbursement=include_reimbursement)
                for period, rows in source.items()}

    @lru_cache(maxsize=None)
    def crosswalk(file_id):
        record = files[file_id]
        return load_crosswalk(checked(file_id), record["member"], record["vintage"])

    def series(periods, year_files, map_id):
        return {period: quarter_series(year_files[str(period // 4)], map_id)[period]
                for period in periods
                if str(period // 4) in year_files
                and period in quarter_series(year_files[str(period // 4)], map_id)}

    for index, entry in origins.items():
        origin = date.fromisoformat(entry["origin"])
        verdict = entry["verdict"]
        anchor = quarter(*entry["last_fit_quarter"])
        if anchor > index:
            raise ValueError("Training anchor follows the forecast origin")
        fit_periods = range(anchor - HISTORY + 1, anchor + 1)
        target_periods = range(index + 1, index + HORIZON + 1)
        if verdict == AS_OF:
            years = {str(period // 4) for period in fit_periods}
            if not years <= entry["training_files"].keys():
                raise ValueError("Missing as-of training release")
            input_ids = [entry["crosswalk"], *(entry["training_files"][year] for year in years)]
            if not all(proven_before(files[file_id], origin) for file_id in input_ids):
                raise ValueError("AS_OF_PROVEN requires pre-origin proofs for SDUD and crosswalk bytes")
        fit = series(fit_periods, entry["training_files"], entry["crosswalk"])
        target = series(target_periods, outcome_lock["files"], outcome_lock["crosswalk"])
        yield origin, verdict, anchor, fit, target


def run_pilot(spec, manifest, root, registry):
    by_vintage = {verdict: {"origins": []} for verdict in (AS_OF, RETROSPECTIVE)}
    pooled = defaultdict(list)
    all_ingredients, paired = set(), set()
    for origin, verdict, anchor, fit, target in pilot_windows(spec, manifest, root):
        index = dev_origin(origin)
        fit_periods = range(anchor - HISTORY + 1, anchor + 1)
        target_periods = range(index + 1, index + HORIZON + 1)
        ingredients, primary, diagnostic, missing = score_origin(origin, anchor, fit, target)
        pooled[verdict, "primary"].extend(primary)
        pooled[verdict, "mapped_diagnostic"].extend(diagnostic)
        all_ingredients.update(ingredients)
        paired.update(row[0] for row in diagnostic)
        by_vintage[verdict]["origins"].append({
            "origin": origin.isoformat(),
            "last_fit_quarter": quarter_label(anchor),
            "candidate_ingredients": len(ingredients),
            "exclusions": missing,
            "training_coverage": coverage(fit_periods, fit),
            "outcome_coverage": coverage(target_periods, target),
            "primary": metrics(primary),
            "mapped_diagnostic": metrics(diagnostic),
        })
    for verdict, table in by_vintage.items():
        for role in ("primary", "mapped_diagnostic"):
            table[role] = metrics(pooled[verdict, role])
            if not table["origins"]:
                table[role]["status"] = "NOT_RUN"
            table[role]["evaluable_origins"] = sum(
                bool(origin[role]["paired_rows"]) for origin in table["origins"]
            )
    links = {}
    for name in sorted(all_ingredients):
        composition = registry.composition([name])
        if composition.parts and not composition.low_confidence:
            links[name] = composition.key
    return {
        "scope": "DEVELOPMENT_ONLY",
        "by_vintage": by_vintage,
        "linkage": {
            "candidates": len(all_ingredients),
            "linked_candidates": len(links),
            "paired_diagnostic_ingredients": len(paired),
            "linked_paired_diagnostic_ingredients": len(paired & links.keys()),
        },
    }, links


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--gsrs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--links-out", type=Path, required=True)
    args = parser.parse_args()
    spec_bytes = lock_bytes(args.spec)
    spec = json.loads(spec_bytes)
    if spec["protocol_version"] != "C4-v1":
        parser.error("C4 v2 uses python -m loe_bench.c4b")
    manifest_bytes = lock_bytes(args.inputs)
    if hashlib.sha256(manifest_bytes).hexdigest() != spec["input_manifest_sha256"]:
        raise ValueError("C4 input manifest SHA-256 mismatch")
    verify_file(args.gsrs, spec["gsrs_sha256"])
    manifest = json.loads(manifest_bytes)
    report, links = run_pilot(spec, manifest, args.raw_dir, registry_for(args.raw_dir, args.gsrs))
    report["spec_sha256"] = hashlib.sha256(spec_bytes).hexdigest()
    report["input_manifest_sha256"] = spec["input_manifest_sha256"]
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
    args.links_out.write_text(json.dumps(links, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
