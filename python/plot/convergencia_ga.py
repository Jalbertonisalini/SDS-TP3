"""Convergencia de una corrida del algoritmo genetico (punto 1.2, GA).

    python plot/convergencia_ga.py \
        --log ../build/resultados/genetico/K4_s1001/log.csv \
        --salida output/convergencia_k4.png

Grafica el mejor fitness de la generacion (linea) y la banda entre el
promedio y el peor, para ver de un vistazo si la poblacion converge o si
sigue diversa hasta el final. El fitness es t90 en segundos (o la
penalizacion si no se llego a Fu=0.90), asi que "menor es mejor".
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--log", type=Path, required=True,
                        help="CSV de convergencia (generacion,mejor_fitness,promedio_fitness,"
                             "peor_fitness,tiempo_s), lo escribe optimizador --log")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    if not args.log.exists():
        print(f"Falta el log: {args.log}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.log)

    fig, ax = plt.subplots(figsize=config.TAM_FIG)
    ax.fill_between(datos["generacion"], datos["mejor_fitness"], datos["peor_fitness"],
                    alpha=0.15, color="tab:blue", label="rango mejor-peor")
    ax.plot(datos["generacion"], datos["promedio_fitness"], linestyle="--", color="tab:orange",
            label="promedio de la poblacion")
    ax.plot(datos["generacion"], datos["mejor_fitness"], color="tab:blue", linewidth=2,
            label="mejor individuo")
    ax.set_xlabel("Generacion", fontsize=config.FUENTE)
    ax.set_ylabel("Fitness (t90 en s, o penalizacion)", fontsize=config.FUENTE)
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
