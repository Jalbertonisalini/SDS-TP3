"""Fotos fijas (no animacion) de como converge la poblacion del GA, una por
cada generacion pedida.

    python plot/snapshots_poblacion.py \
        --population-log ../build/resultados/genetico/quad/K9_s1013/poblacion \
        --generaciones 0 2 4 6 8 10 \
        --salida output/snapshots_poblacion_k9.png

Lee el directorio que escribe `optimizador --population-log` (un CSV por
generacion loguada). Un panel por generacion pedida (si esa generacion no
fue logueada, se usa la logueada mas cercana). Dibuja los obstaculos de
TODA la poblacion de esa generacion superpuestos con transparencia (mas
oscuro = mas individuos coinciden ahi), coloreados segun fitness (mas
claro = mejor). Por default agrega un ultimo panel con la generacion final
de la corrida, aunque no este en --generaciones.

Con --solo-mejor, el "mejor de la ultima generacion logueada" no es
necesariamente el mismo individuo que gano de verdad (el optimizador
reevalua a toda la poblacion -- incluidos los elitistas -- con semillas
nuevas cada generacion, asi que el mejor historico puede haber quedado
en una generacion anterior). Pasando --config-final se reemplaza ese
ultimo panel por la geometria realmente ganadora, sin ambiguedad.
"""

import argparse
import math
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo
import perfil_pared
from convergencia_poblacion import leer_poblacion, dibujar_mesa


def leer_obstaculos(ruta):
    obstaculos = []
    for linea in Path(ruta).read_text().splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        x, y, radio = (float(v) for v in limpia.split())
        obstaculos.append((x, y, radio))
    return obstaculos


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--population-log", type=Path, required=True,
                        help="Directorio que escribe optimizador --population-log")
    parser.add_argument("--generaciones", type=int, nargs="+", required=True,
                        help="Generaciones a mostrar, ej. 0 2 4 6 8 10")
    parser.add_argument("--sin-ultima", action="store_true",
                        help="No agregar automaticamente un panel con la ultima generacion")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    parser.add_argument("--columnas", type=int, default=None,
                        help="Columnas de la grilla (default: la mas cuadrada posible, ej. "
                             "4 paneles -> 2x2, 6 paneles -> 3x2)")
    parser.add_argument("--solo-mejor", action="store_true",
                        help="En vez de la nube de toda la poblacion, dibuja unicamente el "
                             "individuo de menor fitness de esa generacion, en gris solido "
                             "(el degrade por fitness no tiene sentido para un solo individuo)")
    parser.add_argument("--config-final", type=Path, default=None,
                        help="Config ganadora real (formato x y r de simulador --config). Si se "
                             "pasa junto con --solo-mejor, reemplaza el ultimo panel (el que "
                             "seria 'la ultima generacion') por esta geometria en vez de la del "
                             "mejor de la generacion logueada mas cercana al final -- son "
                             "distintas por como el optimizador reevalua fitness cada generacion")
    parser.add_argument("--config-final-etiqueta", default="Ganador final",
                        help="Texto del ultimo panel cuando se pasa --config-final "
                             "(default: 'Ganador final')")
    parser.add_argument("--titulo-panel", choices=["completo", "minimo", "ninguno"],
                        default="completo",
                        help="completo: 'Generacion N  <t90>_5 = X s' (default). "
                             "minimo: solo 'Generacion N', sin el valor de fitness -- para "
                             "entregas donde ese numero va aparte, al costado de la figura. "
                             "ninguno: sin texto embebido en el panel")
    parser.add_argument("--perfil-pared", type=int, default=None, metavar="N",
                        help="Si la corrida es de pared (optimizador --wall-profile N), dibuja "
                             "encima la linea punteada del perfil interpolado y sus N puntos "
                             "de control (solo con --solo-mejor)")
    args = parser.parse_args()

    if not args.population_log.exists():
        print(f"Falta el directorio de poblacion: {args.population_log}", file=sys.stderr)
        return 1

    datos = leer_poblacion(args.population_log)
    disponibles = sorted(datos["generacion"].unique())

    pedidas = list(dict.fromkeys(args.generaciones))  # sin duplicados, preserva orden
    if not args.sin_ultima and disponibles[-1] not in pedidas:
        pedidas.append(disponibles[-1])

    # cada generacion pedida usa la logueada mas cercana disponible
    generaciones = [min(disponibles, key=lambda g: abs(g - pedida)) for pedida in pedidas]

    # paneles: lista de ("generacion", numero) o ("final", obstaculos, etiqueta).
    # El ultimo panel se reemplaza por la config ganadora real si se paso
    # --config-final: "mejor de la generacion logueada mas cercana al final"
    # y "la que gano de verdad" pueden no ser el mismo individuo (ver
    # docstring del modulo).
    paneles = [("generacion", g) for g in generaciones]
    if args.config_final is not None and args.solo_mejor:
        paneles[-1] = ("final", leer_obstaculos(args.config_final), args.config_final_etiqueta)

    norm = Normalize(vmin=datos["fitness"].min(), vmax=datos["fitness"].max())
    cmap = plt.get_cmap("viridis_r")  # menor fitness (mejor) = mas claro

    n = len(paneles)
    columnas = args.columnas or estilo.columnas_grilla(n)
    filas = math.ceil(n / columnas)
    fig, ejes = plt.subplots(filas, columnas,
                             figsize=(5 * columnas, 5 * config.ANCHO / config.LARGO * filas))
    ejes = [ejes] if n == 1 else ejes.flatten()

    for ax, panel in zip(ejes, paneles):
        dibujar_mesa(ax)
        if panel[0] == "final":
            _, obstaculos, etiqueta = panel
            for x, y, radio in obstaculos:
                ax.add_patch(Circle((x, y), radio, color="0.4", linewidth=0))
            if args.perfil_pared:
                perfil_pared.dibujar_perfil(ax, obstaculos, args.perfil_pared)
            if args.titulo_panel != "ninguno":
                ax.set_title(etiqueta, fontsize=config.FUENTE * 0.6)
            continue

        generacion = panel[1]
        cuadro = datos[datos["generacion"] == generacion]
        if args.solo_mejor:
            mejor_id = cuadro.loc[cuadro["fitness"].idxmin(), "individuo"]
            individuo = cuadro[cuadro["individuo"] == mejor_id]
            # Solido, no degrade: es un unico individuo, no una poblacion
            # para comparar por fitness.
            for _, fila in individuo.iterrows():
                ax.add_patch(Circle((fila["x"], fila["y"]), fila["r"], color="0.4", linewidth=0))
            if args.perfil_pared:
                perfil_pared.dibujar_perfil(ax, individuo[["x", "y", "r"]].to_numpy(),
                                            args.perfil_pared)
        else:
            for _, individuo in cuadro.groupby("individuo"):
                color = cmap(norm(individuo["fitness"].iloc[0]))
                for _, fila in individuo.iterrows():
                    ax.add_patch(Circle((fila["x"], fila["y"]), fila["r"], color=color, alpha=0.12,
                                        linewidth=0))
        mejor = cuadro["fitness"].min()
        if args.titulo_panel == "completo":
            ax.set_title(f"Generacion {generacion}    "
                         f"{estilo.t90_promedio(estilo.SEMILLAS_GA)} = {mejor:.2f} s",
                        fontsize=config.FUENTE * 0.6)
        elif args.titulo_panel == "minimo":
            ax.set_title(f"Generacion {generacion}", fontsize=config.FUENTE * 0.6)
    for ax in ejes[n:]:
        ax.axis("off")

    fig.tight_layout()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=config.DPI)
    print(f"Figura guardada en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
