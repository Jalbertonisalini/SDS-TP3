"""Animacion del sistema a partir de una trayectoria completa.

    python plot/animacion.py --trayectoria ../build/resultados/configs/embudo/trayectoria_s1000.csv \
                             --obstaculos ../configs/embudo.txt \
                             --salida output/embudo.mp4 \
                             --fotograma ../entrega/1.2/embudo_frame.png

Con --dt-cuadro 0.04 y --fps 25 el video corre en tiempo real (1 s de video =
1 s simulado); el titulo muestra t, N_g, F_u y t90 una vez alcanzado.

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
import numpy as np
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


def estados_por_instante(datos):
    """Pasa la trayectoria a matrices (instante, particula) para no filtrar el
    DataFrame en cada cuadro."""
    # El ultimo estado puede repetirse si t_max coincide con un muestreo.
    datos = datos.drop_duplicates(["Time", "ID"], keep="last")
    columnas = ["X", "Y", "VX", "VY", "State"]
    tabla = datos.pivot(index="Time", columns="ID", values=columnas)
    return tabla.index.to_numpy(), {columna: tabla[columna].to_numpy() for columna in columnas}


def tiempos_de_cuadros(instantes, dt_cuadro):
    """Devuelve el tiempo de cada cuadro y el estado guardado que le corresponde.

    El muestreo es cada N eventos, asi que los instantes guardados no son
    equiespaciados. Con dt_cuadro se arma una grilla uniforme y cada cuadro
    usa el ultimo estado guardado anterior a su tiempo, para que el video
    avance a ritmo constante de tiempo simulado.
    """
    if dt_cuadro is None:
        return instantes, np.arange(len(instantes))
    grilla = np.arange(instantes[0], instantes[-1] + dt_cuadro / 2, dt_cuadro)
    return grilla, np.searchsorted(instantes, grilla, side="right") - 1


def posiciones(matrices, instantes, indice, tiempo, interpolar):
    """Posiciones de todas las particulas en `tiempo`.

    Interpolar solo es exacto si la trayectoria guarda todos los eventos
    (--cada-eventos 1): entre dos estados consecutivos ninguna particula choca y
    todas siguen en movimiento rectilineo uniforme con la velocidad guardada.
    """
    xs, ys = matrices["X"][indice], matrices["Y"][indice]
    if not interpolar:
        return xs, ys
    vuelo = tiempo - instantes[indice]
    return xs + matrices["VX"][indice] * vuelo, ys + matrices["VY"][indice] * vuelo


def calcular_t90(instantes, estados):
    """Primer instante guardado con F_u >= 0.9, o None si nunca se alcanza."""
    fraccion_usadas = estados.mean(axis=1)
    alcanzados = np.nonzero(fraccion_usadas >= config.FRACCION_OBJETIVO)[0]
    return instantes[alcanzados[0]] if len(alcanzados) else None


def texto_rotulo(instante, estados, t90):
    goles = int(estados.sum())
    texto = f"t = {instante:6.2f} s    $N_g$ = {goles:3d}    $F_u$ = {goles / len(estados):.2f}"
    if t90 is not None and instante >= t90:
        texto += f"    $t_{{90}}$ = {t90:.2f} s"
    return texto


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
    parser.add_argument("--dt-cuadro", type=float, default=None,
                        help="Tiempo simulado entre cuadros, en s. Remuestrea a una grilla "
                             "uniforme (default: un cuadro por cada estado guardado)")
    parser.add_argument("--interpolar", action="store_true",
                        help="Con --dt-cuadro, avanza cada particula en vuelo libre desde el "
                             "ultimo estado guardado. Requiere correr el motor con --cada-eventos 1")
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
    instantes, matrices = estados_por_instante(datos)
    estados = matrices["State"]
    tiempos, indices = tiempos_de_cuadros(instantes, args.dt_cuadro)
    t90 = calcular_t90(instantes, estados)

    circulos = [Circle((0, 0), config.RADIO, color=COLORES[0]) for _ in range(estados.shape[1])]
    for circulo in circulos:
        ax.add_patch(circulo)
    rotulo = ax.set_title(" ", fontsize=14)

    def actualizar(numero_cuadro):
        tiempo, indice = tiempos[numero_cuadro], indices[numero_cuadro]
        xs, ys = posiciones(matrices, instantes, indice, tiempo, args.interpolar)
        for circulo, x, y, estado in zip(circulos, xs, ys, estados[indice]):
            circulo.center = (x, y)
            circulo.set_color(COLORES[int(estado)])
        rotulo.set_text(texto_rotulo(tiempo, estados[indice], t90))
        return [*circulos, rotulo]

    # Sin blit: el titulo queda fuera de los ejes y blit no lo redibujaria.
    anim = animation.FuncAnimation(fig, actualizar, frames=len(tiempos), blit=False)
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
