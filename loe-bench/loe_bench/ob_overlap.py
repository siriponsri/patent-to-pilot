"""Compare Orange Book editions at the application-level tuple grain."""

from collections import Counter, defaultdict


def _nda_tuples(rows, field, application_type, *, normalize_pediatric=True):
    tuples, counts = set(), Counter()
    for row in rows:
        kind = application_type(row)
        if kind != "N":
            counts["non_nda" if kind else "unclassified"] += 1
            continue
        if not row[field] or row["expiry"] is None:
            counts["incomplete"] += 1
            continue
        identifier = row[field].upper()
        if field == "patent_no" and normalize_pediatric and identifier.endswith("*PED"):
            counts["normalized_pediatric_marker"] += 1
            identifier = identifier.removesuffix("*PED")
        tuples.add((row["appl_no"], identifier, row["expiry"]))
    return tuples, dict(counts)


def _compare(annual, archival):
    common = len(annual & archival)
    union = len(annual | archival)
    expiry_sets = defaultdict(lambda: (set(), set()))
    for index, source in enumerate((annual, archival)):
        for nda, identifier, expiry in source:
            expiry_sets[nda, identifier][index].add(expiry)
    return {
        "annual": len(annual), "archival": len(archival), "exact": common,
        "jaccard": common / union if union else None,
        "annual_fraction_matched": common / len(annual) if annual else None,
        "archival_fraction_matched": common / len(archival) if archival else None,
        "annual_only": len(annual) - common, "archival_only": len(archival) - common,
        "shared_identity_different_expiry_sets": sum(
            bool(a and b and a != b) for a, b in expiry_sets.values()
        ),
    }


def compare_editions(annual, archival, application_type):
    """Count exact NDA tuples and diagnose differences at the same identifier."""
    result = {}
    for attribute, field in (("patents", "patent_no"), ("exclusivity", "code")):
        a, a_excluded = _nda_tuples(getattr(annual, attribute), field, application_type)
        b, b_excluded = _nda_tuples(getattr(archival, attribute), field, application_type)
        result[attribute] = dict(_compare(a, b), annual_excluded=a_excluded,
                                 archival_excluded=b_excluded)
        if attribute == "patents":
            raw, _ = _nda_tuples(archival.patents, field, application_type,
                                 normalize_pediatric=False)
            result[attribute]["raw_zip_identifier_jaccard"] = _compare(a, raw)["jaccard"]
            result[attribute]["zip_pediatric_rows"] = b_excluded.pop("normalized_pediatric_marker", 0)
    return result
