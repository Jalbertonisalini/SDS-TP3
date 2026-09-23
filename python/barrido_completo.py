"""Corre de una el barrido de GA de las 3 simetrias con 25 semillas por K.

A `none` se le da mas poblacion/generaciones (mas grados de libertad: K
obstaculos libres contra K/2 en horizontal y K/4 en quad) y un
--max-radius mas chico -- con el default (0.25) el sorteo de individuos
falla para K>=9 sin simetria que ayude a acomodarlos.

Reanudable: reusa barrido_obstaculos() de genetico.py, que ya saltea los
(K, semilla) que esten registrados. Si se corta a la mitad (Ctrl+C, se
cierra la laptop, etc.) correrlo de nuevo retoma justo donde quedo, sin
perder ni repetir trabajo.

    python barrido_completo.py
"""

import sys
from types import SimpleNamespace

import genetico

REALIZACIONES = 25

SWEEPS = [
    dict(symmetry="quad", valores=[1, 4, 5, 8, 9, 12],
         population=48, generations=60, max_radius=None),
    dict(symmetry="horizontal", valores=[2, 3, 4, 6, 7, 8, 9, 10, 11, 12],
         population=48, generations=60, max_radius=None),
    dict(symmetry="none", valores=list(range(2, 13)),
         population=96, generations=90, max_radius=0.12),
]


def main():
    if not genetico.config.EJECUTABLE_GA.exists():
        print(f"Falta compilar el optimizador: no existe {genetico.config.EJECUTABLE_GA}",
              file=sys.stderr)
        return 1

    for sweep in SWEEPS:
        print(f"\n=== {sweep['symmetry']} ===")
        args = SimpleNamespace(
            valores=sweep["valores"],
            realizaciones=REALIZACIONES,
            forzar=False,
            symmetry=sweep["symmetry"],
            population=sweep["population"],
            generations=sweep["generations"],
            seeds_per_gen=5,
            max_radius=sweep["max_radius"],
            threads=None,
        )
        genetico.barrido_obstaculos(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
