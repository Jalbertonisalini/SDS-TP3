"""Animacion del sistema a partir de una trayectoria completa.

    python plot/animacion.py --trayectoria ../build/resultados/configs/embudo/trayectoria_s1000.csv \
                             --obstaculos ../configs/embudo.txt \
                             --salida output/embudo.mp4 \
                             --fotograma ../entrega/1.2/embudo_frame.png

Las particulas frescas se dibujan en azul y las usadas en rojo. Los obstaculos
salen del mismo archivo de configuracion que recibio el motor: la trayectoria no
los repite.

Genera MP4 con el ffmpeg que trae imageio-ffmpeg, asi que no hace falta ningun
binario instalado a mano. Para la presentacion hace falta ademas un fotograma
representativo: --fotograma lo guarda como PNG.
"""

import argparse
import sys
from pathlib import Path

import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

COLORES = {0: "tab:blue", 1: "tab:red"}


def leer_obstaculos(ruta):
    if ruta is None:
        return []
    obstaculos = []
    for linea in Path(ruta).read_text().splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        x, y, radio = (float(valor) for valor in limpia.split())
        obstaculos.append((x, y, radio))
    return obstaculos


def dibujar_mesa(ax, obstaculos):
    ax.set_xlim(0, config.LARGO)
    ax.set_ylim(0, config.ANCHO)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])

    # Los arcos, centrados en el medio de cada pared corta.
    inferior = config.ANCHO / 2 - config.ARCO / 2
    superior = config.ANCHO / 2 + config.ARCO / 2
    for x in (0.0, config.LARGO):
        ax.plot([x, x], [inferior, superior], color="tab:green", linewidth=4)

    for x, y, radio in obstaculos:
        ax.add_patch(Circle((x, y), radio, color="0.4"))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trayectoria", type=Path, required=True,
                        help="CSV de trayectoria completa (Time,ID,X,Y,VX,VY,State)")
    parser.add_argument("--obstaculos", type=Path, default=None,
                        help="Archivo de configuracion de obstaculos usado en la corrida")
    parser.add_argument("--salida", type=Path, default=None, help="Archivo MP4 de salida")
    parser.add_argument("--fotograma", type=Path, default=None,
                        help="Guarda un unico cuadro representativo como PNG")
    parser.add_argument("--instante", type=float, default=None,
                        help="Tiempo del cuadro representativo, en s (default: el ultimo)")
    parser.add_argument("--fps", type=int, default=25, help="Cuadros por segundo del MP4")
    args = parser.parse_args()

    datos = pd.read_csv(args.trayectoria)
    obstaculos = leer_obstaculos(args.obstaculos)
    instantes = sorted(datos["Time"].unique())

    if args.fotograma:
        objetivo = args.instante if args.instante is not None else instantes[-1]
        cuadro = datos[datos["Time"] == min(instantes, key=lambda t: abs(t - objetivo))]
        fig, ax = plt.subplots(figsize=(10, 10 * config.ANCHO / config.LARGO))
        dibujar_mesa(ax, obstaculos)
        for estado, color in COLORES.items():
            subconjunto = cuadro[cuadro["State"] == estado]
            for _, fila in subconjunto.iterrows():
                ax.add_patch(Circle((fila["X"], fila["Y"]), config.RADIO, color=color))
        fig.tight_layout()
        args.fotograma.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.fotograma, dpi=config.DPI)
        plt.close(fig)
        print(f"Fotograma guardado en {args.fotograma}")

    if not args.salida:
        return 0

    # matplotlib no codifica video: lanza el ejecutable de ffmpeg como subproceso.
    # Se lo apunta al binario que trae imageio-ffmpeg para no depender de uno
    # instalado en el sistema. Sin esto matplotlib cae al writer pillow y falla
    # con "unknown file extension: .mp4", que no dice nada de lo que pasa.
    matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

    fig, ax = plt.subplots(figsize=(10, 10 * config.ANCHO / config.LARGO))
    dibujar_mesa(ax, obstaculos)
    circulos = [Circle((0, 0), config.RADIO, color=COLORES[0]) for _ in range(len(datos["ID"].unique()))]
    for circulo in circulos:
        ax.add_patch(circulo)

    def actualizar(indice):
        cuadro = datos[datos["Time"] == instantes[indice]]
        for _, fila in cuadro.iterrows():
            circulo = circulos[int(fila["ID"])]
            circulo.center = (fila["X"], fila["Y"])
            circulo.set_color(COLORES[int(fila["State"])])
        return circulos

    anim = animation.FuncAnimation(fig, actualizar, frames=len(instantes), blit=True)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    escritor = animation.FFMpegWriter(fps=args.fps, codec="libx264", bitrate=6000)
    anim.save(str(args.salida), writer=escritor, dpi=100)
    print(f"Animacion guardada en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
