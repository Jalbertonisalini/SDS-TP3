"""Diagrama estatico de una o mas configuraciones de obstaculos (sin simular),
cada una con su t90 medio +/- desvio si se lo pasas por --etiqueta.

    python plot/diagrama_configs.py \
        --config ../configs/hz_k7_s1004.txt "K=7 (17.91 +/- 1.6 s)" \
        --config ../configs/hz_k6_s1000.txt "K=6 (17.65 +/- 1.6 s)" \
        --salida output/mejores_horizontal.png

Un panel por --config, en grilla. Pensado para comparar geometrias
encontradas por el GA sin gastar tiempo en correr ninguna simulacion.
"""

import argparse
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def leer_obstaculos(ruta):
    obstaculos = []
    for linea in Path(ruta).read_text().splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        x, y, radio = (float(v) for v in limpia.split())
        obstaculos.append((x, y, radio))
    return obstaculos


def dibujar_mesa(ax, obstaculos, titulo=None):
    """titulo=None (o "") no dibuja nada dentro de la figura: para las
    entregas finales esa info (que config es, su t90) va aparte, al costado
    de la figura en la diapositiva, no como titulo embebido."""
    ax.set_xlim(0, config.LARGO)
    ax.set_ylim(0, config.ANCHO)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    inferior = config.ANCHO / 2 - config.ARCO / 2
    superior = config.ANCHO / 2 + config.ARCO / 2
    for x in (0.0, config.LARGO):
        ax.plot([x, x], [inferior, superior], color="tab:green", linewidth=4)
    for x, y, radio in obstaculos:
        ax.add_patch(Circle((x, y), radio, color="0.4"))
    if titulo:
        ax.set_title(titulo, fontsize=config.FUENTE * 0.7)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", nargs=2, action="append", metavar=("ARCHIVO", "ETIQUETA"),
                        required=True, help="Config y su etiqueta (repetible)")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    parser.add_argument("--columnas", type=int, default=None,
                        help="Columnas de la grilla (default: automatico)")
    args = parser.parse_args()

    n = len(args.config)
    columnas = args.columnas or min(n, 3)
    filas = math.ceil(n / columnas)

    fig, ejes = plt.subplots(filas, columnas, figsize=(5 * columnas, 5 * config.ANCHO / config.LARGO * filas))
    ejes = [ejes] if n == 1 else ejes.flatten()

    for ax, (ruta, etiqueta) in zip(ejes, args.config):
        dibujar_mesa(ax, leer_obstaculos(ruta), etiqueta)
    for ax in ejes[n:]:
        ax.axis("off")

    fig.tight_layout()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=config.DPI)
    print(f"Figura guardada en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
