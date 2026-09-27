"""Diagrama de flujo del algoritmo genetico (punto 1.2), siguiendo el orden
real de Optimizer::run (src/Optimizer.cpp).

    python plot/diagrama_flujo_ga.py --salida ../entrega/1.2/diagrama_flujo_ga.png

Diferencias con el flujo generico de un GA que el diagrama deja a la vista:
- La evaluacion esta dentro del ciclo: cada generacion sortea semillas
  nuevas, comunes a toda la poblacion (Common Random Numbers).
- La condicion de parada es un numero fijo de generaciones.
- La nueva poblacion se completa en un ciclo interno (seleccion, cruza y
  mutacion de a un hijo) despues de copiar a los individuos de elite.

El ciclo de una generacion se dibuja como un rectangulo: la fila de arriba
va de izquierda a derecha y la de abajo vuelve de derecha a izquierda.
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo

# Mismo formato que el diagrama de modulos (docs/uml/modulos.puml): Helvetica,
# nombres en negrita, cajas blancas con borde oscuro y flechas grises. Arial va
# primero porque matplotlib solo lee la cara regular de Helvetica.ttc y la
# negrita no se veria; es practicamente la misma letra.
FUENTE_FAMILIA = ["Arial", "Helvetica", "DejaVu Sans"]
RELLENO = "#FFFFFF"
BORDE = "#2D3748"
TEXTO = "#1A202C"
FLECHA = "#4A5568"
ETIQUETA = TEXTO

ANCHO_CAJA = 3.2
ALTO_CAJA = 0.8
MEDIO_DIAMANTE = (1.35, 0.75)  # semiejes horizontal y vertical
FUENTE = 15

SEPARACION_X = 3.9
FILA_INICIO = 1.7
FILA_ARRIBA = 0.0
FILA_ABAJO = -2.0
CARRIL_RETORNO = -3.2  # por donde vuelve el ciclo interno, debajo de la fila de abajo

# clave: (tipo, texto, columna, fila)
NODOS = {
    "inicio": ("caja", "Inicializar población", 1, FILA_INICIO),
    "completa": ("diamante", "¿Población\ncompleta?", 0, FILA_ARRIBA),
    "semillas": ("caja", "Sortear semillas", 1, FILA_ARRIBA),
    "evaluar": ("caja", "Evaluar población", 2, FILA_ARRIBA),
    "parada": ("diamante", "¿Última\ngeneración?", 3, FILA_ARRIBA),
    "mejor": ("caja", "Mejor individuo", 4, FILA_ARRIBA),
    "elite": ("caja", "Elitismo", 3, FILA_ABAJO),
    "seleccion": ("caja", "Selección", 2, FILA_ABAJO),
    "cruza": ("caja", "Cruza", 1, FILA_ABAJO),
    "mutacion": ("caja", "Mutación", 0, FILA_ABAJO),
}


def centro(clave):
    _, _, columna, fila = NODOS[clave]
    return columna * SEPARACION_X, fila


def medio_ancho(clave):
    return MEDIO_DIAMANTE[0] if NODOS[clave][0] == "diamante" else ANCHO_CAJA / 2


def medio_alto(clave):
    return MEDIO_DIAMANTE[1] if NODOS[clave][0] == "diamante" else ALTO_CAJA / 2


def dibujar_nodo(ax, clave):
    tipo, texto, _, _ = NODOS[clave]
    x, y = centro(clave)
    if tipo == "caja":
        forma = FancyBboxPatch((x - ANCHO_CAJA / 2, y - ALTO_CAJA / 2), ANCHO_CAJA, ALTO_CAJA,
                               boxstyle="round,pad=0.02,rounding_size=0.14")
    else:
        dx, dy = MEDIO_DIAMANTE
        forma = Polygon([(x, y + dy), (x + dx, y), (x, y - dy), (x - dx, y)], closed=True)
    forma.set(facecolor=RELLENO, edgecolor=BORDE, linewidth=1.8)
    ax.add_patch(forma)
    ax.text(x, y, texto, ha="center", va="center", color=TEXTO, fontsize=FUENTE,
            fontfamily=FUENTE_FAMILIA, fontweight="bold", linespacing=1.1)


def flecha(ax, puntos):
    """Polilinea con punta de flecha en el ultimo tramo."""
    xs, ys = zip(*puntos)
    ax.plot(xs[:-1], ys[:-1], color=FLECHA, linewidth=1.6, solid_capstyle="butt")
    ax.annotate("", xy=puntos[-1], xytext=puntos[-2],
                arrowprops=dict(arrowstyle="-|>", color=FLECHA, linewidth=1.6,
                                mutation_scale=16, shrinkA=0, shrinkB=0))


def etiqueta(ax, x, y, texto, ha="center"):
    ax.text(x, y, texto, ha=ha, va="center", color=ETIQUETA, fontsize=FUENTE - 1,
            fontfamily=FUENTE_FAMILIA, fontweight="bold")


def horizontal(ax, desde, hasta):
    """Flecha recta entre dos nodos de la misma fila."""
    (x0, y), (x1, _) = centro(desde), centro(hasta)
    signo = 1 if x1 > x0 else -1
    flecha(ax, [(x0 + signo * medio_ancho(desde), y), (x1 - signo * medio_ancho(hasta), y)])


def vertical(ax, desde, hasta):
    """Flecha recta entre dos nodos de la misma columna."""
    (x, y0), (_, y1) = centro(desde), centro(hasta)
    signo = 1 if y1 > y0 else -1
    flecha(ax, [(x, y0 + signo * medio_alto(desde)), (x, y1 - signo * medio_alto(hasta))])


def flechas_del_ciclo(ax):
    vertical(ax, "inicio", "semillas")
    horizontal(ax, "semillas", "evaluar")
    horizontal(ax, "evaluar", "parada")
    horizontal(ax, "parada", "mejor")
    vertical(ax, "parada", "elite")
    horizontal(ax, "elite", "seleccion")
    horizontal(ax, "seleccion", "cruza")
    horizontal(ax, "cruza", "mutacion")
    vertical(ax, "mutacion", "completa")
    horizontal(ax, "completa", "semillas")


def ciclo_interno(ax):
    """Si todavia faltan hijos, vuelve a seleccionar padres."""
    x_completa, y_completa = centro("completa")
    x_seleccion, y_seleccion = centro("seleccion")
    x_izquierda = x_completa - medio_ancho("mutacion") - 0.5
    flecha(ax, [(x_completa - MEDIO_DIAMANTE[0], y_completa), (x_izquierda, y_completa),
                (x_izquierda, CARRIL_RETORNO), (x_seleccion, CARRIL_RETORNO),
                (x_seleccion, y_seleccion - ALTO_CAJA / 2)])


def etiquetas_de_decision(ax):
    dx, dy = MEDIO_DIAMANTE
    x_parada, y_parada = centro("parada")
    etiqueta(ax, x_parada + dx + 0.15, y_parada + 0.3, "Sí", ha="left")
    etiqueta(ax, x_parada + 0.2, y_parada - dy - 0.3, "No", ha="left")
    x_completa, y_completa = centro("completa")
    etiqueta(ax, x_completa + dx + 0.15, y_completa + 0.3, "Sí", ha="left")
    etiqueta(ax, x_completa - dx - 0.15, y_completa + 0.3, "No", ha="right")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    fig, ax = plt.subplots(figsize=(16, 5.5))
    for clave in NODOS:
        dibujar_nodo(ax, clave)
    flechas_del_ciclo(ax)
    ciclo_interno(ax)
    etiquetas_de_decision(ax)

    ax.set_xlim(-ANCHO_CAJA / 2 - 0.8, 4 * SEPARACION_X + ANCHO_CAJA / 2 + 0.2)
    ax.set_ylim(CARRIL_RETORNO - 0.3, FILA_INICIO + ALTO_CAJA / 2 + 0.2)
    ax.set_aspect("equal")
    ax.axis("off")
    estilo.guardar(fig, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
