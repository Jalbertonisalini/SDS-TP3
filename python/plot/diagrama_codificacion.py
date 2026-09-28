"""Como arma el GA cada geometria a partir de sus genes (punto 1.2): todos los
obstaculos en el mismo gris semitransparente, los genes libres marcados con
un borde azul (o un marcador azul en el perfil de pared) y los ejes de
simetria punteados. Sin leyenda embebida (bbox_inches="tight" la recorta con
un tamano distinto por figura segun cuanto texto tenga, lo que rompe el
alineado de las 3 en la diapositiva) -- la leyenda de colores va aparte, en
LaTeX, debajo de cada figura.

    python plot/diagrama_codificacion.py --circulo 0.2 \
        --salida ../entrega/1.2/codificacion_circulo.png
    python plot/diagrama_codificacion.py --quad ../configs/ga_k9_s1003.txt \
        --salida ../entrega/1.2/codificacion_quad.png
    python plot/diagrama_codificacion.py --pared ../configs/pared_ganadora.txt --perfil 6 \
        --salida ../entrega/1.2/codificacion_pared.png

Circulo: un unico obstaculo centrado; el unico parametro es R (el radio
que se dibuja es solo ilustrativo, los barridos van en la diapositiva).
Quad: solo los obstaculos del cuadrante inferior izquierdo (y el central, que
solo tiene radio libre) son genes; los otros 3 cuadrantes son espejos.
Pared: los genes son las N profundidades de la cara izquierda en y <= W/2;
el resto del perfil (y los circulos que lo rellenan) sale por simetria.
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo
import perfil_pared
from diagrama_configs import dibujar_mesa, leer_obstaculos

GEN = "tab:blue"


def ejes_de_simetria(ax):
    kw = dict(color="black", linestyle=":", linewidth=1.2, zorder=5)
    ax.axvline(config.LARGO / 2, **kw)
    ax.axhline(config.ANCHO / 2, **kw)


def circulo(ax, radio):
    dibujar_mesa(ax, [])
    cx, cy = config.LARGO / 2, config.ANCHO / 2
    ax.add_patch(Circle((cx, cy), radio, color=config.COLOR_OBSTACULO,
                        alpha=config.ALPHA_OBSTACULO, linewidth=0))
    ax.annotate("", xy=(cx + radio, cy), xytext=(cx, cy),
                arrowprops=dict(arrowstyle="->", color=GEN, linewidth=2))
    ax.plot(cx, cy, marker="o", markersize=5, color=GEN)
    ax.text(cx + radio / 2, cy + 0.012, "R", ha="center", va="bottom", color=GEN,
            fontsize=config.FUENTE, fontstyle="italic")


def quad(ax, obstaculos):
    dibujar_mesa(ax, [])
    eps = 1e-6
    for x, y, r in obstaculos:
        centro = abs(x - config.LARGO / 2) < eps and abs(y - config.ANCHO / 2) < eps
        libre = centro or (x < config.LARGO / 2 and y < config.ANCHO / 2)
        borde = dict(edgecolor=GEN, linewidth=2.5) if libre else dict(linewidth=0)
        ax.add_patch(Circle((x, y), r, facecolor=config.COLOR_OBSTACULO,
                            alpha=config.ALPHA_OBSTACULO, **borde))
    ejes_de_simetria(ax)


def pared(ax, obstaculos, n):
    dibujar_mesa(ax, [])
    for x, y, r in obstaculos:
        ax.add_patch(Circle((x, y), r, color=config.COLOR_OBSTACULO,
                            alpha=config.ALPHA_OBSTACULO, linewidth=0))
    genes = perfil_pared.dibujar_perfil(ax, obstaculos, n, color="0.3")
    ys = np.linspace(0, config.ANCHO / 2, n)
    ax.plot(genes, ys, linestyle="none", marker="o", markersize=9, color=GEN,
            markeredgecolor="white", markeredgewidth=1, zorder=6)
    ejes_de_simetria(ax)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--circulo", type=float, metavar="R",
                       help="Radio (ilustrativo) del circulo centrado")
    grupo.add_argument("--quad", type=Path, help="Config de un ganador quad")
    grupo.add_argument("--pared", type=Path, help="Config de una pared")
    parser.add_argument("--perfil", type=int, default=None,
                        help="Puntos de control de la pared (obligatorio con --pared)")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()
    if args.pared and not args.perfil:
        parser.error("--pared necesita --perfil")

    fig, ax = plt.subplots(figsize=(8, 8 * config.ANCHO / config.LARGO))
    if args.circulo:
        circulo(ax, args.circulo)
    elif args.quad:
        quad(ax, leer_obstaculos(args.quad))
    else:
        pared(ax, leer_obstaculos(args.pared), args.perfil)
    estilo.guardar(fig, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
