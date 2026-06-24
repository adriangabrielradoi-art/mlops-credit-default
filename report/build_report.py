"""Build REPORT.pdf in the NOVA IMS academic style (cover page + Table of Contents
with real page numbers + numbered-section body), matching the group's CIFO report.

Pipeline: pandoc (Markdown -> HTML body) + a generated cover & ToC -> Chrome headless
(HTML -> PDF). The ToC page numbers are filled by a two-pass render: render once,
read which PDF page each section lands on, then render again with the numbers.

Run:  uv run --with pypdf python build_report.py
(pandoc must be on PATH; Chrome at the path below — swap to Edge if needed.)
"""
import re
import subprocess
from pathlib import Path

from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# ---- editable cover-page fields -------------------------------------------
COVER = dict(
    course="MLOps Project",
    programme="Master's in Data Science and Advanced Analytics",
    school="NOVA Information Management School",
    university="Universidade Nova de Lisboa",
    title="Credit Card Default Prediction",
    subtitle="An End-to-End, Reproducible MLOps Pipeline",
    group="Group: [group name]",
    members=[
        "Adrian Radoi (20250353)",
        "Lorenzo Simonazzi (20250402)",
        "[third member — name &amp; student number]",
    ],
    runline=("Repository: [GitHub link / attached zip]. "
             "Run with <code>uv sync</code> then <code>kedro run</code>, "
             "or open <code>notebooks/00_main.ipynb</code> and <b>Run All</b>."),
    date="June 2026",
)

# ---- section titles (for the ToC) -----------------------------------------
md = (HERE / "REPORT.md").read_text(encoding="utf-8")
sections = [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", md, re.M)]
# search key per section: number + first word (unique, robust to PDF text extraction)
def key(title):
    num = title.split(".")[0]
    first = re.sub(r"[^A-Za-z]", "", title.split(".", 1)[1].split()[0])
    return f"{num}. {first}"

BASE_CSS = (HERE / "report_style.css").read_text(encoding="utf-8")

EXTRA_CSS = """
.cover { height: 96vh; display: flex; flex-direction: column; align-items: center;
         text-align: center; page-break-after: always; }
.cover .blk { margin-top: 7%; }
.cover .course { font-size: 13pt; font-weight: bold; }
.cover .small { font-size: 11.5pt; }
.cover .title { margin-top: 13%; font-size: 22pt; font-weight: bold; line-height: 1.2; }
.cover .subtitle { font-size: 13pt; font-style: italic; margin-top: 6pt; }
.cover .group { margin-top: 12%; font-size: 12pt; font-weight: bold; }
.cover .members { font-size: 12pt; line-height: 1.5; }
.cover .runline { margin-top: 9%; font-size: 9pt; color: #444; max-width: 80%; }
.cover .date { margin-top: auto; margin-bottom: 4%; font-size: 12pt; font-weight: bold; }
.toc { page-break-after: always; }
.toc h2 { text-align: center; border: none; font-size: 15pt; margin-bottom: 12pt; }
.toc-entry { display: flex; align-items: baseline; font-size: 11pt; margin: 5pt 0; }
.toc-entry .leader { flex: 1; border-bottom: 1.5px dotted #888; margin: 0 5px; position: relative; top: -3px; }
.toc-entry .pg { font-variant-numeric: tabular-nums; }
"""


def cover_html():
    members = "<br>".join(COVER["members"])
    return f"""<div class="cover">
  <div class="blk"><div class="course">{COVER['course']}</div>
    <div class="small">{COVER['programme']}</div></div>
  <div class="blk"><div class="course">{COVER['school']}</div>
    <div class="small">{COVER['university']}</div></div>
  <div class="title">{COVER['title']}</div>
  <div class="subtitle">{COVER['subtitle']}</div>
  <div class="blk"><div class="group">{COVER['group']}</div>
    <div class="members">{members}</div></div>
  <div class="runline">{COVER['runline']}</div>
  <div class="date">{COVER['date']}</div>
</div>"""


def toc_html(pages):
    rows = []
    for t in sections:
        pg = pages.get(t, "")
        rows.append(f'<div class="toc-entry"><span class="t">{t}</span>'
                    f'<span class="leader"></span><span class="pg">{pg}</span></div>')
    return '<div class="toc"><h2>Table of Contents</h2>' + "".join(rows) + "</div>"


def build(pages):
    body = subprocess.run(["pandoc", "REPORT.md", "-t", "html", "--no-highlight"],
                          cwd=HERE, capture_output=True, text=True, encoding="utf-8").stdout
    html = (f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{BASE_CSS}{EXTRA_CSS}</style></head><body>"
            f"{cover_html()}{toc_html(pages)}{body}</body></html>")
    (HERE / "REPORT.html").write_text(html, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={HERE / 'REPORT.pdf'}", str(HERE / "REPORT.html")],
                   capture_output=True)


def map_pages():
    reader = PdfReader(str(HERE / "REPORT.pdf"))
    page_text = [re.sub(r"\s+", " ", p.extract_text() or "") for p in reader.pages]
    pages = {}
    for t in sections:
        k = key(t)
        for i, txt in enumerate(page_text):
            if i < 2:  # skip cover + ToC
                continue
            if k in txt:
                pages[t] = i + 1
                break
    return pages, len(reader.pages)


# Pass 1: render with empty page numbers, then map sections to pages.
build({})
pages, n = map_pages()
# Pass 2: render with real page numbers.
build(pages)
pages2, n2 = map_pages()
print(f"Built REPORT.pdf — {n2} pages")
print("ToC:", {t: pages2.get(t) for t in sections})
