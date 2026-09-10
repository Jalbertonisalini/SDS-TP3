"""Punto 1.1: tiempo de ejecucion vs N — random y hexagonal superpuestos.

    python plot/tiempo_ejecucion_vs_n_combined.py --salida ../entrega/1.1/tiempo_vs_n_combined.png

Compara la escalabilidad del barrido aleatorio (azul) con el hexagonal (verde).
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
    parser.add_argument("--resumen-random", type=Path,
                        default=config.RESULTADOS / "particulas" / "resumen.csv",
                        help="CSV del barrido aleatorio")
    parser.add_argument("--resumen-hex", type=Path,
                        default=config.RESULTADOS / "particulas_hex" / "resumen.csv",
                        help="CSV del barrido hexagonal")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    fig, ax = plt.subplots(figsize=config.TAM_FIG)

    for path, label, color, marker in [
        (args.resumen_random, "Random", "tab:blue", "o"),
        (args.resumen_hex, "Hexagonal", "tab:green", "s"),
    ]:
        if not path.exists():
            print(f"No existe {path}, se saltea.", file=sys.stderr)
            continue
        datos = pd.read_csv(path)
        agrupado = datos.groupby("N")["tiempo_ejecucion_s"].agg(["mean", "std", "count"]).reset_index()
        ax.errorbar(agrupado["N"], agrupado["mean"], yerr=agrupado["std"].fillna(0.0),
                    marker=marker, capsize=4, linestyle="-", color=color, label=label)

    ax.set_xlabel("Cantidad de part\u00edculas", fontsize=config.FUENTE)
    ax.set_ylabel("Tiempo de ejecuci\u00f3n (s)", fontsize=config.FUENTE)
    ax.tick_params(labelsize=config.FUENTE)
    ax.legend(fontsize=config.FUENTE)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=config.DPI)
    print(f"Figura guardada en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
