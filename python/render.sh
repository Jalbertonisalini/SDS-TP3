#!/bin/bash
# Compila ../presentation.tex con tectonic usando el python del virtualenv.
#   ./render.sh            una compilacion
#   ./render.sh --watch    recompila al guardar
set -e
cd "$(dirname "$0")"

PY="./.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Falta el virtualenv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

exec "$PY" render_latex.py "$@"
