"""Barridos del TP3: invoca el binario del motor N veces y arma el resumen.

Dos barridos, uno por subcomando:

    python run.py particulas --rango 50 300 50 --realizaciones 10
    python run.py configs vacia central_grande --realizaciones 5

Por defecto no se re-corre un caso cuyo CSV ya existe: los barridos son largos
y se reanudan a mano muchas veces. Con --forzar se recorre igual.
"""

import argparse
import csv
import subprocess
import sys

import config


def parsear_resumen(salida):
    """Convierte las lineas "clave=valor" que imprime el motor en un dict."""
    resumen = {}
    for linea in salida.strip().splitlines():
        if "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        resumen[clave.strip()] = float(valor)
    return resumen


def correr(destino, argumentos, forzar):
    """Corre una simulacion si hace falta y devuelve su resumen.

    Si el CSV ya existe y no se fuerza, el motor no se invoca y se devuelve None:
    el resumen agregado se reconstruye igual desde el CSV existente.
    """
    if destino.exists() and not forzar:
        print(f"  ya existe, se saltea: {destino.name}")
        return None

    destino.parent.mkdir(parents=True, exist_ok=True)
    comando = [str(config.EJECUTABLE), *argumentos, "--output", str(destino)]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    if proceso.returncode != 0:
        print(f"  FALLO {destino.name}: {proceso.stderr.strip()}", file=sys.stderr)
        return None

    print(f"  ok: {destino.name}")
    return parsear_resumen(proceso.stdout)


def escribir_resumen(directorio, columnas, claves, filas):
    """Guarda un CSV agregado con una fila por realizacion.

    Se fusiona con lo que ya habia para que reanudar un barrido no genere filas
    duplicadas. `claves` son las columnas que identifican univocamente una fila.
    """
    destino = directorio / "resumen.csv"
    previas = []
    if destino.exists():
        with open(destino, newline="") as archivo:
            previas = list(csv.DictReader(archivo))

    por_clave = {tuple(fila[c] for c in claves): fila for fila in previas}
    for fila in filas:
        texto = {c: str(fila[c]) for c in columnas}
        por_clave[tuple(texto[c] for c in claves)] = texto

    with open(destino, "w", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for fila in sorted(por_clave.values(), key=lambda f: tuple(f[c] for c in claves)):
            escritor.writerow(fila)
    print(f"Resumen actualizado: {destino}")


def barrido_particulas(args):
    """Punto 1.1: tiempo de ejecucion vs N, sin obstaculos, tf fijo."""
    directorio = config.RESULTADOS / "particulas"
    filas = []

    for n in args.valores:
        for i in range(args.realizaciones):
            semilla = config.SEMILLA_BASE + i
            destino = directorio / f"N{n}_s{semilla}.csv"
            argumentos = [
                "--particles", str(n),
                "--tmax", str(config.TIEMPO_PUNTO_11),
                "--seed", str(semilla),
                # Muestreo grueso: el I/O no debe ensuciar el tiempo de ejecucion medido.
                "--cada-eventos", str(args.cada_eventos),
            ]
            resumen = correr(destino, argumentos, args.forzar)
            if resumen is None:
                continue
            filas.append({
                "N": n,
                "semilla": semilla,
                "tiempo_ejecucion_s": resumen["tiempo_ejecucion_s"],
                "eventos": int(resumen["eventos"]),
                "goles": int(resumen["goles"]),
                "t90": resumen["t90"],
            })

    if filas:
        escribir_resumen(
            directorio,
            ["N", "semilla", "tiempo_ejecucion_s", "eventos", "goles", "t90"],
            ["N", "semilla"],
            filas,
        )


def barrido_configs(args):
    """Punto 1.2: t90 vs configuracion de obstaculos, con N fijo."""
    directorio = config.RESULTADOS / "configs"
    filas = []

    for nombre in args.valores:
        ruta_config = config.CONFIGS / f"{nombre}.txt"
        if not ruta_config.exists():
            print(f"No existe la configuracion {ruta_config}", file=sys.stderr)
            continue

        for i in range(args.realizaciones):
            semilla = config.SEMILLA_BASE + i
            destino = directorio / nombre / f"N{args.particulas}_s{semilla}.csv"
            argumentos = [
                "--config", str(ruta_config),
                "--particles", str(args.particulas),
                "--tmax", str(config.TIEMPO_MAXIMO),
                "--seed", str(semilla),
                "--cada-eventos", str(args.cada_eventos),
            ]
            if args.trayectoria and i == 0:
                argumentos += ["--trajectory", str(destino.with_name(f"trayectoria_s{semilla}.csv"))]

            resumen = correr(destino, argumentos, args.forzar)
            if resumen is None:
                continue
            filas.append({
                "configuracion": nombre,
                "semilla": semilla,
                "tiempo_ejecucion_s": resumen["tiempo_ejecucion_s"],
                "eventos": int(resumen["eventos"]),
                "goles": int(resumen["goles"]),
                "t90": resumen["t90"],
            })

    if filas:
        escribir_resumen(
            directorio,
            ["configuracion", "semilla", "tiempo_ejecucion_s", "eventos", "goles", "t90"],
            ["configuracion", "semilla"],
            filas,
        )


def construir_parser():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="comando", required=True)

    comun = argparse.ArgumentParser(add_help=False)
    comun.add_argument("valores", nargs="*", help="Valores del parametro barrido")
    comun.add_argument("--realizaciones", type=int, default=10,
                       help="Cantidad de realizaciones por caso (default 10)")
    comun.add_argument("--forzar", action="store_true",
                       help="Re-corre aunque el CSV ya exista")
    comun.add_argument("--cada-eventos", type=int, default=200,
                       help="Guarda el estado cada N eventos (default 200)")

    particulas = subparsers.add_parser("particulas", parents=[comun],
                                       help="Punto 1.1: barrido en N sin obstaculos")
    particulas.add_argument("--rango", nargs=3, type=int, metavar=("INI", "FIN", "PASO"),
                            help="Barrido regular en N")
    particulas.set_defaults(funcion=barrido_particulas)

    configs = subparsers.add_parser("configs", parents=[comun],
                                    help="Punto 1.2: barrido sobre configuraciones de obstaculos")
    configs.add_argument("--particulas", type=int, default=config.PARTICULAS,
                         help=f"Cantidad de particulas (default {config.PARTICULAS})")
    configs.add_argument("--trayectoria", action="store_true",
                         help="Guarda la trayectoria completa de la primera realizacion")
    configs.set_defaults(funcion=barrido_configs)

    return parser


def main():
    args = construir_parser().parse_args()

    if not config.EJECUTABLE.exists():
        print(f"Falta compilar el motor: no existe {config.EJECUTABLE}", file=sys.stderr)
        return 1

    if getattr(args, "rango", None):
        inicio, fin, paso = args.rango
        args.valores = list(range(inicio, fin + 1, paso))
    if not args.valores:
        print("Hay que indicar valores o --rango", file=sys.stderr)
        return 1

    args.funcion(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
