"""Shared helpers: date parsing, ingredient-key normalisation, JSONL IO."""
import json
import re
from datetime import date
from typing import Iterator, Optional

SALT_WORDS = {
    "HYDROCHLORIDE", "HCL", "SODIUM", "POTASSIUM", "CALCIUM", "MESYLATE", "MALEATE", "TARTRATE",
    "SUCCINATE", "SULFATE", "PHOSPHATE", "ACETATE", "BESYLATE", "FUMARATE", "CITRATE",
    "HYDROBROMIDE", "BROMIDE", "CHLORIDE", "NITRATE", "MAGNESIUM", "ANHYDROUS", "MONOHYDRATE",
    "DIHYDRATE", "HEMIHYDRATE", "TROMETHAMINE", "DISODIUM", "LACTATE", "GLUCONATE", "OXALATE",
}


def read_jsonl(path: str) -> Iterator[dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def parse_yyyymmdd(s) -> Optional[date]:
    """'20230428' -> date(2023,4,28); returns None for missing/invalid."""
    if not s or not isinstance(s, str) or not re.fullmatch(r"\d{8}", s):
        return None
    try:
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    except ValueError:
        return None


def years_between(a: date, b: date) -> float:
    return (b - a).days / 365.25


def add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def norm_ingredient(name: str) -> str:
    """Crude active-moiety key: uppercase, drop salt/hydrate words and non-letters.
    LIMITATION: not a true active-moiety mapping (documented in docs/04)."""
    toks = re.findall(r"[A-Z0-9\-]+", (name or "").upper())
    toks = [t for t in toks if t not in SALT_WORDS]
    return " ".join(toks)


def ingredient_key(products: list) -> str:
    """Union of normalised ingredients across the products of one record, sorted, joined by '|'."""
    names = set()
    for p in products or []:
        for ai in p.get("active_ingredients") or []:
            n = norm_ingredient(ai.get("name", ""))
            if n:
                names.add(n)
    return "|".join(sorted(names))
