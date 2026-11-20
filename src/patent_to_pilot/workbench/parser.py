"""Bounded field grammar for the authored G01 fixture (parser profile ``authored_fixture_fields_v1``).

The grammar recognizes exactly three explicit fields. It is not general natural-language entailment:

- ``Powered circulation: yes.`` or ``Powered circulation: no.``
- ``Supported temperature range: <number> to <number> °C.``
- ``Independent module replacement: yes.`` or ``Independent module replacement: no.``

A line that starts with a field label but does not follow the grammar is reported as ``invalid`` with a
validation issue (for example a missing unit, an unknown value or a lower bound above the upper bound).
Nothing is guessed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re

PARSER_PROFILE = "authored_fixture_fields_v1"

FIELD_LABELS = {
    "powered_circulation": "Powered circulation",
    "supported_temperature_range": "Supported temperature range",
    "independent_module_replacement": "Independent module replacement",
}
_BOOL = re.compile(r"^(?P<label>[A-Za-z ]+): (?P<value>yes|no)\.$")
_NUM = r"(-?\d+(?:\.\d+)?)"
_RANGE = re.compile(rf"^Supported temperature range: {_NUM} to {_NUM} (?P<unit>°C|℃)\.$")
UNIT_CANONICAL = {"°C": "degC", "℃": "degC"}


@dataclass
class FieldReading:
    """Result of reading one passage for one field."""

    field: str
    status: str                       # "parsed" | "absent" | "invalid"
    value: object = None              # bool for Boolean fields; {"low","high","unit"} for ranges
    line: str | None = None           # the literal source line that carried the field
    line_start: int | None = None     # offset of that line inside the passage (code points)
    issues: list[str] = field(default_factory=list)


def _num(text: str) -> float | int:
    v = float(text)
    return int(v) if v.is_integer() else v


def read_field(passage: str, field_name: str) -> FieldReading:
    label = FIELD_LABELS[field_name]
    offset = 0
    found: FieldReading | None = None
    for raw_line in passage.split("\n"):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        start = offset
        offset += len(raw_line) + 1
        if not line.startswith(label + ":"):
            continue
        if found is not None:
            return FieldReading(field_name, "invalid", line=line, line_start=start,
                                issues=[f"passage states '{label}' more than once"])
        if field_name == "supported_temperature_range":
            m = _RANGE.match(line)
            if not m:
                found = FieldReading(field_name, "invalid", line=line, line_start=start,
                                     issues=["temperature range does not match '<number> to <number> °C.' "
                                             "(missing or unrecognized unit, or malformed numbers)"])
                continue
            low, high = _num(m.group(1)), _num(m.group(2))
            if low > high:
                found = FieldReading(field_name, "invalid", line=line, line_start=start,
                                     issues=[f"lower bound {low} exceeds upper bound {high}"])
                continue
            found = FieldReading(field_name, "parsed", {"low": low, "high": high,
                                                        "unit": UNIT_CANONICAL[m.group("unit")]},
                                 line=line, line_start=start)
        else:
            m = _BOOL.match(line)
            if not m or m.group("label") != label:
                found = FieldReading(field_name, "invalid", line=line, line_start=start,
                                     issues=[f"'{label}' value is not 'yes.' or 'no.'"])
                continue
            found = FieldReading(field_name, "parsed", m.group("value") == "yes", line=line, line_start=start)
    return found or FieldReading(field_name, "absent")


def fmt_num(v) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def evaluate(predicate: dict, reading: FieldReading) -> tuple[str, str]:
    """Return (outcome, explanation) for a parsed reading. Outcomes: meets | does_not_meet."""
    op = predicate["operator"]
    if op == "equals":
        want = predicate["value"]
        got = reading.value
        word = "yes" if got else "no"
        label = FIELD_LABELS[reading.field].lower()
        if got == want:
            return "meets", f"Source states {label}: {word}, as the requirement asks."
        return "does_not_meet", (f"Source states {label}: {word}; the requirement needs "
                                 f"{'yes' if want else 'no'}.")
    if op == "contains_interval":
        if reading.value["unit"] != predicate["unit"]:
            raise ValueError(f"unit {reading.value['unit']} cannot be compared with {predicate['unit']}")
        lo, hi = reading.value["low"], reading.value["high"]
        mn, mx = predicate["minimum"], predicate["maximum"]
        stated = f"Source states {fmt_num(lo)}–{fmt_num(hi)} °C"
        gaps = []
        if lo > mn:
            gaps.append(f"starts at {fmt_num(mn)} °C")
        if hi < mx:
            gaps.append(f"extends to {fmt_num(mx)} °C")
        if not gaps:
            return "meets", f"{stated}, which covers the required {fmt_num(mn)}–{fmt_num(mx)} °C."
        return "does_not_meet", f"{stated}; the requirement {' and '.join(gaps)}."
    raise ValueError(f"unsupported predicate operator {op!r}")
