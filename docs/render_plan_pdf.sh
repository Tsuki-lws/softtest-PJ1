#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_DIR="$ROOT_DIR/docs"
MD_FILE="$DOCS_DIR/项目测试计划书.md"
HTML_FILE="$DOCS_DIR/项目测试计划书.html"
PDF_FILE="$DOCS_DIR/项目测试计划书.pdf"
CSS_FILE="plan_print.css"

pandoc \
  --from=gfm+pipe_tables \
  --to=html5 \
  --standalone \
  --css="$CSS_FILE" \
  --metadata pagetitle='软件测试计划' \
  --output="$HTML_FILE" \
  "$MD_FILE"

npx playwright pdf \
  --channel chrome \
  --paper-format A4 \
  --color-scheme light \
  "file://$HTML_FILE" \
  "$PDF_FILE"

printf 'HTML: %s\nPDF: %s\n' "$HTML_FILE" "$PDF_FILE"
