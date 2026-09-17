"""Geometria ganadora por cada K, para cada simetria del GA (quad/horizontal/none).

Usa exclusivamente python/output/ranking_completo.csv (lo genera
evaluar_todas_configs.py --top-n N --realizaciones 100): son los candidatos
que se llevaron hasta 100 simulaciones reales, no los ~25 candidatos por K
que quedaron afuera del filtro top-N. Mezclar esos dos grupos rompe la
comparacion -- una config con solo 25 corridas puede parecer mejor que una
con 100 por puro ruido de muestreo (menos precision), no porque sea
realmente mejor.

Genera un PNG por simetria (grilla con un panel por K) en python/output/.

    python plot/ganadoras_por_simetria.py
"""

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
from diagrama_configs import leer_obstaculos, dibujar_mesa


def leer_ranking():
    ruta = config.OUTPUT_DIR / "ranking_completo.csv"
    if not ruta.exists():
        sys.exit(f"Falta {ruta} -- corre evaluar_todas_configs.py primero")
    with open(ruta, newline="") as f:
        return list(csv.DictReader(f))


def elegir_ganadoras(filas):
    """Devuelve {simetria: {K: (prefijo, semilla, media, desvio)}} quedandose
    con el menor t90 medio (ya medido a --realizaciones, tipicamente 100)
    entre los candidatos preseleccionados de cada (simetria, K)."""
    ganadoras = {}
    for fila in filas:
        simetria, k = fila["simetria"], int(fila["K"])
        media, desvio = float(fila["media"]), float(fila["desvio"])
        prefijo, semilla = fila["nombre"].split("_")[0], int(fila["semilla"])
        actual = ganadoras.setdefault(simetria, {}).get(k)
        if actual is None or media < actual[2]:
            ganadoras[simetria][k] = (prefijo, semilla, media, desvio)
    return ganadoras


def graficar_simetria(simetria, por_k, salida):
    ks = sorted(por_k)
    columnas = min(len(ks), 3)
    filas = -(-len(ks) // columnas)

    fig, ejes = plt.subplots(filas, columnas,
                              figsize=(5 * columnas, 5 * config.ANCHO / config.LARGO * filas))
    ejes = [ejes] if len(ks) == 1 else ejes.flatten()

    for ax, k in zip(ejes, ks):
        prefijo, semilla, media, desvio = por_k[k]
        ruta = config.CONFIGS / f"{prefijo}_k{k}_s{semilla}.txt"
        titulo = f"K={k}  (t90 = {media:.2f} ± {desvio:.2f} s)"
        dibujar_mesa(ax, leer_obstaculos(ruta), titulo)
    for ax in ejes[len(ks):]:
        ax.axis("off")

    fig.suptitle(f"Simetria: {simetria}", fontsize=config.FUENTE * 0.9)
    fig.tight_layout()
    salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(salida, dpi=config.DPI)
    print(f"Figura guardada en {salida}")


def main():
    filas = leer_ranking()
    ganadoras = elegir_ganadoras(filas)

    for simetria, por_k in sorted(ganadoras.items()):
        print(f"\n=== {simetria} ===")
        for k in sorted(por_k):
            prefijo, semilla, media, desvio = por_k[k]
            print(f"K={k:>2}: {prefijo}_k{k}_s{semilla}  t90 = {media:.3f} +/- {desvio:.3f} s")
        salida = config.OUTPUT_DIR / f"ganadoras_{simetria}.png"
        graficar_simetria(simetria, por_k, salida)

    return 0


if __name__ == "__main__":
    sys.exit(main())
