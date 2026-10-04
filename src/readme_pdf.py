"""Render README.md into README.pdf, a printable brand guide for non-technical readers.

Drops the parts only developers need (the PDF button, the favicon HTML snippet, the
"Rebuilding" section) and styles the rest in the brand palette.
Run after build.py + guidelines.py:  python3 src/readme_pdf.py   (needs markdown, playwright)
"""
import re
from pathlib import Path
import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
md = (ROOT / "README.md").read_text()

md = re.sub(r'\s*&nbsp;\s*<a href="README.pdf">.*?</a>', "", md)                    # PDF button
md = re.sub(r" Or read the same guide as a \*\*\[PDF\]\(README.pdf\)\*\*\.", "", md)
md = re.sub(r"\*\*Web favicon snippet\*\*\n```html.*?```\n", "", md, flags=re.S)    # dev-only
md = re.sub(r"\n---\n\n## 10\. Rebuilding.*", "\n", md, flags=re.S)
md = md.replace(" · [Rebuilding](#10-rebuilding-the-files)", "")
md = md.replace("\n---\n", "\n")
md = re.sub(r"^(guidelines/|src/) .*\n", "", md, flags=re.M)                         # dev folders in file tree

body = markdown.markdown(md, extensions=["tables", "fenced_code", "toc", "md_in_html"])

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
@page { size: A4; margin: 16mm 15mm 18mm; }
body { font-family: 'Space Grotesk', sans-serif; color: #272C35; font-size: 10.5pt; line-height: 1.55; margin: 0; }
h1 { font-size: 26pt; line-height: 1.1; margin: 10mm 0 4mm; letter-spacing: -0.01em; }
h2 { font-size: 17pt; break-before: page; border-bottom: 2px solid #272C35; padding-bottom: 2mm; margin: 0 0 4mm; }
h3 { font-size: 12.5pt; margin: 7mm 0 2mm; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
img { max-width: 100%; height: auto; break-inside: avoid; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0 5mm; font-size: 9pt; break-inside: avoid; }
th, td { border: 1px solid #272C3526; padding: 2mm 2.5mm; text-align: left; vertical-align: top; }
th { background: #F3EFE8; }
thead tr:has(th:empty:first-child + th:empty) { display: none; }
td img { max-width: 100%; }
code { font-family: ui-monospace, Menlo, monospace; font-size: 8.5pt; background: #F3EFE8; padding: 0.3mm 1.2mm; border-radius: 1mm; }
pre { background: #F3EFE8; padding: 3mm 4mm; border-radius: 2mm; font-size: 7pt; break-inside: avoid; white-space: pre; overflow: hidden; }
pre code { background: none; padding: 0; }
a { color: #285ABD; text-decoration: none; }
p[align=center] { text-align: center; margin: 8mm 0; }
p[align=center] a img { height: 13mm; width: auto; }
"""

html = f'<!doctype html><html><head><meta charset="utf-8"><base href="{ROOT.as_uri()}/"><style>{CSS}</style></head><body>{body}</body></html>'
tmp = ROOT / "_readme.html"
tmp.write_text(html)
with sync_playwright() as pw:
    br = pw.chromium.launch()
    pg = br.new_page()
    pg.goto(tmp.as_uri()); pg.wait_for_load_state("networkidle")
    pg.pdf(path=str(ROOT / "README.pdf"), format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<span></span>",
           footer_template='<div style="font:8px sans-serif;color:#888;width:100%;text-align:center">aibuilders.id · Logo &amp; Brand Guidelines · <span class="pageNumber"></span>/<span class="totalPages"></span></div>')
    br.close()
tmp.unlink()
print("README.pdf written")
