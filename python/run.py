"""Barridos del TP3: invoca el binario del motor N veces y arma el resumen.

Dos barridos, uno por subcomando:

    python run.py particulas --rango 50 300 50 --realizaciones 10
    python run.py configs vacia central_grande --realizaciones 5

Por defecto no se re-corre un caso cuyo CSV ya existe: los barridos son largos
y se reanudan a mano muchas veces. Con --forzar se recorre igual.
"""

import argparse
import csv
import re
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

    Cada corrida exitosa deja un sidecar ``<csv>.resumen`` con las metricas que
    imprime el motor por stdout. Asi, un barrido cortado a la mitad no pierde los
    tiempos: el resumen_agregado se puede reconstruir desde los sidecars.
    Solo se saltea un caso si ya existe tanto el CSV como su sidecar; si falta el
    sidecar se re-corre para volver a capturar las metricas.
    """
    sidecar = destino.with_suffix(".resumen")
    if destino.exists() and sidecar.exists() and not forzar:
        print(f"  ya registrado, se saltea: {destino.name}")
        return None

    destino.parent.mkdir(parents=True, exist_ok=True)
    comando = [str(config.EJECUTABLE), *argumentos, "--output", str(destino)]
    proceso = subprocess.run(comando, capture_output=True, text=True)
    if proceso.returncode != 0:
        print(f"  FALLO {destino.name}: {proceso.stderr.strip()}", file=sys.stderr)
        return None

    sidecar.write_text(proceso.stdout)
    print(f"  ok: {destino.name}")
    return parsear_resumen(proceso.stdout)


def fila_desde_sidecar_partículas(sidecar):
    """Reconstruye una fila del resumen de particulas desde un sidecar."""
    m = re.fullmatch(r"N(\d+)_s(\d+)", sidecar.stem)
    if not m:
        return None
    resumen = parsear_resumen(sidecar.read_text())
    return {
        "N": int(m.group(1)),
        "semilla": int(m.group(2)),
        "tiempo_ejecucion_s": resumen["tiempo_ejecucion_s"],
        "eventos": int(resumen["eventos"]),
        "goles": int(resumen["goles"]),
        "t90": resumen["t90"],
    }


def fila_desde_sidecar_config(sidecar):
    """Reconstruye una fila del resumen de configuraciones desde un sidecar."""
    m = re.fullmatch(r"N(\d+)_s(\d+)", sidecar.stem)
    if not m:
        return None
    resumen = parsear_resumen(sidecar.read_text())
    return {
        "configuracion": sidecar.parent.name,
        "semilla": int(m.group(2)),
        "tiempo_ejecucion_s": resumen["tiempo_ejecucion_s"],
        "eventos": int(resumen["eventos"]),
        "goles": int(resumen["goles"]),
        "t90": resumen["t90"],
    }


def escribir_resumen(directorio, columnas, claves, filas, extraer_sidecar=None):
    """Guarda un CSV agregado con una fila por realizacion.

    Se fusiona con lo que ya habia y con los sidecars ``*.resumen`` de la carpeta
    (buscandolos tambien en subcarpetas), de modo que reanudar un barrido no
    genere filas duplicadas y un barrido cortado siga produciendo resumenes
    completos. `claves` son las columnas que identifican univocamente una fila.
    """
    destino = directorio / "resumen.csv"
    previas = []
    if destino.exists():
        with open(destino, newline="") as archivo:
            previas = list(csv.DictReader(archivo))

    por_clave = {tuple(fila[c] for c in claves): fila for fila in previas}

    def agregar(fila):
        texto = {c: str(fila[c]) for c in columnas}
        por_clave[tuple(texto[c] for c in claves)] = texto

    for fila in filas:
        agregar(fila)
    if extraer_sidecar is not None:
        for sidecar in directorio.rglob("*.resumen"):
            fila = extraer_sidecar(sidecar)
            if fila is not None:
                agregar(fila)

    with open(destino, "w", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        for fila in sorted(por_clave.values(), key=lambda f: tuple(f[c] for c in claves)):
            escritor.writerow(fila)
    print(f"Resumen actualizado: {destino}")


def barrido_particulas(args):
    """Punto 1.1: tiempo de ejecucion vs N, sin obstaculos, tf fijo."""
    placement = getattr(args, "placement", "random")
    directorio = config.RESULTADOS / ("particulas_hex" if placement == "hex" else "particulas")
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
                "--placement", placement,
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

    escribir_resumen(
        directorio,
        ["N", "semilla", "tiempo_ejecucion_s", "eventos", "goles", "t90"],
        ["N", "semilla"],
        filas,
        extraer_sidecar=fila_desde_sidecar_partículas,
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

    escribir_resumen(
        directorio,
        ["configuracion", "semilla", "tiempo_ejecucion_s", "eventos", "goles", "t90"],
        ["configuracion", "semilla"],
        filas,
        extraer_sidecar=fila_desde_sidecar_config,
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
    particulas.add_argument("--placement", choices=["random", "hex"], default="random",
                            help="Colocacion de particulas: random (default) o hex")
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
