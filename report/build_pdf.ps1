# Regenerate REPORT.pdf (NOVA IMS style: cover + Table of Contents + numbered sections).
# Run from the report/ folder:  .\build_pdf.ps1
# Requires: pandoc on PATH, Google Chrome, and uv (for the pypdf used to number the ToC).

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

# build_report.py does: pandoc (MD->HTML body) + generated cover & ToC -> Chrome (PDF),
# with a two-pass render so the Table of Contents shows real page numbers.
uv run --no-project --with pypdf python build_report.py

Write-Host "Wrote REPORT.pdf"
