"""Constantes del TP y rutas del repositorio: unica fuente de verdad.

Todas las rutas se derivan de __file__, asi que los scripts funcionan sin
importar desde que directorio se los invoque.
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BUILD = RAIZ / "build"
EJECUTABLE = BUILD / "simulador"
EJECUTABLE_GA = BUILD / "optimizador"
RESULTADOS = BUILD / "resultados"
CONFIGS = RAIZ / "configs"
ENTREGA = RAIZ / "entrega"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

# Parametros fijos del enunciado (seccion 1.4).
LARGO = 1.20  # L [m]
ANCHO = 0.68  # W [m]
ARCO = 0.20  # d [m]
RADIO = 0.0175  # r [m]
MASA = 0.025  # m [kg]
VELOCIDAD_INICIAL = 1.0  # v0 [m/s]
TIEMPO_MAXIMO = 100.0  # t_max [s]
PARTICULAS = 100  # N para los puntos 1.2 en adelante

# Punto 1.1: tiempo absoluto fijo del barrido en N.
TIEMPO_PUNTO_11 = 30.0  # tf [s]

# Fraccion de particulas usadas que define t90.
FRACCION_OBJETIVO = 0.9

# Las realizaciones usan semillas deterministas SEMILLA_BASE + i para que
# cualquier corrida se pueda repetir identica al defenderla.
SEMILLA_BASE = 1000

# Estilo de las figuras (guia de la catedra).
FUENTE = 20
TAM_FIG = (13, 6)
DPI = 150
