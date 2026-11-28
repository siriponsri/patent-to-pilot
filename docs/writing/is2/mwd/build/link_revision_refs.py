"""Restore external links and wrap the Thai student footnote in a KMITL build."""

import copy
import sys
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from md2content import LINK, reference_label


def link_text(paragraph, label, url):
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


def wrap_student_footnote(document):
    school = "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง"
    run, = (run for p in document.paragraphs if p.text.startswith("1 นักศึกษาปริญญาโท")
            for run in p.runs if run.text == school)
    run._r.find(qn("w:t")).addprevious(OxmlElement("w:br"))


def main():
    draft_path, docx_path = map(Path, sys.argv[1:])
    draft = draft_path.read_text(encoding="utf-8")
    document = Document(docx_path)
    for line in draft.splitlines():
        if line.startswith("!"):
            continue
        marker = line.split(" ", 1)[0]
        is_reference = marker.startswith("[") and marker[1:-1].isdigit()
        for name, url in LINK.findall(line):
            if not url.startswith("https://"):
                continue
            label = reference_label(name) if is_reference else name
            paragraph, = (p for p in document.paragraphs
                          if (not is_reference or p.text.startswith(marker + " "))
                          and any(label in run.text for run in p.runs))
            if is_reference:
                paragraph.paragraph_format.keep_together = True
            link_text(paragraph, label, url)
    wrap_student_footnote(document)
    document.save(docx_path)


if __name__ == "__main__":
    main()
