"""Animacion de como converge la poblacion del GA, generacion a generacion.

    python plot/convergencia_poblacion.py \
        --population-log ../build/resultados/genetico/demo/offsprings \
        --config-final ../build/resultados/genetico/demo/config.txt \
        --salida output/convergencia_poblacion.mp4

Lee el directorio que escribe `optimizador --population-log` (un CSV por
generacion loguada: gen_00000.csv, gen_00005.csv, ...). Cada cuadro es una
generacion completa: dibuja los obstaculos de TODA la poblacion superpuestos
con transparencia (mas oscuro = mas individuos coinciden ahi) y coloreados
segun el fitness de cada uno (mas claro/amarillo = mejor, t90 mas bajo). La
configuracion final se marca en rojo punteado como referencia, para ver
hacia donde converge la nube. Pensado para una corrida chica y puntual, no
para el barrido grande.
"""

import argparse
import re
import sys
from pathlib import Path

import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.patches import Circle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def leer_poblacion(directorio):
    """Concatena los gen_NNNNN.csv del directorio en un unico DataFrame con
    columna 'generacion' (extraida del nombre de archivo, no viene en el CSV)."""
    archivos = sorted(directorio.glob("gen_*.csv"))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos gen_*.csv en {directorio}")

    tablas = []
    for archivo in archivos:
        m = re.fullmatch(r"gen_(\d+)\.csv", archivo.name)
        generacion = int(m.group(1))
        tabla = pd.read_csv(archivo)
        tabla["generacion"] = generacion
        tablas.append(tabla)
    return pd.concat(tablas, ignore_index=True)


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


def dibujar_mesa(ax):
    ax.set_xlim(0, config.LARGO)
    ax.set_ylim(0, config.ANCHO)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    inferior = config.ANCHO / 2 - config.ARCO / 2
    superior = config.ANCHO / 2 + config.ARCO / 2
    for x in (0.0, config.LARGO):
        ax.plot([x, x], [inferior, superior], color="tab:green", linewidth=4)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--population-log", type=Path, required=True,
                        help="Directorio que escribe optimizador --population-log")
    parser.add_argument("--config-final", type=Path, default=None,
                        help="Config ganadora, se marca en rojo punteado como referencia")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo MP4 de salida")
    parser.add_argument("--fps", type=int, default=4,
                        help="Cuadros por segundo; cada cuadro es una generacion (default 4)")
    args = parser.parse_args()

    if not args.population_log.exists():
        print(f"Falta el directorio de poblacion: {args.population_log}", file=sys.stderr)
        return 1

    datos = leer_poblacion(args.population_log)
    generaciones = sorted(datos["generacion"].unique())
    referencia = leer_obstaculos(args.config_final)

    norm = Normalize(vmin=datos["fitness"].min(), vmax=datos["fitness"].max())
    cmap = plt.get_cmap("viridis_r")  # menor fitness (mejor) = mas claro

    matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

    fig, ax = plt.subplots(figsize=(10, 10 * config.ANCHO / config.LARGO))

    def actualizar(indice):
        ax.clear()
        dibujar_mesa(ax)
        generacion = generaciones[indice]
        cuadro = datos[datos["generacion"] == generacion]
        for _, individuo in cuadro.groupby("individuo"):
            color = cmap(norm(individuo["fitness"].iloc[0]))
            for _, fila in individuo.iterrows():
                ax.add_patch(Circle((fila["x"], fila["y"]), fila["r"], color=color, alpha=0.12,
                                    linewidth=0))
        for x, y, r in referencia:
            ax.add_patch(Circle((x, y), r, fill=False, edgecolor="red", linewidth=2,
                                linestyle="--"))
        mejor = cuadro["fitness"].min()
        ax.set_title(f"Generacion {generacion}    mejor fitness = {mejor:.2f} s",
                    fontsize=config.FUENTE * 0.6)
        return []

    anim = animation.FuncAnimation(fig, actualizar, frames=len(generaciones), blit=False)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    # -pix_fmt yuv420p: sin esto libx264 codifica en yuv444p (perfil "High
    # 4:4:4"), que Windows/VLC reproducen pero QuickTime no reconoce.
    escritor = animation.FFMpegWriter(fps=args.fps, codec="libx264", bitrate=6000,
                                      extra_args=["-pix_fmt", "yuv420p"])
    anim.save(str(args.salida), writer=escritor, dpi=100)
    print(f"Animacion guardada en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
