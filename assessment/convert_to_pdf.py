"""Convert hypothesis-data-assessment-v5.md to PDF using Edge headless."""
import subprocess
import sys
from pathlib import Path

import markdown

ASSESSMENT_DIR = Path(__file__).parent
MD_FILE = ASSESSMENT_DIR / "hypothesis-data-assessment-v5.md"
HTML_FILE = ASSESSMENT_DIR / "hypothesis-data-assessment-v5.html"
PDF_FILE = ASSESSMENT_DIR / "hypothesis-data-assessment-v5.pdf"

CSS = """
* { box-sizing: border-box; }

body {
    font-family: -apple-system, 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    line-height: 1.7;
    color: #1a1a2e;
    max-width: 900px;
    margin: 0 auto;
    padding: 40px 48px;
    background: #fff;
}

h1 {
    font-size: 26px;
    font-weight: 700;
    color: #0f3460;
    border-bottom: 3px solid #0f3460;
    padding-bottom: 10px;
    margin-top: 0;
    page-break-after: avoid;
}

h2 {
    font-size: 20px;
    font-weight: 700;
    color: #16213e;
    border-bottom: 2px solid #e8e8f0;
    padding-bottom: 6px;
    margin-top: 40px;
    page-break-after: avoid;
}

h3 {
    font-size: 16px;
    font-weight: 600;
    color: #0f3460;
    margin-top: 28px;
    page-break-after: avoid;
}

h4 {
    font-size: 14px;
    font-weight: 600;
    color: #444;
    margin-top: 20px;
    page-break-after: avoid;
}

p { margin: 10px 0; }

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 12.5px;
    page-break-inside: avoid;
}

th {
    background-color: #0f3460;
    color: #fff;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 7px 12px;
    border-bottom: 1px solid #e0e0ea;
    vertical-align: top;
}

tr:nth-child(even) td { background-color: #f7f7fc; }
tr:hover td { background-color: #eef2ff; }

/* Code blocks */
pre {
    background: #f4f4f8;
    border: 1px solid #d0d0e8;
    border-left: 4px solid #0f3460;
    border-radius: 4px;
    padding: 14px 16px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 11.5px;
    line-height: 1.5;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
    page-break-inside: avoid;
}

code {
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 11.5px;
    background: #eeeef8;
    padding: 1px 5px;
    border-radius: 3px;
}

pre code {
    background: none;
    padding: 0;
}

/* Blockquotes */
blockquote {
    margin: 16px 0;
    padding: 12px 16px;
    border-left: 4px solid #0f3460;
    background: #f0f4ff;
    border-radius: 0 4px 4px 0;
    font-style: italic;
    color: #333;
}

blockquote p { margin: 0; }

/* Lists */
ul, ol { padding-left: 24px; margin: 10px 0; }
li { margin: 4px 0; }

/* Horizontal rule */
hr {
    border: none;
    border-top: 1px solid #e0e0ea;
    margin: 28px 0;
}

/* Strong / emphasis */
strong { color: #0f3460; }

/* Links */
a { color: #1a73e8; text-decoration: none; }

/* Page break hints */
.page-break { page-break-before: always; }

/* Print optimizations */
@media print {
    body { padding: 20px 28px; font-size: 13px; }
    h1 { font-size: 22px; }
    h2 { font-size: 17px; margin-top: 24px; }
    h3 { font-size: 14px; }
    pre { font-size: 10.5px; }
    table { font-size: 11.5px; }
    td, th { padding: 5px 9px; }

    /* Keep headings with following content */
    h1, h2, h3, h4 { page-break-after: avoid; }

    /* Avoid breaking inside tables and code */
    table, pre { page-break-inside: avoid; }

    /* Ensure blockquotes don't break */
    blockquote { page-break-inside: avoid; }
}

/* Header badge line */
.header-meta {
    background: #eef2ff;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
    color: #555;
    margin-bottom: 24px;
}
"""

def build_html(md_text: str) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "toc", "nl2br"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
        },
    )
    body = md.convert(md_text)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hypothesis Platform — Data Assessment v5</title>
  <style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""


def find_edge():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


def find_chrome():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        rf"C:\Users\{Path.home().name}\AppData\Local\Google\Chrome\Application\chrome.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    return None


def main():
    md_text = MD_FILE.read_text(encoding="utf-8")
    html = build_html(md_text)

    HTML_FILE.write_text(html, encoding="utf-8")
    print(f"HTML generado: {HTML_FILE}")

    browser = find_edge() or find_chrome()
    if not browser:
        print("No se encontró Edge ni Chrome.")
        print(f"Abri el HTML manualmente en tu navegador y usa Ctrl+P → 'Guardar como PDF':")
        print(f"  {HTML_FILE}")
        sys.exit(1)

    print(f"Usando navegador: {browser}")
    print(f"Generando PDF en: {PDF_FILE}")

    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-software-rasterizer",
        f"--print-to-pdf={PDF_FILE}",
        "--print-to-pdf-no-header",
        f"file:///{HTML_FILE}",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if PDF_FILE.exists() and PDF_FILE.stat().st_size > 10_000:
        size_kb = PDF_FILE.stat().st_size // 1024
        print(f"\nPDF generado exitosamente: {PDF_FILE} ({size_kb} KB)")
    else:
        print(f"stderr: {result.stderr[:500]}")
        print(f"\n⚠️ PDF no generado o muy pequeño. Abre el HTML en tu navegador:")
        print(f"  {HTML_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()
