"""Join Rai court filings to the Orange Book patents observable when filed."""
from collections import Counter, defaultdict
from dataclasses import replace
from functools import lru_cache
from hashlib import file_digest
from pathlib import Path
import re

from .challenge import ChallengeHistory, Witness
from .kleene import T3
from .t2_features import _EditionIndex, _edition_selection


_GRANT = re.compile(
    r"(?:US\s*-?\s*)?(RE|PP|D)?\s*(0*[0-9]{1,8}|[0-9]{1,3}(?:,[0-9]{3}){1,2})"
    r"(?:\s*-?\s*(?:A|[BC][12]|E1?|S1?|P[2-3]))?",
    re.ASCII,
)


def normalize_patent_number(value):
    """Resolve one US grant identifier, retaining the patent series prefix."""
    match = _GRANT.fullmatch((value or "").strip().upper())
    if match is None:
        return None
    prefix, number = match.groups()
    digits = number.replace(",", "").lstrip("0")
    return (prefix or "") + digits if digits else None


class FilingPatentIndex:
    def __init__(self, history, linker):
        self.history = history
        self.linker = linker

    @lru_cache(maxsize=32)
    def _index(self, source):
        path = Path(self.history.data_dir) / source.identity["file"]
        with path.open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != source.identity["sha256"]:
                raise ValueError(f"Orange Book ZIP digest mismatch: {path}")
        edition = self.history.load_source(source)
        keys_by_product = {
            product: key for key, products in _EditionIndex(edition, linker=self.linker).by_key.items()
            for product in products
        }
        patents = defaultdict(list)
        for position, row in enumerate(edition.patents, 1):
            number = normalize_patent_number(row["patent_no"])
            if number is None or (row["submission_date"] and row["submission_date"] > edition.edition_date):
                continue
            product = row["appl_no"], row["product_no"]
            patents[number].append((keys_by_product.get(product), {
                "appl_no": product[0], "product_no": product[1], "raw_patent_no": row["patent_no"],
                "locator": f"patent.txt data row {position}", "delist_flag": row["delist"],
            }))
        return patents

    @lru_cache(maxsize=4096)
    def _source(self, filed):
        return _edition_selection(self.history, filed)

    def match(self, value, filed, cutoff):
        if filed > cutoff:
            return "AFTER_CUTOFF", None, None, ()
        number = normalize_patent_number(value)
        if number is None:
            return "NO_NORMALIZED_PATENT", None, None, ()
        source, edition = self._source(filed)
        if source is None:
            return "NO_FRESH_EDITION", number, edition, ()
        rows = self._index(source).get(number, ())
        return ("LISTED" if rows else "PATENT_ABSENT"), number, edition, rows


def _agreement(patent, name):
    if patent and name:
        if patent == name:
            return "exact"
        return "partial_overlap" if patent & name else "disjoint"
    if patent:
        return "patent_only"
    return "name_only" if name else "neither"


class PatentChallengeHistory(ChallengeHistory):
    """Preserve E7 evidence and add independently attributed patent matches."""

    def __init__(self, piv, identity, court, rai_source, corroboration, patent_index):
        super().__init__(piv, identity, court, rai_source, corroboration)
        self.patent_index = patent_index

    @lru_cache(maxsize=16)
    def patent_evidence(self, cutoff):
        filed_cases = set()
        listed_cases = set()
        counts = Counter()
        name_keys = defaultdict(set)
        matches = defaultdict(lambda: defaultdict(list))
        unmatched_examples = {}
        for row in self.court:
            if row.filed > cutoff:
                continue
            case = row.court, row.docket, row.filed
            filed_cases.add(case)
            if key := self.identity.court_key(row.brands, row.ingredients, cutoff):
                name_keys[case].add(key)
            status, number, edition, listings = self.patent_index.match(row.patent, row.filed, cutoff)
            if status == "LISTED":
                listed_cases.add(case)
                status = "LISTED_WITHOUT_DATED_MOIETY"
                for key, listing in listings:
                    entity = self.identity.linker.entities.get(key)
                    if entity and entity.nda_first and entity.nda_first <= row.filed:
                        status = "LINKED"
                        matches[case][key].append({
                            "rai_locator": row.locator, "patent": number, "orange_book": {
                                **edition["source"], "edition_date": edition["chosen_edition"],
                                "availability_proof": edition["availability_proof"], **listing,
                            },
                        })
            counts[status] += 1
            if status != "LINKED" and status not in unmatched_examples:
                unmatched_examples[status] = dict(
                    court=row.court, docket=row.docket, filed=row.filed.isoformat(),
                    rai_locator=row.locator, raw_patent=row.patent,
                    edition_date=edition["chosen_edition"] if edition else None,
                )

        admitted_names = defaultdict(set)
        for key, witnesses in self._rai(cutoff)[0].items():
            for witness in witnesses:
                proof = witness.corroboration
                admitted_names[proof["court"], proof["docket"], witness.date].add(key)

        witnesses_by_key = defaultdict(list)
        raw_agreement = Counter()
        admitted_agreement = Counter()
        disagreement_examples = []
        for case in sorted(filed_cases):
            patent_keys = set(matches.get(case, ()))
            raw_keys = name_keys.get(case, set())
            admitted_keys = admitted_names.get(case, set())
            raw_status = _agreement(patent_keys, raw_keys)
            raw_agreement[raw_status] += 1
            admitted_agreement[_agreement(patent_keys, admitted_keys)] += 1
            court, docket, filed = case
            if raw_status in {"disjoint", "partial_overlap"} and len(disagreement_examples) < 5:
                disagreement_examples.append(dict(court=court, docket=docket, filed=filed.isoformat(),
                    patent_keys=sorted(patent_keys), name_keys=sorted(raw_keys)))
            for key, hits in sorted(matches.get(case, {}).items()):
                locators = list(dict.fromkeys(hit["rai_locator"] for hit in hits))
                proof = self.corroboration[case] if key in admitted_keys else None
                witnesses_by_key[key].append(Witness(
                    "RAI_OB_PATENT", f"{court} {docket}", filed, self.rai_source["version"],
                    self.rai_source["sha256"], ", ".join(locators), self.rai_source["url"],
                    {"case_type": "ANDA_CORROBORATED" if proof else "UNSPECIFIED",
                     "case_type_proof": proof, "matches": hits},
                ))
        return witnesses_by_key, {
            "filed_cases": len(filed_cases), "cases_with_listed_patent": len(listed_cases),
            "listed_patent_case_rate": len(listed_cases) / len(filed_cases) if filed_cases else None,
            "cases_with_resolved_moiety": len(matches),
            "cases_with_multiple_patent_keys": sum(len(keys) > 1 for keys in matches.values()),
            "patent_case_key_pairs": sum(map(len, matches.values())),
            "drugs_with_patent_witness": len(witnesses_by_key),
            "drugs_with_any_rai_witness": len(witnesses_by_key.keys() | self._rai(cutoff)[0].keys()),
            "row_dispositions": dict(counts), "unmatched_row_examples": unmatched_examples,
            "raw_name_agreement": dict(raw_agreement), "admitted_name_agreement": dict(admitted_agreement),
            "raw_name_disagreement_examples": disagreement_examples,
        }

    def lookup(self, key, cutoff):
        original = super().lookup(key, cutoff)
        patent_witnesses = self.patent_evidence(cutoff)[0].get(key, ())
        if not patent_witnesses:
            return original
        return replace(original, state=T3.TRUE, witnesses=(*original.witnesses, *patent_witnesses))
