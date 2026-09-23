"""Punto 1.3: DCM de una realizacion y coeficiente de difusion por ajuste lineal.

    python plot/dcm_vs_tiempo.py \
        --trayectoria ../build/resultados/punto_1_3/dcm/vacia/trayectoria_N100_s1000.csv \
        --tmax-ajuste 1.5 \
        --salida ../entrega/1.3/dcm_vacia.png

El DCM se calcula aca (observables.dcm) a partir de la trayectoria que escribe
el motor con --trajectory; el motor no calcula observables.

El ajuste sigue el metodo de la Teorica 0: se barre la pendiente candidata c,
se calcula el error cuadratico E(c) = sum (DCM_i - c * t_i)^2 y se elige la c
que lo minimiza. En dos dimensiones DCM = 4 D t, de modo que D = c / 4.

El DCM satura cuando las particulas exploran toda la mesa, asi que el ajuste
solo tiene sentido en el tramo inicial: elegirlo con --tmax-ajuste mirando el grafico.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo
import observables

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


def dibujar_dcm(ax, datos, tiempos_ajuste, pendiente, etiqueta="DCM simulado"):
    """DCM simulado y la recta DCM = c t sobre la ventana ajustada, en un eje dado
    (lo reusa punto_1_3.py para armar la grilla de configuraciones)."""
    difusion = pendiente / (2.0 * DIMENSION)
    ax.plot(datos["Time"], datos["DCM"], label=etiqueta)
    ax.plot(tiempos_ajuste, pendiente * tiempos_ajuste, linestyle="--", linewidth=2.5,
            label=f"Ajuste: D = {difusion:#.2g} m$^2$/s")
    estilo.etiquetar_ejes(ax, "Tiempo (s)", "DCM (m$^2$)")


def dibujar_error(ax, pendientes, errores, pendiente):
    """E(c) con su minimo c*, como en la Teorica 0, en un eje dado."""
    ax.plot(pendientes, errores)
    ax.plot([pendiente], [errores.min()], marker="o", markersize=10, linestyle="none",
            color="black", label=f"c* = {pendiente:#.2g} m$^2$/s")
    estilo.etiquetar_ejes(ax)
    estilo.etiquetar_eje_con_potencia(ax, "x", "Pendiente c", "m$^2$/s")
    estilo.etiquetar_eje_con_potencia(ax, "y", "E(c)", "m$^4$")


def graficar_dcm(datos, tiempos_ajuste, pendiente, tmax_grafico, salida):
    # Recortar el eje temporal deja ver el tramo ajustado: con la serie completa
    # la meseta de saturacion ocupa casi todo el grafico.
    if tmax_grafico is not None:
        datos = datos[datos["Time"] <= tmax_grafico]
    fig, ax = estilo.nueva_figura()
    dibujar_dcm(ax, datos, tiempos_ajuste, pendiente)
    ax.legend(loc="best", fontsize=config.FUENTE)
    estilo.guardar(fig, salida)


def graficar_error(pendientes, errores, pendiente, salida):
    fig, ax = estilo.nueva_figura()
    dibujar_error(ax, pendientes, errores, pendiente)
    ax.legend(loc="upper center", fontsize=config.FUENTE)
    estilo.guardar(fig, salida)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trayectoria", type=Path, required=True,
                        help="Trayectoria (--trajectory del motor) de una unica realizacion")
    parser.add_argument("--tmax-ajuste", type=float, required=True,
                        help="Ultimo instante incluido en el ajuste lineal, en s")
    parser.add_argument("--tmax-grafico", type=float, default=None,
                        help="Ultimo instante graficado, en s (default: toda la serie)")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG del DCM")
    parser.add_argument("--salida-error", type=Path, default=None,
                        help="Archivo PNG opcional con la curva de error E(c)")
    args = parser.parse_args()

    if not args.trayectoria.exists():
        print(f"Falta la trayectoria: {args.trayectoria}", file=sys.stderr)
        return 1

    datos = observables.dcm(observables.leer_trayectoria(args.trayectoria))
    ventana = datos[datos["Time"] <= args.tmax_ajuste]
    tiempos = ventana["Time"].to_numpy()
    dcm = ventana["DCM"].to_numpy()

    pendientes, errores, pendiente = barrer_pendiente(tiempos, dcm)
    difusion = pendiente / (2.0 * DIMENSION)
    print(f"Pendiente ajustada: {pendiente:.6f} m^2/s")
    print(f"Coeficiente de difusion D = {difusion:.6f} m^2/s")

    graficar_dcm(datos, tiempos, pendiente, args.tmax_grafico, args.salida)
    if args.salida_error:
        graficar_error(pendientes, errores, pendiente, args.salida_error)

    return 0


if __name__ == "__main__":
    sys.exit(main())
