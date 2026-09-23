"""Linea de perfil y puntos de control de una pared del optimizador
(`optimizador --wall-profile N`), dibujados encima de sus circulos.

El config de la pared solo trae los circulos chicos ya rasterizados, no los
N puntos de control del genoma. Se los reconstruye invirtiendo
WallProfileCodec::expand: en cada fila de circulos (misma y), el borde
izquierdo del circulo mas a la izquierda esta en x = profundidad(y), y
profundidad(y) es la interpolacion lineal entre puntos de control
equiespaciados en y in [0, W/2] (espejada en y = W/2). Eso es lineal en los
N genes, asi que sale por cuadrados minimos.

Ojo: con grano 0.018 hay 9 filas por media mesa. Si N <= 9 (ej. la pared
ganadora, N=6) la reconstruccion es exacta. Si N > 9 hay puntos de control
que ninguna fila "ve" por separado y el perfil no queda determinado: se
elige, entre todas las soluciones que reproducen exactamente la pared, la
de menor curvatura (la mas suave).
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

COLOR = "tab:red"


def _matriz_interpolacion(ys, n):
    """Fila i = pesos de cada gen en profundidad(ys[i]), igual que
    profundidadEn() de WallProfileCodec."""
    mitad = config.ANCHO / 2
    plegadas = np.minimum(ys, config.ANCHO - ys)
    matriz = np.zeros((len(ys), n))
    if n == 1:
        matriz[:, 0] = 1.0
        return matriz
    posicion = plegadas / mitad * (n - 1)
    idx = np.minimum(n - 2, np.floor(posicion).astype(int))
    frac = posicion - idx
    filas = np.arange(len(ys))
    matriz[filas, idx] += 1 - frac
    matriz[filas, idx + 1] += frac
    return matriz


def reconstruir(obstaculos, n):
    """Profundidades de los n puntos de control a partir de los circulos."""
    obstaculos = np.asarray(obstaculos, dtype=float)
    grano = obstaculos[0, 2]
    ys = np.unique(np.round(obstaculos[:, 1], 6))
    profundidades = np.array([obstaculos[np.isclose(obstaculos[:, 1], y), 0].min() - grano
                              for y in ys])
    matriz = _matriz_interpolacion(ys, n)
    particular, _, rango, _ = np.linalg.lstsq(matriz, profundidades, rcond=None)
    if rango == n or n < 3:
        return particular
    # Subdeterminado: moverse en el nucleo de la matriz (no cambia ninguna
    # fila) hasta minimizar la segunda diferencia del perfil.
    _, _, vt = np.linalg.svd(matriz)
    nucleo = vt[rango:].T
    segunda = np.diff(np.eye(n), n=2, axis=0)
    z, *_ = np.linalg.lstsq(segunda @ nucleo, -segunda @ particular, rcond=None)
    return particular + nucleo @ z


def dibujar_perfil(ax, obstaculos, n, color=COLOR):
    """Linea punteada del perfil interpolado (las dos caras de la pared) y
    sus puntos de control, espejados en y = W/2 y en x = L/2."""
    genes = reconstruir(obstaculos, n)
    mitad = config.ANCHO / 2
    y_control = np.linspace(0, mitad, n) if n > 1 else np.array([0.0, mitad])
    d_control = genes if n > 1 else np.repeat(genes, 2)
    # Perfil completo en y in [0, W]: media mesa y su espejo.
    ys = np.concatenate([y_control, config.ANCHO - y_control[::-1]])
    ds = np.concatenate([d_control, d_control[::-1]])
    for xs in (ds, config.LARGO - ds):
        ax.plot(xs, ys, linestyle="--", color=color, linewidth=1.5, zorder=3)
        ax.plot(xs, ys, linestyle="none", marker="o", markersize=5, color=color,
                markeredgecolor="white", markeredgewidth=0.8, zorder=4)
    return genes
