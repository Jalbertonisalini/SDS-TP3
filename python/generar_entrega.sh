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

echo "== 1.2 =="
"$PY" plot/t90_vs_configuracion.py --salida "$ENTREGA/1.2/t90_vs_configuracion.png"
"$PY" plot/fu_vs_tiempo.py \
  --directorio "$RESULTADOS/configs/vacia" \
  --directorio "$RESULTADOS/configs/central_grande" \
  --directorio "$RESULTADOS/configs/embudo" \
  --salida "$ENTREGA/1.2/fu_vs_tiempo.png"

echo "== 1.3 =="
"$PY" plot/dcm_vs_tiempo.py \
  --serie "$RESULTADOS/configs/vacia/N100_s1000.csv" \
  --tmax-ajuste 2.0 \
  --salida "$ENTREGA/1.3/dcm_vacia.png" \
  --salida-error "$ENTREGA/1.3/error_pendiente_vacia.png"
"$PY" plot/dcm_vs_tiempo.py \
  --serie "$RESULTADOS/configs/embudo/N100_s1000.csv" \
  --tmax-ajuste 2.0 \
  --salida "$ENTREGA/1.3/dcm_embudo.png"
