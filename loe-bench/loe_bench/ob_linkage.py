"""Link historical Orange Book products to the fixed FIX2b entity identities."""
from collections import defaultdict
from pathlib import Path

from .common import read_jsonl
from .moiety import drug_product, orange_products, product_names, registry_for
from .ob_history import norm_appl_no


class HistoricalMoietyLinker:
    def __init__(self, raw_dir, entities, *, gsrs_path=None):
        self.registry = registry_for(raw_dir, gsrs_path)
        self.entities = entities
        self.aliases = {alias: key for key, entity in entities.items() for alias in entity.key_aliases}
        self.application_types = defaultdict(set)
        self.nda_products = defaultdict(set)
        orange = orange_products(raw_dir)
        for app, _ in orange:
            kind, number = (("N", app[3:]) if app.startswith("NDA") else ("A", app[4:]))
            self.application_types[number].add(kind)
        for kind, prefix in (("N", "NDA"), ("A", "ANDA")):
            for record in read_jsonl(Path(raw_dir) / f"df_{prefix.lower()}.jsonl"):
                app = record.get("application_number") or ""
                if not app.startswith(prefix) or not app[len(prefix):].isdigit():
                    continue
                number = norm_appl_no(app[len(prefix):])
                self.application_types[number].add(kind)
                if kind == "N":
                    self._add_nda_products(record, number, orange)

    def _add_nda_products(self, record, number, orange):
        for product in record.get("products") or []:
            product_no = str(product.get("product_number") or "")
            if not product_no.isdigit():
                continue
            product_no = product_no.zfill(3)
            evidence = orange.get(("NDA" + number, product_no))
            listed = evidence[0] if evidence else None
            composition = drug_product(self.registry, record, product, listed, reconcile_resin=True)
            names = self.registry.composition(product_names(product) or product_names(listed or {})).names
            if composition.key:
                self.nda_products[number, product_no].add((self.canonical(composition.key), names))

    def canonical(self, key):
        return self.aliases.get(key, key)

    def application_type(self, row):
        if row["appl_type"]:
            return row["appl_type"]
        kinds = self.application_types.get(row["appl_no"], ())
        return next(iter(kinds)) if len(kinds) == 1 else None

    def match(self, row):
        ingredient = row.get("ingredient", "")
        composition = self.registry.composition(ingredient.split(";"))
        key = self.canonical(composition.key)
        by_name = key if key in self.entities else None
        number = row["product_no"]
        anchors = self.nda_products.get((row["appl_no"], number.zfill(3)), ()) if number.isdigit() else ()
        anchor_keys = {candidate for candidate, _ in anchors}
        if row.get("partial_ingredient"):
            if len(anchor_keys) > 1:
                return None, "conflicting_product_identity"
            candidate = next(iter(anchor_keys), None)
            if candidate not in self.entities:
                return None, "no_exact_product_anchor"
            if (not composition.low_confidence and composition.parts
                    and not composition.parts.issubset(candidate.split("|"))):
                return None, "conflicting_product_identity"
            return candidate, "application_product_partial_ingredient"
        if by_name is not None:
            if anchor_keys and anchor_keys != {by_name}:
                return None, "conflicting_product_identity"
            return by_name, "ingredient"
        if len(anchor_keys) > 1:
            return None, "conflicting_product_identity"
        for candidate, names in anchors:
            if candidate in self.entities and (
                not composition.names or (composition.low_confidence and composition.names == names)
            ):
                return candidate, "application_product"
        return None, "no_entity_match"
