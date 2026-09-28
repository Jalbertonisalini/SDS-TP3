"""Corridas "en vivo" para la defensa: t90 de la mejor configuracion.

Corre el motor una vez por semilla con la mejor configuracion, imprime el
numero de particulas convertidas en cada nueva conversion y, al terminar cada
corrida, su t90. Al final imprime la media y el desvio de los t90.

    python en_vivo.py
    python en_vivo.py --semillas 1 2 3 4 5
    python en_vivo.py --config pared_ganadora --semillas 1000 1001 1002 1003 1004

Las conversiones se leen del registro de goles ("Time,ID") que escribe el
motor, asi que se imprimen apenas termina cada corrida (tarda menos de un
segundo).
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import config
import observables

# Menor <t90> de la comparacion final (ver build/resultados/punto_1_3/difusion_vs_t90.csv).
MEJOR_CONFIGURACION = "pared_ganadora"
CANTIDAD_SEMILLAS = 5
SEMILLAS_DEFAULT = [config.SEMILLA_BASE + i for i in range(CANTIDAD_SEMILLAS)]


def simular(nombre_config, semilla, ruta_goles):
    """Corre el motor hasta que convierte el 90 % de las particulas (o t_max)."""
    comando = [
        str(config.EJECUTABLE),
        "--config", str(config.CONFIGS / f"{nombre_config}.txt"),
        "--particles", str(config.PARTICULAS),
        "--tmax", str(config.TIEMPO_MAXIMO),
        "--seed", str(semilla),
        "--stop-fraction", str(config.FRACCION_OBJETIVO),
        "--output", str(ruta_goles),
    ]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    if proceso.returncode != 0:
        sys.exit(f"El motor fallo con la semilla {semilla}:\n{proceso.stderr}")


def imprimir_conversiones(goles):
    for cantidad, tiempo in enumerate(goles["Time"], start=1):
        print(f"  t = {tiempo:9.4f} s   convertidas: {cantidad:3d}/{config.PARTICULAS}")


def correr_semilla(nombre_config, semilla, directorio):
    """Corre una realizacion, imprime sus conversiones y devuelve su t90 (-1 si no llego)."""
    print(f"\n=== Semilla {semilla} ===")
    ruta_goles = Path(directorio) / f"goles_s{semilla}.csv"
    simular(nombre_config, semilla, ruta_goles)
    goles = pd.read_csv(ruta_goles)
    imprimir_conversiones(goles)

    t90 = observables.t90(goles, config.PARTICULAS)
    if t90 < 0:
        print(f"  t90: no se alcanzo antes de t_max = {config.TIEMPO_MAXIMO} s")
    else:
        print(f"  t90 = {t90:.4f} s")
    return t90


def imprimir_resumen(semillas, tiempos):
    print("\n=== Resumen ===")
    for semilla, t90 in zip(semillas, tiempos):
        texto = f"{t90:.4f} s" if t90 >= 0 else "no alcanzado"
        print(f"  semilla {semilla}: t90 = {texto}")

    validos = np.array([t90 for t90 in tiempos if t90 >= 0])
    if len(validos) < 2:
        print("  Hacen falta al menos 2 t90 validos para el desvio.")
        return
    # Desvio muestral (ddof=1), igual que el resto de las estadisticas del TP.
    print(f"  <t90> = {validos.mean():.4f} s")
    print(f"  desvio = {validos.std(ddof=1):.4f} s")
    if len(validos) < len(tiempos):
        print(f"  (sobre {len(validos)} de {len(tiempos)} corridas: el resto no llego a t90)")


def construir_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--semillas", type=int, nargs="+", default=SEMILLAS_DEFAULT,
                        help=f"semillas a correr (default: {' '.join(map(str, SEMILLAS_DEFAULT))})")
    parser.add_argument("--config", default=MEJOR_CONFIGURACION,
                        help=f"configuracion de configs/ sin extension (default: {MEJOR_CONFIGURACION})")
    return parser


def main():
    args = construir_parser().parse_args()
    print(f"Configuracion: {args.config}   N = {config.PARTICULAS}   semillas: {args.semillas}")
    with tempfile.TemporaryDirectory() as directorio:
        tiempos = [correr_semilla(args.config, semilla, directorio) for semilla in args.semillas]
    imprimir_resumen(args.semillas, tiempos)


if __name__ == "__main__":
    main()
