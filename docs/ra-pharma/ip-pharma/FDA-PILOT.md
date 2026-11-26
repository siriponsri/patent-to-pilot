# FDA product-to-patent listing pilot

## Prospective engineering protocol

Use the first successful retrieval of the [FDA Orange Book data archive](https://www.fda.gov/media/76860/download?attachment) linked by the [field dictionary](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files). Save the intact ZIP outside Git and lock its SHA-256 before reading its tables. Fail closed on schema ambiguity. Never substitute another snapshot after reviewing counts. This is a public, exposed source-integrity exercise for ideas D, E and G. Comparator context is [PEMT](https://doi.org/10.1093/bioinformatics/btac716), which associates chemicals with candidate documents, and [PatentFinder](https://arxiv.org/abs/2412.07819), which tests a separate molecule-to-claim relation.

**Question.** If a portfolio demo labels a US patent as listed for an FDA product, how many unlisted product–patent pairs would two common shortcuts display? Take every unique NDA product key with an exact single ingredient from the fixed panel below, across all marketing categories. Keep leading zeros, empty patent sets and all listed patent identifiers as published. No treatment, clinical or enforceability inference. The six ingredients are a convenience panel selected by the Planner. Freeze before looking at the product or patent rows.

**Arms and endpoint.** For each query product, predict the union of unique patent numbers listed for (a) any enrolled product sharing the ingredient, (b) any enrolled product in the same FDA application, or (c) that exact FDA product key. Independently build the reference listing by reading the patent table at the exact key. Count predicted distinct product–patent pairs absent at that key, missed listed pairs, product keys with at least one extra, and total listed pairs. Report all arms and a per-ingredient breakdown. Method (c) is a deterministic schema control. Its agreement is a consistency check by construction. An absent listing means only that the association was absent from these bytes. No cohort adjustment, retries for performance, inference, significance test or TH gate scoring. Stop when the archived bytes have been read once for the original receipt.

## Reproduce on the retained archive

The following Python standard-library program takes the path to the pinned ZIP as its first argument. It does not use the network. The JSON output provides counts in the order printed under `fields`.

```python
import csv
import io
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import PurePosixPath

panel = (
    "APIXABAN", "RIVAROXABAN", "SITAGLIPTIN PHOSPHATE",
    "OMEPRAZOLE", "METFORMIN HYDROCHLORIDE", "EMPAGLIFLOZIN",
)
key_fields = ("appl_type", "appl_no", "product_no")

def table(archive, name):
    member, = [n for n in archive.namelist() if PurePosixPath(n).name.lower() == name]
    with archive.open(member) as binary:
        reader = csv.DictReader(io.TextIOWrapper(binary, encoding="latin-1"), delimiter="~")
        for row in reader:
            yield {field.lower().strip(): value.strip() for field, value in row.items()}

products = {}
listed = defaultdict(set)
with zipfile.ZipFile(sys.argv[1]) as archive:
    for row in table(archive, "products.txt"):
        ingredient = row["ingredient"].upper()
        if row["appl_type"] == "N" and ingredient in panel:
            key = tuple(row[f] for f in key_fields)
            assert key not in products or products[key] == ingredient
            products[key] = ingredient
    for row in table(archive, "patent.txt"):
        key = tuple(row[f] for f in key_fields)
        if key in products and row["patent_no"]:
            listed[key].add(row["patent_no"])

by_ingredient = defaultdict(set)
by_application = defaultdict(set)
for key, ingredient in products.items():
    by_ingredient[ingredient].update(listed[key])
    by_application[key[:2]].update(listed[key])

def summarize(keys):
    result = {}
    for arm in ("ingredient", "application", "exact"):
        extra = missed = affected = reference_size = 0
        for key in keys:
            expected = listed[key]
            predicted = {"ingredient": by_ingredient[products[key]],
                         "application": by_application[key[:2]], "exact": listed[key]}[arm]
            extra += len(predicted - expected)
            missed += len(expected - predicted)
            affected += bool(predicted - expected)
            reference_size += len(expected)
        result[arm] = [len(keys), reference_size, extra, missed, affected]
    return result

print(json.dumps({"fields": ["products", "listed_pairs", "extra_pairs", "missed_pairs",
                             "products_with_extra"], "all": summarize(list(products)),
                  "panel": {name: summarize([k for k in products if products[k] == name])
                            for name in panel}}, indent=2))
```
