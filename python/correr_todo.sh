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

# El barrido aleatorio corta en N = 425. En N = 450 el muestreo por rechazo ya
# esta al borde del empaquetamiento: de 50 semillas sondeadas solo 16 logran
# ubicar las particulas sin solapamientos, asi que con las semillas 1000-1009 se
# consiguen 5 realizaciones y no las 10 que pide el enunciado. El tramo
# 450-700 lo cubre el barrido hexagonal, que coloca sobre una red y nunca falla.
echo "== 1.1: tiempo de ejecucion vs N (sin obstaculos, 10 realizaciones) =="
"$PY" run.py particulas --rango 50 425 25 --realizaciones 10 --cada-eventos 100000

# El hexagonal arranca en el mismo N que el aleatorio para que las curvas se
# puedan comparar en 50-450, y sigue hasta 700 (la grilla admite 722 sitios).
# Los ultimos valores de N son caros: con N = 700 se ocupa el 97 % de los sitios
# y la red queda casi bloqueada, asi que la tasa de colisiones se dispara.
echo "== 1.1 hex: tiempo de ejecucion vs N (hexagonal, 10 realizaciones) =="
"$PY" run.py particulas --rango 50 700 25 --realizaciones 10 --cada-eventos 100000 --placement hex

echo "== 1.2 y 1.3: configuraciones de obstaculos (5 realizaciones, N = 100) =="
# shellcheck disable=SC2086
"$PY" run.py configs $CONFIGS --realizaciones 5 --trayectoria
