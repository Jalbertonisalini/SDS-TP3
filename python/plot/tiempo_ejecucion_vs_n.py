"""Punto 1.1: tiempo de ejecucion promedio vs N, con su desvio estandar.

    python plot/tiempo_ejecucion_vs_n.py --salida ../entrega/1.1/tiempo_vs_n.png

El tiempo lo mide el propio motor (wall-clock del bucle de eventos), asi que no
incluye el arranque del proceso ni la escritura inicial.
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
    parser.add_argument("--resumen", type=Path,
                        default=config.RESULTADOS / "particulas" / "resumen.csv",
                        help="CSV agregado del barrido en N")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    if not args.resumen.exists():
        print(f"Falta el resumen del barrido: {args.resumen}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.resumen)
    agrupado = datos.groupby("N")["tiempo_ejecucion_s"].agg(["mean", "std", "count"]).reset_index()

    fig, ax = plt.subplots(figsize=config.TAM_FIG)
    ax.errorbar(agrupado["N"], agrupado["mean"], yerr=agrupado["std"].fillna(0.0),
                marker="o", capsize=4, linestyle="-")
    ax.set_xlabel("Cantidad de particulas", fontsize=config.FUENTE)
    ax.set_ylabel("Tiempo de ejecucion (s)", fontsize=config.FUENTE)
    ax.tick_params(labelsize=config.FUENTE)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=config.DPI)
    print(f"Figura guardada en {args.salida}")
    print(agrupado.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
