"""Punto 1.2: fraccion de particulas usadas en funcion del tiempo, por configuracion.

    python plot/fu_vs_tiempo.py --directorio ../build/resultados/configs/vacia \
                                --directorio ../build/resultados/configs/embudo \
                                --salida ../entrega/1.2/fu_vs_tiempo.png

Una curva por --directorio; el nombre de la configuracion se deduce de la ruta.
Como la simulacion es dirigida por eventos, las series vienen con muestreo
irregular: antes de promediar entre realizaciones se interpolan todas a una
grilla temporal uniforme comun.
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def serie_promedio(directorio, grilla):
    """Promedia F_u(t) sobre las realizaciones del directorio, en la grilla dada."""
    curvas = []
    for csv_path in sorted(directorio.glob("N*_s*.csv")):
        datos = pd.read_csv(csv_path)
        # F_u es monotona no decreciente: fuera del rango simulado se mantiene el ultimo valor.
        curvas.append(np.interp(grilla, datos["Time"], datos["UsedFraction"]))
    if not curvas:
        return None, None
    apiladas = np.vstack(curvas)
    return apiladas.mean(axis=0), apiladas.std(axis=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--directorio", type=Path, action="append", required=True,
                        help="Directorio de una configuracion; repetible, una curva por aparicion")
    parser.add_argument("--tmax", type=float, default=config.TIEMPO_MAXIMO,
                        help="Extremo derecho de la grilla temporal")
    parser.add_argument("--puntos", type=int, default=200,
                        help="Cantidad de puntos de la grilla uniforme")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    grilla = np.linspace(0.0, args.tmax, args.puntos)
    fig, ax = plt.subplots(figsize=config.TAM_FIG)

    for directorio in args.directorio:
        media, desvio = serie_promedio(directorio, grilla)
        if media is None:
            print(f"Sin realizaciones en {directorio}", file=sys.stderr)
            continue
        # F_u esta acotada en [0, 1]: la banda de error se recorta al dominio fisico.
        inferior = np.clip(media - desvio, 0.0, 1.0)
        superior = np.clip(media + desvio, 0.0, 1.0)
        linea, = ax.plot(grilla, media, label=directorio.name)
        ax.fill_between(grilla, inferior, superior, alpha=0.25, color=linea.get_color())

    ax.axhline(config.FRACCION_OBJETIVO, linestyle="--", color="black", alpha=0.6)
    ax.set_xlabel("Tiempo (s)", fontsize=config.FUENTE)
    ax.set_ylabel("Fraccion de particulas usadas", fontsize=config.FUENTE)
    ax.tick_params(labelsize=config.FUENTE)
    ax.legend(loc="best", fontsize=config.FUENTE)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=config.DPI)
    print(f"Figura guardada en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
