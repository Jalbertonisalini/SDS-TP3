"""Punto 1.3: DCM de una realizacion y coeficiente de difusion por ajuste lineal.

    python plot/dcm_vs_tiempo.py --serie ../build/resultados/configs/vacia/N100_s1000.csv \
                                 --tmax-ajuste 5 \
                                 --salida ../entrega/1.3/dcm_vacia.png

El ajuste sigue el metodo de la Teorica 0: se barre la pendiente candidata c,
se calcula el error cuadratico E(c) = sum (DCM_i - c * t_i)^2 y se elige la c
que lo minimiza. En dos dimensiones DCM = 4 D t, de modo que D = c / 4.

El DCM satura cuando las particulas exploran toda la mesa, asi que el ajuste
solo tiene sentido en el tramo inicial: elegirlo con --tmax-ajuste mirando el grafico.
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

DIMENSION = 2


def barrer_pendiente(tiempos, dcm, cantidad=2000):
    """Devuelve (pendientes, errores, pendiente_optima) segun el metodo de la Teorica 0."""
    if np.dot(tiempos, tiempos) == 0.0:
        raise ValueError("La serie no tiene ningun instante distinto de cero.")

    # El minimo analitico del error cuadratico da el centro del barrido.
    centro = np.dot(tiempos, dcm) / np.dot(tiempos, tiempos)
    pendientes = np.linspace(0.5 * centro, 1.5 * centro, cantidad)
    errores = np.array([np.sum((dcm - c * tiempos) ** 2) for c in pendientes])
    return pendientes, errores, pendientes[int(np.argmin(errores))]


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serie", type=Path, required=True,
                        help="CSV de serie compacta de una unica realizacion")
    parser.add_argument("--tmax-ajuste", type=float, required=True,
                        help="Ultimo instante incluido en el ajuste lineal, en s")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG del DCM")
    parser.add_argument("--salida-error", type=Path, default=None,
                        help="Archivo PNG opcional con la curva de error E(c)")
    args = parser.parse_args()

    if not args.serie.exists():
        print(f"Falta la serie: {args.serie}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.serie)
    ventana = datos[datos["Time"] <= args.tmax_ajuste]
    tiempos = ventana["Time"].to_numpy()
    dcm = ventana["MSD"].to_numpy()

    pendientes, errores, pendiente = barrer_pendiente(tiempos, dcm)
    difusion = pendiente / (2.0 * DIMENSION)
    print(f"Pendiente ajustada: {pendiente:.6f} m^2/s")
    print(f"Coeficiente de difusion D = {difusion:.6f} m^2/s")

    fig, ax = plt.subplots(figsize=config.TAM_FIG)
    ax.plot(datos["Time"], datos["MSD"], marker="o", markersize=3, linestyle="none",
            label="DCM simulado")
    ax.plot(tiempos, pendiente * tiempos, linestyle="--",
            label=f"Ajuste: D = {difusion:.4f} m$^2$/s")
    ax.set_xlabel("Tiempo (s)", fontsize=config.FUENTE)
    ax.set_ylabel("Desplazamiento cuadratico medio (m$^2$)", fontsize=config.FUENTE)
    ax.tick_params(labelsize=config.FUENTE)
    ax.legend(loc="best", fontsize=config.FUENTE)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=config.DPI)
    print(f"Figura guardada en {args.salida}")

    if args.salida_error:
        fig_error, ax_error = plt.subplots(figsize=config.TAM_FIG)
        ax_error.plot(pendientes, errores)
        ax_error.axvline(pendiente, linestyle="--", color="black", alpha=0.6)
        ax_error.set_xlabel("Pendiente candidata (m$^2$/s)", fontsize=config.FUENTE)
        ax_error.set_ylabel("Error cuadratico", fontsize=config.FUENTE)
        ax_error.tick_params(labelsize=config.FUENTE)
        ax_error.grid(alpha=0.3)
        fig_error.tight_layout()
        args.salida_error.parent.mkdir(parents=True, exist_ok=True)
        fig_error.savefig(args.salida_error, dpi=config.DPI)
        print(f"Figura guardada en {args.salida_error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
