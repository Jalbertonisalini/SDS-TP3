"""Convergencia de una corrida del algoritmo genetico (punto 1.2, GA).

    python plot/convergencia_ga.py \
        --log ../build/resultados/genetico/K4_s1001/log.csv \
        --salida output/convergencia_k4.png

Grafica el fitness promedio de la poblacion por generacion (linea), con una
banda sombreada de +/- 1 desvio estandar (dispersion real de la poblacion
en esa generacion, no el rango mejor-peor que exagera outliers). El fitness
es t90 en segundos (o la penalizacion si no se llego a Fu=0.90), asi que
"menor es mejor".
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
                             "desvio_fitness,peor_fitness,tiempo_s), lo escribe optimizador --log")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    if not args.log.exists():
        print(f"Falta el log: {args.log}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.log)
    if "desvio_fitness" not in datos.columns:
        sys.exit("El log no tiene desvio_fitness -- recompila el optimizador y volve a correr "
                 "esta corrida del GA (el logger viejo no calculaba el desvio).")

    inferior = datos["promedio_fitness"] - datos["desvio_fitness"]
    superior = datos["promedio_fitness"] + datos["desvio_fitness"]

    fig, ax = plt.subplots(figsize=config.TAM_FIG)
    ax.fill_between(datos["generacion"], inferior, superior,
                    alpha=0.2, color="tab:orange", label="promedio +/- 1 desvio")
    ax.plot(datos["generacion"], datos["promedio_fitness"], color="tab:orange", linewidth=2,
            label="fitness promedio de la poblacion")
    ax.set_xlabel("Generacion", fontsize=config.FUENTE)
    ax.set_ylabel("Fitness", fontsize=config.FUENTE)
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
