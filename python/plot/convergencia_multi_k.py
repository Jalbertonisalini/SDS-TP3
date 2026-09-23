"""Convergencia del GA comparando varias corridas en un mismo grafico (punto
1.2, simetria quad): una curva de mejor_fitness vs generacion por serie, sin
banda de desvio (a diferencia de convergencia_ga.py, que muestra una unica
corrida con la dispersion de su poblacion).

    python plot/convergencia_multi_k.py \
        --serie "K=5"  ../build/resultados/genetico/quad/K5_s1000/log.csv \
        --serie "K=9"  ../build/resultados/genetico/quad/K9_s1002/log.csv \
        --serie "K=13" ../build/resultados/genetico/quad/K13_s1001/log.csv \
        --serie "K=17" ../build/resultados/genetico/quad/K17_s1000/log.csv \
        --salida output/quad_convergencia.png

El fitness es el que usa el GA para seleccionar (t90 medido con pocas
semillas comunes por generacion): sirve para comparar velocidad/forma de
convergencia entre series, no como medicion de t90 real -- para eso hay que
correr la config ganadora con muchas realizaciones (ver t90_vs_configuracion.py).
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serie", nargs=2, action="append", metavar=("ETIQUETA", "LOG_CSV"),
                        required=True,
                        help="Etiqueta de la curva (ej. 'K=9') y su log.csv de convergencia "
                             "(repetible)")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    fig, ax = estilo.nueva_figura()

    for etiqueta, ruta_log in args.serie:
        ruta_log = Path(ruta_log)
        if not ruta_log.exists():
            print(f"Falta el log: {ruta_log}", file=sys.stderr)
            return 1
        datos = pd.read_csv(ruta_log)
        ax.plot(datos["generacion"], datos["mejor_fitness"], linewidth=2, label=etiqueta)

    estilo.etiquetar_ejes(ax, "Generacion", "Fitness")
    if len(args.serie) > 1:
        ax.legend(loc="best", fontsize=config.FUENTE * 0.8)
    estilo.guardar(fig, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
