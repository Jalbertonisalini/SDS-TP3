"""Mide t90 real con N realizaciones, pero solo sobre los --top-n candidatos
mas prometedores de cada (simetria, K) -- no las 662 configs del GA. Es
"optimal computing budget allocation": el filtro usa lo barato que ya
tenemos (mejor_fitness de cada corrida del GA, en resultados/genetico/,
disponible para las 662 sin excepcion), esto es la etapa cara y angosta,
solo sobre los que sobrevivieron el filtro.

    python evaluar_todas_configs.py --top-n 5 --realizaciones 100

El filtro NO usa build/resultados/configs/resumen.csv (ese t90 medido
todavia no cubre todo el GA) -- usa mejor_fitness directo de
build/resultados/genetico/<simetria>/K<k>_s<semilla>.resumen, que si esta
completo para las 3 simetrias. Reusa run.barrido_configs(), que es
incremental por (config, semilla): si un candidato ya tenia algo simulado
y ahora se pide 100, corre solo lo que falte.
"""

import argparse
import csv
import re
import statistics
import sys
from collections import defaultdict
from types import SimpleNamespace

import config
import run

PATRON = re.compile(r"^(ga|hz|nn)_k(\d+)_s(\d+)$")
PREFIJO_A_SIMETRIA = {"ga": "quad", "hz": "horizontal", "nn": "none"}
SIMETRIA_A_PREFIJO = {v: k for k, v in PREFIJO_A_SIMETRIA.items()}
PATRON_SIDECAR_GA = re.compile(r"^K(\d+)_s(\d+)$")


def listar_configs_ga():
    return sorted(p.stem for p in config.CONFIGS.glob("*.txt") if PATRON.match(p.stem))


def cargar_t90():
    ruta = config.RESULTADOS / "configs" / "resumen.csv"
    t90 = defaultdict(list)
    if not ruta.exists():
        return t90
    with open(ruta, newline="") as f:
        for fila in csv.DictReader(f):
            t90[fila["configuracion"]].append(float(fila["t90"]))
    return t90


def preseleccionar(top_n):
    """De cada grupo (simetria, K), los top_n de menor mejor_fitness del GA
    (build/resultados/genetico/<simetria>/K<k>_s<semilla>.resumen)."""
    grupos = defaultdict(list)
    for simetria, prefijo in SIMETRIA_A_PREFIJO.items():
        directorio = config.RESULTADOS / "genetico" / simetria
        if not directorio.exists():
            continue
        for sidecar in directorio.glob("K*_s*.resumen"):
            m = PATRON_SIDECAR_GA.match(sidecar.stem)
            if not m:
                continue
            k, semilla = int(m.group(1)), int(m.group(2))
            resumen = run.parsear_resumen(sidecar.read_text())
            nombre = f"{prefijo}_k{k}_s{semilla}"
            grupos[(simetria, k)].append((resumen["mejor_fitness"], nombre))

    elegidos = []
    for clave, candidatos in sorted(grupos.items()):
        candidatos.sort(key=lambda c: c[0])
        top = candidatos[:top_n]
        print(f"  {clave[0]:11} K={clave[1]:>2}: {len(candidatos)} candidatos -> "
              f"top {len(top)}: {', '.join(n for _, n in top)}")
        elegidos.extend(n for _, n in top)
    return elegidos


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--realizaciones", type=int, default=100,
                        help="Simulaciones por config (default 100)")
    parser.add_argument("--top-n", type=int, default=5,
                        help="Candidatos por (simetria, K) a llevar a --realizaciones "
                             "(default 5). 0 = todas las configs, sin filtro")
    args = parser.parse_args()

    if args.top_n > 0:
        print(f"Preseleccionando top-{args.top_n} por (simetria, K) segun t90 ya medido...")
        nombres = preseleccionar(args.top_n)
    else:
        nombres = listar_configs_ga()
    print(f"\n{len(nombres)} configs a llevar a {args.realizaciones} realizaciones")

    sim_args = SimpleNamespace(
        valores=nombres,
        realizaciones=args.realizaciones,
        forzar=False,
        cada_eventos=200,
        particulas=config.PARTICULAS,
        trayectoria=False,
    )
    run.barrido_configs(sim_args)

    t90 = cargar_t90()
    filas = []
    for nombre, valores in t90.items():
        m = PATRON.match(nombre)
        if not m or len(valores) < args.realizaciones:
            continue
        prefijo, k, semilla = m.group(1), int(m.group(2)), int(m.group(3))
        filas.append({
            "simetria": PREFIJO_A_SIMETRIA[prefijo],
            "K": k,
            "semilla": semilla,
            "nombre": nombre,
            "media": statistics.mean(valores),
            "desvio": statistics.stdev(valores),
            "n": len(valores),
        })
    filas.sort(key=lambda f: f["media"])

    print(f"\n=== TOP 15 GLOBAL (con >= {args.realizaciones} realizaciones) ===")
    for f in filas[:15]:
        print(f"{f['nombre']:16} {f['simetria']:11} K={f['K']:>2}  "
              f"t90={f['media']:.3f} +/- {f['desvio']:.3f}  (n={f['n']})")

    print("\n=== Mejor por (simetria, K) ===")
    mejores = {}
    for f in filas:
        clave = (f["simetria"], f["K"])
        if clave not in mejores:
            mejores[clave] = f
    for (sim, k), f in sorted(mejores.items()):
        print(f"{sim:11} K={k:>2}: {f['nombre']:16} t90={f['media']:.3f} +/- {f['desvio']:.3f}")

    salida = config.OUTPUT_DIR / "ranking_completo.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", newline="") as fh:
        escritor = csv.DictWriter(fh, fieldnames=["simetria", "K", "semilla", "nombre",
                                                   "media", "desvio", "n"])
        escritor.writeheader()
        for f in filas:
            escritor.writerow(f)
    print(f"\nRanking completo guardado en {salida}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
