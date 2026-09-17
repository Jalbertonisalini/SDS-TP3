"""Barrido de hiperparametros del perfil de la pared (punto 1.2): como
cambia el mejor fitness del GA al variar la granularidad de los circulos
que arman el muro (--wall-grain) y la cantidad de puntos de control del
perfil (--wall-profile), cada uno con el otro fijo en su valor ganador
("one-factor-at-a-time", no una grilla completa).

    python plot/hparams_pared.py \
        --resumen ../build/resultados/genetico/pared_hparams/resumen.csv \
        --salida output/pared_hparams.png

Espera un CSV con columnas variable,valor,fijo,mejor_fitness (lo escribe
punto_1_2.py durante el barrido). El fitness del GA es un proxy barato para
rankear hiperparametros -- no es t90 medido: el t90 real de la config final
elegida se mide aparte con 100 realizaciones (t90_vs_configuracion.py).
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


def graficar_variable(ax, datos, variable, xlabel):
    subconjunto = datos[datos["variable"] == variable].sort_values("valor")
    if subconjunto.empty:
        ax.text(0.5, 0.5, f"Sin datos para {variable}", ha="center", va="center",
                transform=ax.transAxes)
        return
    ax.plot(subconjunto["valor"], subconjunto["mejor_fitness"], marker="o")
    estilo.etiquetar_ejes(ax, xlabel, "Fitness")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resumen", type=Path, required=True,
                        help="CSV con columnas variable,valor,fijo,mejor_fitness")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    if not args.resumen.exists():
        print(f"Falta el resumen del barrido: {args.resumen}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.resumen)

    fig, (ax_grano, ax_perfil) = plt.subplots(
        1, 2, figsize=(2 * config.TAM_FIG[0] / 1.3, config.TAM_FIG[1]))
    graficar_variable(ax_grano, datos, "grain", "Radio de los circulos del muro (m)")
    graficar_variable(ax_perfil, datos, "profile", "Puntos de control del perfil")

    estilo.guardar(fig, args.salida)
    print(datos.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
