"""Punto 1.2: <t90> con barra de error para cada configuracion de obstaculos.

    python plot/t90_vs_configuracion.py --salida ../entrega/1.2/t90_vs_config.png

Las configuraciones que no llegan al 90% de particulas usadas dentro de t_max
se marcan aparte: el motor devuelve t90 negativo en ese caso.
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
                        default=config.RESULTADOS / "configs" / "resumen.csv",
                        help="CSV agregado del barrido sobre configuraciones")
    parser.add_argument("--orden", nargs="*", default=None,
                        help="Orden explicito de las configuraciones en el eje x")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    if not args.resumen.exists():
        print(f"Falta el resumen del barrido: {args.resumen}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.resumen)

    incompletas = sorted(datos.loc[datos["t90"] < 0, "configuracion"].unique())
    if incompletas:
        print("No alcanzan F_u = 0.9 dentro de t_max: " + ", ".join(incompletas), file=sys.stderr)

    validas = datos[datos["t90"] >= 0]
    agrupado = validas.groupby("configuracion")["t90"].agg(["mean", "std", "count"]).reset_index()
    if args.orden:
        agrupado["orden"] = agrupado["configuracion"].apply(
            lambda nombre: args.orden.index(nombre) if nombre in args.orden else len(args.orden))
        agrupado = agrupado.sort_values("orden")
    else:
        agrupado = agrupado.sort_values("mean")

    fig, ax = plt.subplots(figsize=config.TAM_FIG)
    ax.errorbar(agrupado["configuracion"], agrupado["mean"], yerr=agrupado["std"].fillna(0.0),
                marker="o", capsize=4, linestyle="none")
    ax.set_xlabel("Configuracion de obstaculos", fontsize=config.FUENTE)
    ax.set_ylabel("Tiempo hasta el 90% de usadas (s)", fontsize=config.FUENTE)
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
