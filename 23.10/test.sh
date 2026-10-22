#!/usr/bin/env bash
set -e
python -m coverage erase
python -m coverage run --source=analyzer -m unittest discover -s tests -v
python -m coverage report --skip-empty
python -m coverage html
python -m unittest discover -s tests -v 2>&1 | tee test-run.txt
python - <<'PY'
import html
from pathlib import Path
text = Path("test-run.txt").read_text(encoding="utf-8", errors="replace")
Path("test-report.html").write_text(
    "<!doctype html><html lang='ru'><meta charset='utf-8'><title>Отчёт тестов</title>"
    "<h1>Отчёт автоматических тестов</h1><pre>" + html.escape(text) + "</pre></html>",
    encoding="utf-8")
PY
echo "HTML отчёты: test-report.html и htmlcov/index.html"
