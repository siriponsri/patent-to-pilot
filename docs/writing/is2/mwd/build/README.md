# IS2 paper build

Builds the KMITL AI4BA short paper (.docx and .pdf) from the Markdown drafts with the `kmitl-is-paper` skill. Needs Windows with Microsoft Word.

```sh
python ~/.claude/skills/kmitl-is-paper/scripts/make_paper.py --content content_th.py --figdir ../figures --out IS2-MWD-TH.docx
python ~/.claude/skills/kmitl-is-paper/scripts/make_paper.py --content content_en.py --figdir ../figures --out IS2-MWD-EN.docx
```

`md2content.py` converts `../IS2-DRAFT-{TH,EN}.md` into the paperkit content contract. Internal receipt links are dropped from print, and web links in references become "[Online]. Available: URL". Tables with more than five columns and Figure 1 are full-width floats. The script prints the page count and column ends; the target is 8–10 pages.
