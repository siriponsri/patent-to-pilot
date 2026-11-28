import sys, html, subprocess
from markdown_it import MarkdownIt
src, out_html = sys.argv[1], sys.argv[2]
md = open(src, encoding='utf-8').read()
body = MarkdownIt('commonmark', {'html': False, 'linkify': False}).enable('table').render(md)
css = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #1f2a44; }
h1 { font-size: 17pt; line-height: 1.25; margin: 0 0 8pt; }
h2 { font-size: 13pt; margin: 16pt 0 6pt; border-bottom: 1px solid #c9d1dd; padding-bottom: 2pt; }
h3 { font-size: 11pt; margin: 12pt 0 4pt; }
p, li { margin: 0 0 6pt; }
a { color: #0f766e; text-decoration: none; overflow-wrap: anywhere; }
code { font-family: Consolas, monospace; font-size: 8.5pt; overflow-wrap: anywhere; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 8.8pt; page-break-inside: avoid; }
th, td { border: 1px solid #c9d1dd; padding: 3pt 5pt; vertical-align: top; text-align: left; }
th { background: #f0f2f5; }
blockquote { margin: 6pt 0; padding-left: 8pt; border-left: 3px solid #c9d1dd; }
"""
open(out_html, 'w', encoding='utf-8').write(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>LOE-Bench preregistration</title><style>{css}</style></head><body>{body}</body></html>")
