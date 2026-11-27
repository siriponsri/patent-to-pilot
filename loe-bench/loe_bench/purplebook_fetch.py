"""Print the monthly Purple Book CSV URLs (Track B). Direct curl may be blocked by an FDA bot page,
so download in a browser (or via a page-scrape service) into data/purplebook/ and then use purplebook.py.
Month spelling on the FDA listing page can differ (e.g. 'april' vs 'April'): check the listing page.
Usage: python3 -m loe_bench.purplebook_fetch 2020 2026
"""
import sys

MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]


def urls(y0: int, y1: int):
    for y in range(y0, y1 + 1):
        for m in MONTHS:
            yield f"https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/{y}/purplebook-search-{m}-data-download.csv"


if __name__ == "__main__":
    y0, y1 = int(sys.argv[1]), int(sys.argv[2])
    for u in urls(y0, y1):
        print(u)
