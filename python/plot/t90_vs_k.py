"""Punto 1.2 (GA, simetria quad): t90 real vs K, con K como eje numerico (a
diferencia de t90_vs_configuracion.py, que trata cada config como una
categoria separada sin relacion de orden entre ellas).

    python plot/t90_vs_k.py \
        --punto 5  15.70 2.11 \
        --punto 9  14.25 1.69 \
        --punto 13 16.65 2.08 \
        --punto 17 16.40 2.00 \
        --salida ../entrega/1.2/quad_t90_vs_k.png

Cada --punto es K, t90 medio y desvio (ya calculados con 100 realizaciones
reales, no fitness del GA -- ver punto_1_2.py).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--punto", nargs=3, action="append", metavar=("K", "MEDIA", "DESVIO"),
                        required=True, help="K, t90 medio y desvio (repetible)")
    parser.add_argument("--realizaciones", type=int, default=None,
                        help="Corridas detras de cada media (va de subindice en el eje y)")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    puntos = sorted((int(k), float(media), float(desvio)) for k, media, desvio in args.punto)
    ks = [p[0] for p in puntos]
    medias = [p[1] for p in puntos]
    desvios = [p[2] for p in puntos]

    fig, ax = estilo.nueva_figura()
    ax.errorbar(ks, medias, yerr=desvios, marker="o", capsize=4, linestyle="-")
    ax.set_xticks(ks)
    estilo.etiquetar_ejes(ax, "Cantidad de obstaculos (K)",
                          f"{estilo.t90_promedio(args.realizaciones)} (s)")

    estilo.guardar(fig, args.salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
