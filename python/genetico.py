"""Barrido en K (punto 1.2, metodologia GA): invoca `optimizador` una vez por
cantidad de obstaculos y arma el resumen, siguiendo el mismo patron que
run.py (sidecars ``.resumen``, resumen agregado que se reconstruye desde
ellos, no se re-corre un caso ya registrado salvo --forzar).

    python genetico.py 2 4 8 --realizaciones 5 --symmetry quad

Guarda por cada (K, semilla): la config ganadora (config.txt, cargable con
`simulador --config`) y el log de convergencia (log.csv) bajo
build/resultados/genetico/<symmetry>/K<k>_s<semilla>/, y un sidecar
K<k>_s<semilla>.resumen con lo que imprime `optimizador` por stdout -- con
eso alcanza para reproducir y defender el resultado. La carpeta por
simetria (quad/, horizontal/, none/) permite correr experimentos con
distintas simetrias sin que se pisen entre si.
"""

import argparse
import re
import subprocess
import sys

import config
import run


def fila_desde_sidecar_genetico(sidecar):
    """Reconstruye una fila del resumen desde un sidecar K<k>_s<semilla>.resumen."""
    m = re.fullmatch(r"K(\d+)_s(\d+)", sidecar.stem)
    if not m:
        return None
    resumen = run.parsear_resumen(sidecar.read_text())
    return {
        "K": int(m.group(1)),
        "semilla": int(m.group(2)),
        "mejor_fitness": resumen["mejor_fitness"],
        "tiempo_ejecucion_s": resumen["tiempo_ejecucion_s"],
    }


def correr_ga(k, semilla, args, forzar):
    """Corre la busqueda genetica para un K y una semilla si hace falta."""
    directorio = config.RESULTADOS / "genetico" / args.symmetry
    caso = directorio / f"K{k}_s{semilla}"
    sidecar = directorio / f"K{k}_s{semilla}.resumen"
    config_out = caso / "config.txt"
    log_out = caso / "log.csv"

    if config_out.exists() and sidecar.exists() and not forzar:
        print(f"  ya registrado, se saltea: K{k}_s{semilla}")
        return None

    caso.mkdir(parents=True, exist_ok=True)
    comando = [
        str(config.EJECUTABLE_GA),
        "--obstacles", str(k),
        "--symmetry", args.symmetry,
        "--population", str(args.population),
        "--generations", str(args.generations),
        "--seeds-per-gen", str(args.seeds_per_gen),
        "--seed", str(semilla),
        "--config-out", str(config_out),
        "--log", str(log_out),
    ]
    if args.max_radius is not None:
        comando += ["--max-radius", str(args.max_radius)]
    if args.mutation_gene_rate is not None:
        comando += ["--mutation-gene-rate", str(args.mutation_gene_rate)]
    if args.elitism is not None:
        comando += ["--elitism", str(args.elitism)]
    if args.threads is not None:
        comando += ["--threads", str(args.threads)]
    if getattr(args, "population_log", False):
        poblacion_out = caso / "poblacion"
        poblacion_out.mkdir(parents=True, exist_ok=True)
        comando += ["--population-log", str(poblacion_out),
                    "--population-log-every", str(args.population_log_every)]
    # stdout se captura (ahi va el resumen parseable); stderr se hereda tal
    # cual para ver el progreso generacion a generacion en vivo, en foreground.
    proceso = subprocess.run(comando, stdout=subprocess.PIPE, text=True)
    if proceso.returncode != 0:
        print(f"  FALLO K{k}_s{semilla} (ver el error mas arriba)", file=sys.stderr)
        return None

    sidecar.write_text(proceso.stdout)
    print(f"  ok: K{k}_s{semilla}")
    return run.parsear_resumen(proceso.stdout)


def barrido_obstaculos(args):
    directorio = config.RESULTADOS / "genetico" / args.symmetry
    filas = []

    total = len(args.valores) * args.realizaciones
    hecho = 0

    for k in args.valores:
        for i in range(args.realizaciones):
            semilla = config.SEMILLA_BASE + i
            hecho += 1
            print(f"\n=== [{hecho}/{total}] K={k} semilla={semilla} ===", flush=True)

            resumen = correr_ga(k, semilla, args, args.forzar)
            if resumen is None:
                continue
            filas.append({
                "K": k,
                "semilla": semilla,
                "mejor_fitness": resumen["mejor_fitness"],
                "tiempo_ejecucion_s": resumen["tiempo_ejecucion_s"],
            })

    print(f"\n=== Barrido completo: {hecho}/{total} casos procesados ===")

    run.escribir_resumen(
        directorio,
        ["K", "semilla", "mejor_fitness", "tiempo_ejecucion_s"],
        ["K", "semilla"],
        filas,
        extraer_sidecar=fila_desde_sidecar_genetico,
    )


def construir_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("valores", nargs="+", type=int, help="Valores de K (cantidad de obstaculos)")
    parser.add_argument("--realizaciones", type=int, default=5,
                        help="Corridas de GA por K, con semillas distintas (default 5)")
    parser.add_argument("--forzar", action="store_true",
                        help="Re-corre aunque el caso ya este registrado")
    parser.add_argument("--symmetry", choices=["none", "horizontal", "quad"], default="none",
                        help="Modo de simetria del genoma (default none)")
    parser.add_argument("--population", type=int, default=64, help="Tamano de poblacion (default 64)")
    parser.add_argument("--generations", type=int, default=100, help="Generaciones (default 100)")
    parser.add_argument("--seeds-per-gen", type=int, default=5,
                        help="Semillas comunes por generacion (default 5)")
    parser.add_argument("--max-radius", type=float, default=None,
                        help="Radio maximo de obstaculo en m (default: el del optimizador, 0.25)")
    parser.add_argument("--mutation-gene-rate", type=float, default=None, dest="mutation_gene_rate",
                        help="Prob. de mutar cada gen (default: el del optimizador, 0.3)")
    parser.add_argument("--elitism", type=int, default=None,
                        help="Individuos que pasan sin cambios a la siguiente generacion (default: el del optimizador, 2)")
    parser.add_argument("--threads", type=int, default=None,
                        help="Hilos OpenMP por corrida (default: todos los disponibles)")
    parser.add_argument("--population-log", action="store_true", dest="population_log",
                        help="Guarda la poblacion completa de cada corrida (para animar la "
                             "convergencia con plot/snapshots_poblacion.py o "
                             "plot/convergencia_poblacion.py). Pensado para pocas corridas "
                             "puntuales, no para un barrido grande")
    parser.add_argument("--population-log-every", type=int, default=5, dest="population_log_every",
                        help="Cada cuantas generaciones guardar la poblacion (default 5)")
    return parser


def main():
    args = construir_parser().parse_args()
    if not config.EJECUTABLE_GA.exists():
        print(f"Falta compilar el optimizador: no existe {config.EJECUTABLE_GA}", file=sys.stderr)
        return 1
    barrido_obstaculos(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
