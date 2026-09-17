"""Estilo compartido de figuras (guia de formato de la catedra, ver TP3).

Reglas que encapsula, para no repetirlas (mal) en cada script de plot:

- Las figuras no llevan titulo ni leyenda de parametros fijos dentro de la
  imagen (`etiquetar_ejes` nunca llama a `set_title`/`suptitle`): esa info
  va aparte, como texto en la diapositiva. Los ejes si llevan nombre en
  palabras + unidades MKS entre parentesis, con tamano de fuente similar
  al resto del texto (`config.FUENTE`).
- Numeros grandes/chicos en los ejes van en notacion cientifica con
  potencia de 10 (superindice), nunca "1e2" (`notacion_cientifica`).
- Un observable con su error se expresa con las cifras significativas que
  marca el error (Teorica 0), no con un monton de decimales sueltos
  (`formatear_valor`).

    from plot import estilo
    fig, ax = estilo.nueva_figura()
    ax.plot(x, y)
    estilo.etiquetar_ejes(ax, "Radio del obstaculo (m)", "Tiempo hasta el 90% de usadas (s)")
    estilo.guardar(fig, ruta_salida)
"""

import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def nueva_figura(figsize=None):
    """Figura y eje unico con el tamano estandar del TP (config.TAM_FIG)."""
    return plt.subplots(figsize=figsize or config.TAM_FIG)


def etiquetar_ejes(ax, xlabel=None, ylabel=None, grid=True):
    """Labels en palabras + unidades, tamano de fuente uniforme. Nunca pone
    titulo: esa informacion (parametros fijos de la corrida) va aparte, al
    costado de la figura en la diapositiva, no dentro de la imagen."""
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=config.FUENTE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=config.FUENTE)
    ax.tick_params(labelsize=config.FUENTE)
    if grid:
        ax.grid(alpha=0.3)


def notacion_cientifica(ax, eje="y"):
    """Fuerza potencias de 10 con superindice (1x10^2, no 1e2) en el eje
    pedido, para cuando los valores son muy grandes o muy chicos."""
    ax.ticklabel_format(axis=eje, style="sci", scilimits=(-2, 3), useMathText=True)
    formateador = ax.yaxis if eje == "y" else ax.xaxis
    formateador.get_offset_text().set_fontsize(config.FUENTE)


def columnas_grilla(n):
    """Columnas para una grilla de n paneles lo mas cuadrada posible (4 ->
    2x2, 6 -> 3x2, 9 -> 3x3), en vez de amontonar todo en una sola fila."""
    return math.ceil(math.sqrt(n))


def guardar(fig, ruta):
    ruta = Path(ruta)
    fig.tight_layout()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    # bbox_inches="tight": sin esto, un ylabel largo (ej. "Mejor fitness del
    # GA (t90 en s, o penalizacion)") puede quedar recortado en el borde
    # izquierdo -- tight_layout() solo ajusta el espaciado INTERNO entre ejes
    # y no siempre reserva margen de figura suficiente para labels rotados.
    fig.savefig(ruta, dpi=config.DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Figura guardada en {ruta}")


def _decimales_por_desvio(desvio):
    """Cantidad de decimales para que `desvio` quede con 1 cifra
    significativa (Teorica 0: el error manda cuantos digitos tiene sentido
    mostrar). Sin desvio valido, no redondea (deja 3 decimales por default)."""
    if desvio is None or desvio == 0 or math.isnan(desvio):
        return 3
    exponente = math.floor(math.log10(abs(desvio)))
    return max(-exponente, 0)


def formatear_valor(media, desvio=None, unidad=""):
    """"13.5 ± 0.8 s": media y desvio redondeados a las cifras
    significativas que marca el desvio, con la unidad al final si se pasa."""
    decimales = _decimales_por_desvio(desvio)
    formato = f"{{:.{decimales}f}}"
    texto = formato.format(round(media, decimales))
    if desvio is not None and not math.isnan(desvio):
        texto += f" ± {formato.format(round(desvio, decimales))}"
    if unidad:
        texto += f" {unidad}"
    return texto
