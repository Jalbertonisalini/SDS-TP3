"""Punto 1.2: F_u(t) de UNA corrida puntual, la misma trayectoria que se usa
para animar el mejor caso de cada experimento (circulo, quad, pared). Pensado
para la diapositiva que sigue a esa animacion en la presentacion.

    python plot/fu_vs_tiempo_corrida.py \
        --trayectoria ../build/resultados/configs/circulo_r0.34/trayectoria_mejor_s1032.csv \
        --salida ../entrega/1.2/circulo_fu_vs_tiempo.png

A diferencia de fu_vs_tiempo.py (que promedia F_u sobre todas las
realizaciones de una configuracion), esto grafica una unica corrida a partir
de su trayectoria completa: no hace falta el registro de goles porque el
estado (fresca/usada) de cada particula ya esta guardado en cada frame.
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo


def fraccion_usada_de_la_corrida(ruta):
    """F_u(t) de una corrida puntual, en cada instante guardado de su trayectoria."""
    datos = pd.read_csv(ruta, usecols=["Time", "ID", "State"])
    datos = datos.drop_duplicates(["Time", "ID"], keep="last")
    tabla = datos.pivot(index="Time", columns="ID", values="State")
    return tabla.index.to_numpy(), tabla.to_numpy().mean(axis=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trayectoria", type=Path, required=True,
                        help="CSV de trayectoria completa de una corrida puntual "
                             "(Time,ID,X,Y,VX,VY,State)")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    instantes, fu = fraccion_usada_de_la_corrida(args.trayectoria)

    fig, ax = estilo.nueva_figura()
    ax.plot(instantes, fu, color="tab:blue", linewidth=2)
    ax.set_xlim(0, instantes[-1])
    ax.set_ylim(0, 1.02)
    estilo.etiquetar_ejes(ax, "Tiempo (s)", "$F_u$")
    # t90: primer instante con F_u >= 0.9, con una linea vertical punteada y
    # su valor como una marca mas del eje del tiempo.
    alcanzado = fu >= config.FRACCION_OBJETIVO
    if alcanzado.any():
        t90 = instantes[alcanzado.argmax()]
        ax.axvline(t90, linestyle="--", color="tab:red", linewidth=2)
        # Se sacan las marcas comunes que quedarian pegadas a la de t90.
        separacion = 0.06 * instantes[-1]
        marcas = [m for m in ax.get_xticks()
                  if 0 <= m <= instantes[-1] and abs(m - t90) > separacion]
        ax.set_xticks(sorted(marcas + [t90]))
        ax.set_xticklabels([f"{t90:.2f}" if m == t90 else f"{m:g}"
                            for m in sorted(marcas + [t90])])
        for etiqueta, m in zip(ax.get_xticklabels(), sorted(marcas + [t90])):
            if m == t90:
                etiqueta.set_color("tab:red")
    estilo.guardar(fig, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
