"""Sincroniza las configs ganadoras del GA con el barrido de simulacion.

Por cada semilla de GA que termino bien (tiene .resumen) en
build/resultados/genetico/<simetria>/, copia su config.txt a
configs/<prefijo>_k<K>_s<semilla>.txt si todavia no esta, y simula 25 veces
las que sean nuevas (build/resultados/configs/resumen.csv). Al final
recalcula y regrafica las ganadoras por simetria.

Pensado para correrlo cada vez que barrido_completo.py sume semillas nuevas
sin tener que acordarse de los pasos a mano.

    python sincronizar_configs.py
"""

import re
import sys
from types import SimpleNamespace

import config
import run
from plot import ganadoras_por_simetria

SIMETRIA_A_PREFIJO = {"quad": "ga", "horizontal": "hz", "none": "nn"}
PATRON_SIDECAR = re.compile(r"^K(\d+)_s(\d+)$")
REALIZACIONES_SIM = 25


def copiar_nuevas():
    nuevas = []
    for simetria, prefijo in SIMETRIA_A_PREFIJO.items():
        directorio = config.RESULTADOS / "genetico" / simetria
        if not directorio.exists():
            continue
        for sidecar in sorted(directorio.glob("K*_s*.resumen")):
            m = PATRON_SIDECAR.match(sidecar.stem)
            if not m:
                continue
            k, semilla = m.group(1), m.group(2)
            nombre = f"{prefijo}_k{k}_s{semilla}"
            destino = config.CONFIGS / f"{nombre}.txt"
            if destino.exists():
                continue
            origen = directorio / f"K{k}_s{semilla}" / "config.txt"
            if not origen.exists():
                continue
            destino.write_text(origen.read_text())
            nuevas.append(nombre)
            print(f"  copiada: {nombre}")
    return nuevas


def main():
    nuevas = copiar_nuevas()
    if not nuevas:
        print("No hay configs nuevas para copiar.")
    else:
        print(f"\nSimulando {len(nuevas)} configs nuevas x{REALIZACIONES_SIM} realizaciones...")
        args = SimpleNamespace(
            valores=nuevas,
            realizaciones=REALIZACIONES_SIM,
            forzar=False,
            cada_eventos=200,
            particulas=config.PARTICULAS,
            trayectoria=False,
        )
        run.barrido_configs(args)

    print("\nRecalculando ganadoras...")
    ganadoras_por_simetria.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
