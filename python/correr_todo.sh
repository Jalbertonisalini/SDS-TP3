#!/bin/bash
# Regenera TODAS las simulaciones del TP desde cero.
set -e
cd "$(dirname "$0")"

PY="./.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Falta el virtualenv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

if [ ! -x "../build/simulador" ]; then
  echo "Falta compilar el motor: cmake -S .. -B ../build && cmake --build ../build" >&2
  exit 1
fi

# Configuraciones exploradas en el punto 1.2. Agregar aca las nuevas candidatas.
CONFIGS="vacia central_grande embudo"

echo "== 1.1: tiempo de ejecucion vs N (sin obstaculos, 10 realizaciones) =="
"$PY" run.py particulas --rango 50 500 25 --realizaciones 10 --cada-eventos 100000

echo "== 1.1 hex: tiempo de ejecucion vs N (hexagonal, 10 realizaciones) =="
"$PY" run.py particulas --rango 300 700 25 --realizaciones 10 --cada-eventos 100000 --placement hex

echo "== 1.2 y 1.3: configuraciones de obstaculos (5 realizaciones, N = 100) =="
# shellcheck disable=SC2086
"$PY" run.py configs $CONFIGS --realizaciones 5 --trayectoria
