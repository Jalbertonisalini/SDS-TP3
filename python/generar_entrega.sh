#!/bin/bash
# Regenera TODAS las figuras del informe y de la presentacion.
# Ninguna figura del .tex se genera a mano: si esta en el informe, sale de aca.
set -e
cd "$(dirname "$0")"

PY="./.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Falta el virtualenv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi

ENTREGA="../entrega"
RESULTADOS="../build/resultados"

echo "== 1.1 =="
"$PY" plot/tiempo_ejecucion_vs_n.py --salida "$ENTREGA/1.1/tiempo_ejecucion_vs_n.png"
"$PY" plot/tiempo_ejecucion_vs_n_loglog.py --salida "$ENTREGA/1.1/tiempo_ejecucion_vs_n_loglog.png"
"$PY" plot/tiempo_ejecucion_vs_n_hex.py --salida "$ENTREGA/1.1/tiempo_ejecucion_vs_n_hex.png"
"$PY" plot/tiempo_ejecucion_vs_n_combined.py --salida "$ENTREGA/1.1/tiempo_ejecucion_vs_n_combined.png"

echo "== 1.2 =="
"$PY" plot/t90_vs_configuracion.py --salida "$ENTREGA/1.2/t90_vs_configuracion.png"

echo "== 1.3 =="
# DCM y D de cada configuracion, y <t90> vs D. La ventana de ajuste vive en
# punto_1_3.py para que todas las figuras usen la misma.
"$PY" punto_1_3.py --solo-graficos
