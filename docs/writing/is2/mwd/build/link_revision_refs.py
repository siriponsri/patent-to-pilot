"""Link the compact readout-guide and Zenodo citations in a KMITL build."""

import copy
import re
import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE


def link_reference(document, number, label, url):
    paragraph, = (p for p in document.paragraphs if p.text.startswith(number + " "))
    run, = (r for r in paragraph.runs if label in r.text)
    before, after = run.text.split(label, 1)
    linked_run = copy.deepcopy(run._r)
    linked_run.text = label
    trailing_run = copy.deepcopy(run._r)
    trailing_run.text = after
    run.text = before

    hyperlink = OxmlElement("w:hyperlink")
    relationship = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink.set(qn("r:id"), relationship)
    hyperlink.append(linked_run)
    run._r.addnext(hyperlink)
    hyperlink.addnext(trailing_run)


def main():
    draft_path, docx_path = map(Path, sys.argv[1:])
    draft = draft_path.read_text(encoding="utf-8")
    document = Document(docx_path)
    for marker, name, url in re.findall(r"^(\[\d+\]).*?\[(Source|doi: 10\.5281/[^\]]+)\]\((https://[^)]+)\)", draft, re.M):
        label = "[Online guide]" if name == "Source" else name
        link_reference(document, marker, label, url)
    document.save(docx_path)


if __name__ == "__main__":
    main()
