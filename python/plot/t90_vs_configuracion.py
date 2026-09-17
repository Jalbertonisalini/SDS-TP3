"""Punto 1.2: <t90> con barra de error para cada configuracion de obstaculos.

    python plot/t90_vs_configuracion.py --salida ../entrega/1.2/t90_vs_config.png

Ademas de la media +/- desvio, anota el valor numerico (con las cifras
significativas del desvio) arriba de cada punto.

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo


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

    posiciones = list(range(len(agrupado)))

    fig, ax = estilo.nueva_figura()
    ax.errorbar(posiciones, agrupado["mean"], yerr=agrupado["std"].fillna(0.0),
                marker="o", capsize=4, linestyle="none", color="tab:orange", markersize=8,
                linewidth=2)
    for pos, fila in zip(posiciones, agrupado.itertuples()):
        desvio = fila.std if fila.std == fila.std else 0.0  # NaN-safe (1 sola realizacion)
        etiqueta = f"{fila.mean:.2f} ± {desvio:.2f}"
        # Ancla arriba de la punta de la barra de error (mean + desvio), no
        # del punto medio, para que el numero no quede pisando la barra.
        ax.annotate(etiqueta, (pos, fila.mean + desvio), textcoords="offset points",
                   xytext=(0, 14), ha="center", va="bottom", fontsize=config.FUENTE * 0.7)
    ax.margins(y=0.18)  # aire arriba para las anotaciones, si no quedan pegadas al borde
    ax.set_xticks(posiciones)
    ax.set_xticklabels(agrupado["configuracion"])
    estilo.etiquetar_ejes(ax, "Configuracion de obstaculos", "t90 (s)")

    estilo.guardar(fig, args.salida)
    print(agrupado.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
