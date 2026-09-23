"""Observables del TP3, calculados en postproceso a partir de la salida del motor.

El motor solo escribe estado y eventos:
- registro de goles (--output, "Time,ID"): instante exacto del primer gol de
  cada particula;
- trayectoria (--trajectory, "Time,ID,X,Y,VX,VY,State"): estado de todas las
  particulas cada --cada-eventos eventos.

Todo observable (goles, F_u(t), t90, DCM) sale de aca, nunca del motor.
"""

import numpy as np
import pandas as pd

import config

COLUMNAS_GOLES = ["Time", "ID"]


def es_registro_de_goles(ruta):
    """True si el CSV tiene el formato actual del registro de goles.

    Las corridas del motor anterior escribian una serie "Time,Goals,UsedFraction,MSD"
    con los observables ya calculados adentro del motor; esas no se pueden
    postprocesar y hay que distinguirlas."""
    with open(ruta) as archivo:
        encabezado = archivo.readline().strip()
    return encabezado.split(",") == COLUMNAS_GOLES


def leer_goles(ruta):
    if not es_registro_de_goles(ruta):
        raise ValueError(f"{ruta} no es un registro de goles (Time,ID): "
                         "es salida del motor anterior, hay que re-correrla.")
    return pd.read_csv(ruta)


def t90(goles, particulas, fraccion=config.FRACCION_OBJETIVO):
    """Instante del gol con el que F_u alcanza `fraccion`.

    Devuelve -1 si no se alcanzo antes de t_max (misma convencion que usan los
    resumen.csv). La comparacion es la misma division en punto flotante que
    define F_u = goles / N, asi que el cruce se detecta en el mismo gol."""
    for cantidad, tiempo in enumerate(goles["Time"], start=1):
        if cantidad / particulas >= fraccion:
            return float(tiempo)
    return -1.0


def fraccion_usada(goles, particulas, tiempos):
    """F_u(t) = (particulas con su primer gol en t' <= t) / N, en cada instante de `tiempos`."""
    instantes_de_gol = np.sort(goles["Time"].to_numpy())
    return np.searchsorted(instantes_de_gol, tiempos, side="right") / particulas


def leer_trayectoria(ruta):
    """Solo las columnas que necesita el DCM: la trayectoria completa puede pesar cientos de MB."""
    return pd.read_csv(ruta, usecols=["Time", "ID", "X", "Y"])


def dcm(trayectoria):
    """DCM(t) = < |r_i(t) - r_i(0)|^2 >, promediado sobre todas las particulas
    (frescas y usadas), con r_i(0) tomado del primer frame de la trayectoria.

    El motor escribe cada frame con todas las particulas en el mismo orden de
    ID, asi que la tabla se reordena como una matriz (frames x particulas)."""
    particulas = trayectoria["ID"].nunique()
    if len(trayectoria) % particulas != 0:
        raise ValueError("La trayectoria tiene frames incompletos.")

    ids = trayectoria["ID"].to_numpy().reshape(-1, particulas)
    if not (ids == ids[0]).all():
        raise ValueError("Los frames de la trayectoria no tienen el mismo orden de ID.")

    x = trayectoria["X"].to_numpy().reshape(-1, particulas)
    y = trayectoria["Y"].to_numpy().reshape(-1, particulas)
    desplazamiento_cuadrado = (x - x[0]) ** 2 + (y - y[0]) ** 2
    tiempos = trayectoria["Time"].to_numpy().reshape(-1, particulas)[:, 0]
    return pd.DataFrame({"Time": tiempos, "DCM": desplazamiento_cuadrado.mean(axis=1)})
