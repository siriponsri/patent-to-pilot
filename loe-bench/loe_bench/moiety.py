"""Resolve active-moiety sets from the pinned public FDA/NCATS GSRS export."""
import gzip
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .common import parse_yyyymmdd, read_jsonl

GSRS_FILE = "dump-public-2026-08-06.gsrs"
GSRS_SHA256 = "07be61aea161cd212545c6cc1057a376bdbefcfc634da7ab1b4903b99f7bacad"
ORANGE_FILES = ("ob_nda.jsonl", "ob_anda_pre1982.jsonl", "ob_anda_to2009.jsonl",
                "ob_anda_2010s.jsonl", "ob_anda_2020plus.jsonl")
UNII = re.compile(r"[A-Z0-9]{10}")
SOLVATES = re.compile(r"(?:ANHYDROUS|(?:MONO|DI|TRI|TETRA|PENTA|HEXA|HEPTA|OCTA|HEMI|SESQUI)?HYDRATE|ETHANOLATE)$")
SALT_SUFFIXES = {
    "HYDROCHLORIDE", "HCL", "HYDROBROMIDE", "MESYLATE", "BESYLATE",
    "MALEATE", "DIMALEATE", "BITARTRATE", "FUMARATE", "DIFUMARATE",
}
ELECTROLYTE = re.compile(
    r"^(?:SODIUM|POTASSIUM|MAGNESIUM|CALCIUM|AMMONIUM) "
    r"(?:CHLORIDE|ACETATE|BICARBONATE|CARBONATE|SULFATE|PHOSPHATE|LACTATE|GLUCONATE)"
    r"(?: (?:MONOBASIC|DIBASIC|TRIBASIC))?$"
)


def name_form(name):
    return " ".join(re.findall(r"[A-Z0-9]+", (name or "").upper()))


def fallback_name(name):
    """Remove trailing solvate qualifiers and a narrow list of salt suffixes."""
    words = name_form(name).split()
    while len(words) > 1 and (SOLVATES.fullmatch(words[-1]) or words[-1] in SALT_SUFFIXES):
        words.pop()
    return " ".join(words)


def electrolyte_name(name):
    """Preserve a specifically listed electrolyte, collapsing hydration only."""
    name = re.sub(r" " + SOLVATES.pattern, "", name_form(name))
    return name if ELECTROLYTE.fullmatch(name) else None


def contains_name(text, name):
    return bool(name and f" {name} " in f" {text} ")


def product_names(product):
    return tuple(a["name"] for a in product.get("active_ingredients") or [] if a.get("name"))


@dataclass(frozen=True)
class Composition:
    parts: frozenset
    low_confidence: bool = False

    @property
    def key(self):
        return "|".join(sorted(self.parts))


class Registry:
    def __init__(self, records=()):
        self.aliases = defaultdict(set)
        self.targets = {}
        uuids, relationships = {}, {}
        for record in records:
            code = record.get("approvalID") or ""
            if not UNII.fullmatch(code):
                continue
            if record.get("uuid"):
                uuids[record["uuid"]] = code
            for item in record.get("names") or []:
                if name := name_form(item.get("name")):
                    self.aliases[name].add(code)
            relationships[code] = [r.get("relatedSubstance") or {}
                                   for r in record.get("relationships") or []
                                   if r.get("type") == "ACTIVE MOIETY"]
        for code, refs in relationships.items():
            targets = set()
            for ref in refs:
                target = ref.get("approvalID") or uuids.get(ref.get("refuuid")) or ref.get("linkingID")
                if target and UNII.fullmatch(target):
                    targets.add(target)
            self.targets[code] = frozenset(targets or {code})

    def ids(self, name):
        return self.aliases.get(name_form(name), set())

    def from_ids(self, codes):
        return frozenset("U:" + target for code in codes
                         for target in self.targets.get(code, (code,)))

    def known(self, name, hints=frozenset()):
        codes = self.ids(name)
        if codes & hints:
            codes = codes & hints
        choices = {self.from_ids([code]) for code in codes}
        return next(iter(choices)) if len(choices) == 1 else None

    def composition(self, names, unii=()):
        hints = {code for code in unii if UNII.fullmatch(code)}
        parts, low = set(), False
        for name in names:
            known = self.known(name, hints)
            electrolyte = electrolyte_name(name)
            if electrolyte:
                # Some GSRS entries resolve different qualifying ions to
                # phosphate alone. Retain the FDA listed electrolyte unit.
                parts.add("E:" + electrolyte)
                low |= not bool(known or self.known(electrolyte, hints))
                continue
            if known:
                parts.update(known)
                continue
            # A native field can encode a combination; require recognized
            # components for implicit delimiters to avoid breaking substance names.
            tokens = re.split(r"\s*[:;]\s*|\s+AND\s+", name, flags=re.IGNORECASE)
            components = [self.known(token, hints) for token in tokens]
            if len(tokens) > 1 and all(components):
                parts.update(set().union(*components))
                continue
            stripped = fallback_name(name)
            if (stripped in {"PURIFIED WATER", "STERILE WATER", "STERILE WATER FOR INJECTION",
                             "STERILE WATER FOR IRRIGATION"}
                    and self.ids("WATER") & hints):
                parts.update(self.from_ids(self.ids("WATER") & hints))
                continue
            low = True
            if self.ids(name):
                parts.add(name_form(name))
                continue
            if stripped in {"PURIFIED WATER", "STERILE WATER", "STERILE WATER FOR INJECTION",
                            "STERILE WATER FOR IRRIGATION"}:
                stripped = "WATER"
            if stripped:
                parts.update(self.known(stripped, hints) or {stripped})
        return Composition(frozenset(parts), low)

    def product(self, product, annotation=None):
        """Use labels only when tied to a product, never as an unscoped union."""
        annotation = annotation or {}
        hints = annotation.get("unii") or []
        names = product_names(product)
        native = self.composition(names, hints)
        substances = annotation.get("substance_name") or []
        if (len(names) == len(substances) == len(hints) == 1 and len(native.parts) == 1
                and native.low_confidence and name_form(names[0]) == name_form(substances[0])
                and hints[0] in self.targets and not self.ids(names[0])):
            return Composition(self.from_ids(hints))
        brand = name_form(product.get("brand_name"))
        label_brands = [name_form(name) for name in annotation.get("brand_name") or []]
        if not substances or len(annotation.get("spl_id") or []) != 1 or not brand:
            return native

        label = self.composition(substances, hints)
        # A one-label exact brand (or a proprietary brand expanded by SPL)
        # corroborates the scope. A native descriptive name must also agree
        # unless each additional ingredient is named on the product itself.
        exact_brand = any(b == brand or b.startswith(brand + " ") for b in label_brands)
        named = all(contains_name(brand, fallback_name(n)) for n in substances)
        if named and native.parts < label.parts:
            return label
        if exact_brand and native.parts and native.parts <= label.parts:
            # The extra ingredients must appear on a matching descriptive product name.
            matched = [b for b in label_brands if b == brand or b.startswith(brand + " ")]
            if label.parts == native.parts or all(
                any(contains_name(b, fallback_name(n)) for b in matched)
                for n in substances
            ):
                return label
        return native

    def orange_book(self, product):
        return self.product(product, product.get("openfda"))


def drug_product(registry, record, product, orange=None):
    annotation = product.get("openfda") or record.get("openfda") or {}
    native = registry.product(product, annotation)
    if orange is None:
        return native
    listed = registry.orange_book(orange)
    # Preserve the native source where the two product records disagree.
    return listed if not native.parts else native


@lru_cache(maxsize=2)
def _load(path):
    with path.open("rb") as file:
        if hashlib.file_digest(file, "sha256").hexdigest() != GSRS_SHA256:
            raise ValueError(f"GSRS digest mismatch: {path}")
    with gzip.open(path, "rt", encoding="utf-8") as file:
        return Registry(json.loads(line.split("\t", 2)[-1]) for line in file if line.strip())


def registry_for(raw_dir, gsrs_path=None):
    if gsrs_path is not None:
        return _load(Path(gsrs_path).resolve())
    path = Path(raw_dir).resolve().parent / "moiety" / GSRS_FILE
    return _load(path) if path.is_file() else Registry()


def orange_products(raw_dir):
    """Index unique openFDA Orange Book product evidence by typed application and number."""
    products = {}
    conflicts = set()
    for name in sorted(ORANGE_FILES):
        path = Path(raw_dir) / name
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            for p in row.get("products") or []:
                prefix = {"N": "NDA", "A": "ANDA"}.get(p.get("application_type"))
                number = p.get("application_number")
                product = p.get("product_number") or row.get("product_number")
                if prefix and number and product:
                    index = (prefix + str(number).zfill(6), str(product).zfill(3))
                    evidence = (p, parse_yyyymmdd(p.get("approval_date") or row.get("approval_date")))
                    if index in products and (product_names(products[index][0]) != product_names(p)
                                              or products[index][1] != evidence[1]):
                        conflicts.add(index)
                    products[index] = evidence
    return {index: row for index, row in products.items() if index not in conflicts}
