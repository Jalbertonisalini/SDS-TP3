"""<t90> de varias configuraciones como barras horizontales con su desvio,
con un dibujo de cada mesa en el eje y en lugar de su nombre: asi se ve de
un vistazo que geometria corresponde a cada barra.

    from plot import barras_configs
    barras_configs.graficar([
        {"etiqueta": "K=9", "obstaculos": [...], "media": 14.2, "desvio": 1.9},
        {"etiqueta": "Pared", "obstaculos": [...], "media": 13.6, "desvio": 1.5,
         "perfil": 6},   # opcional: dibuja la linea de perfil de la pared
    ], "Tiempo ...", ruta_salida)

Las barras van en el orden de la lista, de arriba hacia abajo.

`etiquetas=False` no escribe el nombre de cada config al lado de su mesa (el
dibujo alcanza). `decimales=None` deja solo la barra con su error; con un
entero escribe "media ± desvio s" al final de cada barra con esos decimales.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import diagrama_configs
import estilo
import perfil_pared

# Separacion vertical entre mesas, relativa a la altura de cada una.
SEPARACION = 0.12


def graficar(items, xlabel, salida, etiquetas=True, decimales=None):
    n = len(items)
    # Cada fila tiene la proporcion de la mesa (L/W) en la columna de dibujos.
    # Proporcion ~2.4:1, la del lugar libre de la diapositiva (\\figancha
    # en presentation.tex: casi todo el ancho de pagina bajo el titulo), para
    # que la figura lo llene sin que sobre ni alto ni ancho.
    ancho_fig = 13 if etiquetas else 14.5  # sin nombres, el ancho va a las barras
    alto_fila = 4.1 / (n + (n - 1) * SEPARACION)
    ancho_mesa = alto_fila * config.LARGO / config.ANCHO
    fig = plt.figure(figsize=(ancho_fig, alto_fila * (n + (n - 1) * SEPARACION) + 1))
    grilla = fig.add_gridspec(n, 2, width_ratios=[ancho_mesa, ancho_fig - ancho_mesa - 2.2],
                              hspace=SEPARACION, wspace=0.03)

    for i, item in enumerate(items):
        ax_mesa = fig.add_subplot(grilla[i, 0])
        diagrama_configs.dibujar_mesa(ax_mesa, item["obstaculos"])
        if item.get("perfil"):
            perfil_pared.dibujar_perfil(ax_mesa, item["obstaculos"], item["perfil"])
        if etiquetas:
            ax_mesa.set_ylabel(item["etiqueta"], fontsize=config.FUENTE, rotation=0,
                               ha="right", va="center", labelpad=12)

    # Eje de barras que cubre todas las filas: con ylim (0, 1) la fila i
    # queda centrada en y = 1 - (i * (a + g) + a / 2), con a la altura de
    # cada fila y g la separacion, en fraccion de la altura total.
    ax = fig.add_subplot(grilla[:, 1])
    a = 1 / (n + (n - 1) * SEPARACION)
    g = a * SEPARACION
    ys = [1 - (i * (a + g) + a / 2) for i in range(n)]
    medias = [item["media"] for item in items]
    desvios = [item["desvio"] for item in items]
    ax.barh(ys, medias, height=a * 0.62, xerr=desvios, color="tab:blue",
            error_kw={"ecolor": "black", "elinewidth": 2, "capsize": 6, "capthick": 2})
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    tope = max(m + d for m, d in zip(medias, desvios))
    ax.set_xlim(0, tope * 1.05)
    if decimales is not None:
        textos = [ax.text(media + desvio + tope * 0.015, y,
                          f"{media:.{decimales}f} ± {desvio:.{decimales}f} s",
                          va="center", fontsize=config.FUENTE)
                  for y, media, desvio in zip(ys, medias, desvios)]
        # Agranda el eje x hasta que el texto mas largo quede adentro: se mide
        # el ancho real de cada texto y se lo pasa a unidades de datos.
        for _ in range(3):
            fig.canvas.draw()
            derecha = max(ax.transData.inverted().transform(
                t.get_window_extent().corners()[-1])[0] for t in textos)
            ax.set_xlim(0, max(tope * 1.05, derecha + tope * 0.03))
    estilo.etiquetar_ejes(ax, xlabel=xlabel)
    ax.grid(False)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, dpi=config.DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Figura guardada en {salida}")
