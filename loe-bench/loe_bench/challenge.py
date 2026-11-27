"""Point-in-time challenge witnesses on FIX2c active-moiety keys."""
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from functools import lru_cache
from zipfile import BadZipFile
from xml.etree.ElementTree import ParseError
import re
import zlib

from .kleene import T3
from .moiety import name_form
from .piv_history import ingredient_names


@dataclass(frozen=True)
class Witness:
    source: str
    document_id: str
    date: date
    version: str
    sha256: str
    locator: str
    url: str
    corroboration: dict | None = None


@dataclass(frozen=True)
class ChallengeEvidence:
    state: T3
    witnesses: tuple[Witness, ...]


class ChallengeIdentity:
    """Resolve full compositions and dated exact brand aliases, without fuzzy matches."""

    def __init__(self, linker, brands):
        self.linker = linker
        self.brands = defaultdict(dict)
        for name, key, approved in brands:
            group = self.brands[name_form(name)]
            group[key] = min(approved, group.get(key, approved))

    def ingredient(self, names, cutoff):
        key = self.linker.canonical(self.linker.registry.composition(names).key)
        entity = self.linker.entities.get(key)
        return key if entity and entity.nda_first and entity.nda_first <= cutoff else None

    def piv_key(self, entry, cutoff):
        name = re.sub(r"\s*\bNEW\s*!\s*$", "", entry.ingredient, flags=re.I)
        # Try the whole name before splitting because individual names can contain punctuation.
        return self.ingredient((name,), cutoff) or self.ingredient(ingredient_names(name), cutoff)

    def court_key(self, brands, ingredients, cutoff):
        by_brand = {
            key for brand in brands.split(",")
            for key, approved in self.brands.get(name_form(brand), {}).items()
            if approved <= cutoff
        }
        by_ingredient = {
            key for product in ingredients.split(",")
            if (key := self.ingredient(product.split(";"), cutoff)) is not None
        }
        if by_brand and by_ingredient:
            candidates = by_brand & by_ingredient
        else:
            candidates = by_brand or by_ingredient
        return next(iter(candidates)) if len(candidates) == 1 else None


@dataclass(frozen=True)
class CourtRow:
    court: str
    docket: str
    filed: date
    brands: str
    ingredients: str
    locator: str


def court_rows(path, stop_before):
    """Read discovery fields only for cases filed before the supplied boundary."""
    with path.open(encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source, delimiter="\t")
        required = {"court", "civilaction", "filedon", "orangebookproducts", "orangebookingredients"}
        if not required.issubset(rows.fieldnames or ()):
            raise ValueError("unexpected Rai table fields")
        for row in rows:
            try:
                filed = datetime.strptime(row["filedon"], "%m/%d/%Y").date()
            except (ValueError, TypeError):
                continue
            if filed < stop_before and row["court"] and row["civilaction"]:
                yield CourtRow(row["court"], row["civilaction"], filed, row["orangebookproducts"],
                               row["orangebookingredients"], f"TSV line {rows.line_num}")


class ChallengeHistory:
    """Combine dated witnesses with the closed-world rule for a verified fresh FDA list."""

    def __init__(self, piv, identity, court, rai_source, corroboration):
        self.piv = piv
        self.identity = identity
        self.court = tuple(court)
        self.rai_source = rai_source
        self.corroboration = {(r["court"], r["docket"], date.fromisoformat(r["filed"])): r
                              for r in corroboration}

    @lru_cache(maxsize=16)
    def _piv(self, cutoff):
        edition = self.piv.edition_asof(cutoff)
        witnesses = defaultdict(list)
        if edition is None:
            return witnesses, {"status": "NO_FRESH_EDITION"}
        source = {
            "version": edition.version_date.isoformat(), "captured": edition.wayback_timestamp,
            "sha256": edition.sha256, "file": edition.file, "url": edition.source_url,
            "wayback_url": f"https://web.archive.org/web/{edition.wayback_timestamp}id_/{edition.source_url}",
        }
        try:
            rows = self.piv.entries(edition)
        except (OSError, ValueError, KeyError, IndexError, BadZipFile, ParseError, zlib.error) as exc:
            return witnesses, {"status": "UNVERIFIED", "edition": source, "error": type(exc).__name__}
        counts = Counter({"rows": len(rows), "matched_rows": 0, "dated_witness_rows": 0})
        examples = []
        for row in rows:
            key = self.identity.piv_key(row, cutoff)
            if key is None:
                if len(examples) < 5:
                    examples.append({"ingredient": row.ingredient, "form": row.dosage_form,
                                     "locator": row.locator})
                continue
            counts["matched_rows"] += 1
            if row.first_submission and row.first_submission <= cutoff:
                counts["dated_witness_rows"] += 1
                witnesses[key].append(Witness(
                    "FDA_PIV", edition.file, row.first_submission, source["version"],
                    edition.sha256, row.locator, source["wayback_url"],
                ))
        return witnesses, {"status": "FRESH", "edition": source, **counts,
                           "match_rate": counts["matched_rows"] / len(rows) if rows else None,
                           "unmatched_examples": examples}

    @lru_cache(maxsize=16)
    def _rai(self, cutoff):
        witnesses = defaultdict(list)
        counts = Counter(dict(rows=0, matched_rows=0, corroborated_rows=0, admitted_rows=0))
        examples = []
        cases = defaultdict(list)
        for row in self.court:
            if row.filed > cutoff:
                continue
            counts["rows"] += 1
            key = self.identity.court_key(row.brands, row.ingredients, cutoff)
            if key:
                counts["matched_rows"] += 1
            elif len(examples) < 5:
                examples.append({field: getattr(row, field)
                                 for field in ("court", "docket", "brands", "ingredients", "locator")})
            case = (row.court, row.docket, row.filed)
            proof = self.corroboration.get(case)
            if not proof:
                continue
            # Restrict retrospective Orange Book product annotations to the corroborated brand.
            brands = {name_form(brand) for brand in row.brands.split(",")}
            if name_form(proof["brand"]) not in brands:
                continue
            counts["corroborated_rows"] += 1
            # Multi-product patent rows can contain unrelated ingredients. The exact,
            # corroborated brand anchors the case to a single dated NDA composition.
            key = self.identity.court_key(proof["brand"], row.ingredients if len(brands) == 1 else "",
                                          cutoff)
            if key:
                counts["admitted_rows"] += 1
                cases[key, case].append(row.locator)
        for (key, case), locators in sorted(cases.items()):
            court, docket, filed = case
            witnesses[key].append(Witness(
                "RAI_COURT", f"{court} {docket}", filed, self.rai_source["version"],
                self.rai_source["sha256"], ", ".join(locators), self.rai_source["url"],
                self.corroboration[case],
            ))
        return witnesses, {**counts, "admitted_case_key_pairs": len(cases),
                           "match_rate": counts["matched_rows"] / counts["rows"] if counts["rows"] else None,
                           "unmatched_examples": examples}

    def lookup(self, key, cutoff):
        piv, coverage = self._piv(cutoff)
        rai, _ = self._rai(cutoff)
        witnesses = (*piv.get(key, ()), *rai.get(key, ()))
        state = T3.UNKNOWN
        if witnesses:
            state = T3.TRUE
        elif coverage["status"] == "FRESH":
            state = T3.FALSE
        return ChallengeEvidence(state, witnesses)

    def linkage_audit(self, cutoff):
        return {"FDA_PIV": self._piv(cutoff)[1], "RAI_COURT": self._rai(cutoff)[1]}
