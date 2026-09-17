"""Hub del punto 1.2 para la presentacion: circulo naive (barrido de radio),
GA con simetria quad (K=5,9,13,17) y la pared (barrido de hiperparametros +
corrida final). Reemplaza el estado disperso que habia (wall_ganador.txt,
wall_ganador_250gens.txt y wall_demo con distinto fitness y sin log que
corresponda; quad con solo K=9 parcialmente corrido) por un unico punto de
entrada reproducible, logueado y con el mismo estilo de graficos en todas
las figuras.

    python punto_1_2.py --wipe             # borra resultados previos de estas 3 fases (pide confirmacion)
    python punto_1_2.py                    # corre las 3 fases (default), incremental
    python punto_1_2.py --phase pared
    python punto_1_2.py --phase circulo_naive quad_ga

Cada fase escribe sus CSVs/logs en build/resultados/ ANTES de graficar nada
(mismo patron que run.py/genetico.py), asi que un grafico nuevo que haga
falta mas adelante es una corrida de un script de plot/, no una corrida
nueva del hub. El fitness que reporta el GA es un proxy barato (pocas
semillas comunes por generacion) para elegir individuos/hiperparametros y
para graficar convergencia -- todo t90 que se presenta como resultado sale
de una simulacion real con --realizaciones 100 (run.barrido_configs).

Todo el output (incluido el de los subprocesos `simulador`/`optimizador`,
que imprimen su progreso en vivo) queda ademas en
build/resultados/punto_1_2/log_<timestamp>.txt via un `tee` de los file
descriptors, para poder revisar una corrida larga despues de que termino.
"""

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import config
import genetico
import run

PLOT_DIR = Path(__file__).resolve().parent / "plot"
sys.path.insert(0, str(PLOT_DIR))
import diagrama_configs  # noqa: E402
import estilo  # noqa: E402

ENTREGA_12 = config.ENTREGA / "1.2"

FASES = ["circulo_naive", "quad_ga", "pared"]

RADIOS_CIRCULO = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.34]

QUAD_KS = [5, 9, 13, 17]
QUAD_SEEDS = [1000, 1001, 1002, 1003, 1004]
QUAD_POBLACION = 48
QUAD_GENERACIONES = 60
QUAD_TOP_N_VALIDAR = 2  # candidatos por K que se validan con 100 corridas reales

# Por consigna, el radio de CUALQUIER obstaculo (incluidos los circulos
# chicos que arman el muro) tiene que ser estrictamente mayor al radio de
# la particula (config.RADIO = 0.0175 m) -- no hay margen para ir mas chico
# que eso por mas que geometricamente el muro quede sellado igual. 0.03 ya
# se probo (con profile=10) y no genero ningun individuo factible (circulos
# demasiado grandes para caber en el perfil); se deja igual en el barrido
# porque el fallo es por empaquetamiento a esa profundidad, no por el
# radio en si, y el pipeline lo saltea sin romperse si vuelve a fallar.
# OJO al interpretar el barrido de "profile": estas corridas exploratorias
# usan el mismo presupuesto (poblacion/generaciones) para cualquier
# cantidad de puntos de control, pero mas puntos = genoma mas grande =
# problema mas dificil de optimizar en el mismo presupuesto. Que "menos
# puntos" gane fitness puede ser el muro siendo mejor, o puede ser nada mas
# que el GA convergiendo mas facil con menos genes -- no se puede
# distinguir con este barrido tal como esta armado.
PARED_GRANOS = [0.018, 0.02, 0.025, 0.03]
PARED_PERFILES = [4, 6, 10, 14]
PARED_PERFIL_BASE = 10
PARED_SEMILLA = 1000
PARED_POBLACION_EXPL = 40
PARED_GENERACIONES_EXPL = 80
PARED_POBLACION_FINAL = 64
PARED_GENERACIONES_FINAL = 150

REALIZACIONES_STATS = 100

_TEE_PROCESO = None  # referencia viva para que no se cierre el pipe del tee


# --------------------------------------------------------------------------
# Utilidades de orquestacion (logging, banners, borrado)
# --------------------------------------------------------------------------

def habilitar_log_tee(ruta_log):
    """Duplica stdout/stderr del proceso (y de todo lo que arranque como
    subproceso, ya que heredan el file descriptor) hacia `ruta_log` ademas
    de la terminal, via un `tee` real: asi no hay que acordarse de un
    `| tee archivo` a mano para revisar una corrida larga despues."""
    global _TEE_PROCESO
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    sys.stdout.flush()
    sys.stderr.flush()
    _TEE_PROCESO = subprocess.Popen(["tee", "-a", str(ruta_log)], stdin=subprocess.PIPE)
    os.dup2(_TEE_PROCESO.stdin.fileno(), sys.stdout.fileno())
    os.dup2(_TEE_PROCESO.stdin.fileno(), sys.stderr.fileno())
    # Sin esto, sys.stdout queda con buffer de bloque (elegido al arrancar
    # el proceso, cuando el fd todavia no era un pipe a `tee`): los print()
    # del propio hub quedarian retenidos en memoria en vez de aparecer en
    # vivo. Los binarios C++ no tienen este problema (stderr es unbuffered
    # por default en el estandar), pero el print() de Python si.
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)


def banner(fase):
    print(f"\n{'=' * 70}\n=== FASE: {fase}  (inicio {datetime.now():%Y-%m-%d %H:%M:%S})\n{'=' * 70}")
    return time.monotonic()


def fin_banner(fase, inicio):
    print(f"=== FIN FASE: {fase}  (duracion {(time.monotonic() - inicio) / 60:.1f} min) ===\n")


def generacion_del_mejor(ruta_log):
    """Generacion (y su mejor_fitness) donde quedo fijado el individuo que
    termino siendo el ganador (`best` en Optimizer.cpp): la primera fila
    donde `mejor_fitness` toca el minimo de toda la columna. Es la misma
    reevaluacion con semillas nuevas cada generacion la que hace que esto no
    siempre sea la ultima generacion logueada (ver docstring de
    snapshots_poblacion.py)."""
    datos = pd.read_csv(ruta_log)
    fila = datos.loc[datos["mejor_fitness"].idxmin()]
    return int(fila["generacion"]), float(fila["mejor_fitness"])


def guardar_csv(ruta, columnas, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        for fila in filas:
            escritor.writerow(fila)
    print(f"CSV guardado en {ruta}")


def rutas_a_borrar():
    build = [
        config.RESULTADOS / "genetico" / "quad",
        config.RESULTADOS / "genetico" / "wall_demo",
        config.RESULTADOS / "genetico" / "pared",
        config.RESULTADOS / "genetico" / "pared_hparams",
    ]
    build += list((config.RESULTADOS / "configs").glob("circulo_r*"))
    build += list((config.RESULTADOS / "configs").glob("pared_perfil*"))
    for nombre in ("central_grande", "central_max", "wall_ganador", "wall_ganador_250gens",
                   "pared_ganadora"):
        build.append(config.RESULTADOS / "configs" / nombre)
    for k in QUAD_KS:
        build += list((config.RESULTADOS / "configs").glob(f"ga_k{k}_s*"))

    configs = list(config.CONFIGS.glob("circulo_r*.txt"))
    configs += list(config.CONFIGS.glob("pared_perfil*.txt"))
    for nombre in ("central_grande.txt", "central_max.txt", "wall_ganador.txt",
                   "wall_ganador_250gens.txt"):
        configs.append(config.CONFIGS / nombre)
    for k in QUAD_KS:
        configs += list(config.CONFIGS.glob(f"ga_k{k}_s*.txt"))

    return [p for p in build if p.exists()], [p for p in configs if p.exists()]


def wipe(confirmar=True):
    rutas_build, rutas_configs = rutas_a_borrar()
    todas = rutas_build + rutas_configs
    if not todas:
        print("Nada para borrar.")
        return
    print("Se va a borrar (solo circulo_naive/quad_ga/pared; hz_k*/nn_k*/bloque_*/embudo/vacia "
          "quedan intactos):")
    for ruta in todas:
        print(f"  {ruta}")
    if confirmar:
        respuesta = input("\nConfirmar borrado? [s/N] ").strip().lower()
        if respuesta != "s":
            print("Cancelado.")
            return
    for ruta in todas:
        shutil.rmtree(ruta) if ruta.is_dir() else ruta.unlink()
    print("Borrado listo.")


# --------------------------------------------------------------------------
# Fase 1: circulo naive, barrido de radio
# --------------------------------------------------------------------------

def escribir_config_circulo(radio):
    ruta = config.CONFIGS / f"circulo_r{radio:.2f}.txt"
    ruta.write_text(
        "# Circulo naive centrado, barrido de radio (punto 1.2)\n"
        "# Formato: una linea por obstaculo con \"x_k y_k R_k\" en metros.\n"
        f"{config.LARGO / 2:.2f} {config.ANCHO / 2:.2f} {radio:.6f}\n"
    )
    return ruta


def elegir_mejor_caso_circulo(nombres):
    ruta = config.RESULTADOS / "configs" / "resumen.csv"
    if not ruta.exists():
        return None
    datos = pd.read_csv(ruta)
    datos = datos[datos["configuracion"].isin(nombres) & (datos["t90"] >= 0)]
    if datos.empty:
        return None
    fila = datos.loc[datos["t90"].idxmin()]
    return fila["configuracion"], int(fila["semilla"])


def guardar_trayectoria_puntual(nombre, semilla, sufijo):
    """Re-corre (config, semilla) puntual con --trajectory: el barrido
    estadistico solo guarda trayectoria para la semilla base (i=0), y el
    mejor caso real puede haber salido con otra semilla."""
    directorio = config.RESULTADOS / "configs" / nombre
    destino = directorio / f"N{config.PARTICULAS}_s{semilla}.csv"
    ruta_trayectoria = directorio / f"trayectoria_{sufijo}_s{semilla}.csv"
    argumentos = [
        "--config", str(config.CONFIGS / f"{nombre}.txt"),
        "--particles", str(config.PARTICULAS),
        "--tmax", str(config.TIEMPO_MAXIMO),
        "--seed", str(semilla),
        "--cada-eventos", "50",
        "--trajectory", str(ruta_trayectoria),
    ]
    run.correr(destino, argumentos, forzar=True)
    return ruta_trayectoria


DURACION_MAX_VIDEO = 20.0  # segundos: nadie necesita ver la cola de rezagados


def animar_caso(nombre, ruta_trayectoria, prefijo_salida):
    comando = [
        sys.executable, str(PLOT_DIR / "animacion.py"),
        "--trayectoria", str(ruta_trayectoria),
        "--obstaculos", str(config.CONFIGS / f"{nombre}.txt"),
        "--salida", str(ENTREGA_12 / f"{prefijo_salida}.mp4"),
        "--fotograma", str(ENTREGA_12 / f"{prefijo_salida}_frame.png"),
        "--dt-cuadro", "0.04", "--fps", "25",
        "--duracion-max", str(DURACION_MAX_VIDEO),
    ]
    subprocess.run(comando, check=True)


def fase_circulo_naive():
    inicio = banner("circulo_naive")

    nombres = ["vacia"]
    for radio in RADIOS_CIRCULO:
        escribir_config_circulo(radio)
        nombres.append(f"circulo_r{radio:.2f}")

    args_sim = SimpleNamespace(valores=nombres, realizaciones=REALIZACIONES_STATS, forzar=False,
                                cada_eventos=200, particulas=config.PARTICULAS, trayectoria=True)
    run.barrido_configs(args_sim)

    # "vacia" (radio=0) casi seguro gana en t90 -- es el punto de referencia
    # del barrido, no un caso interesante para animar como "mejor caso" del
    # experimento del circulo. Se lo deja afuera solo para elegir la animacion.
    nombres_con_obstaculo = [n for n in nombres if n != "vacia"]
    mejor = elegir_mejor_caso_circulo(nombres_con_obstaculo)
    if mejor is not None:
        nombre, semilla = mejor
        print(f"  mejor caso: {nombre} semilla={semilla}")
        ruta_trayectoria = guardar_trayectoria_puntual(nombre, semilla, "mejor")
        animar_caso(nombre, ruta_trayectoria, "circulo_mejor_caso")
    else:
        print("  no se encontro un caso con t90 valido, se saltea la animacion", file=sys.stderr)

    subprocess.run([sys.executable, str(PLOT_DIR / "t90_vs_radio.py"),
                    "--salida", str(ENTREGA_12 / "circulo_t90_vs_radio.png")], check=True)

    fin_banner("circulo_naive", inicio)


# --------------------------------------------------------------------------
# Fase 2: GA con simetria quad, K=5,9,13,17
# --------------------------------------------------------------------------

def resumen_de_sidecar_quad(k, semilla):
    sidecar = config.RESULTADOS / "genetico" / "quad" / f"K{k}_s{semilla}.resumen"
    return run.parsear_resumen(sidecar.read_text()) if sidecar.exists() else None


def graficar_convergencia_quad(representantes):
    comando = [sys.executable, str(PLOT_DIR / "convergencia_multi_k.py")]
    for k in sorted(representantes):
        semilla = representantes[k]
        log_path = config.RESULTADOS / "genetico" / "quad" / f"K{k}_s{semilla}" / "log.csv"
        comando += ["--serie", f"K={k}", str(log_path)]
    comando += ["--salida", str(ENTREGA_12 / "quad_convergencia.png")]
    subprocess.run(comando, check=True)


def filtrar_resumen(nombres, ruta_salida, renombrar=None):
    """resumen.csv es un agregado de TODAS las configs alguna vez simuladas
    (incluidas hz_k*/nn_k*/... que esta fase no toca): t90_vs_configuracion.py
    grafica cada `configuracion` que encuentra, sin filtrar, asi que hay que
    darle un CSV recortado a solo lo que corresponde a esta fase. `renombrar`
    (dict nombre->etiqueta) cambia el valor de la columna antes de guardar,
    para que el eje x de esa figura muestre una etiqueta linda (ej. "K=9")
    en vez del nombre interno con semilla (ej. "ga_k9_s1002")."""
    datos = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    datos = datos[datos["configuracion"].isin(nombres)].copy()
    if renombrar:
        datos["configuracion"] = datos["configuracion"].map(renombrar).fillna(datos["configuracion"])
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    datos.to_csv(ruta_salida, index=False)
    return ruta_salida


def graficar_t90_quad(representantes):
    etiquetas = {f"ga_k{k}_s{representantes[k]}": f"K={k}" for k in sorted(representantes)}
    ruta_filtrada = filtrar_resumen(list(etiquetas),
                                     config.RESULTADOS / "genetico" / "quad_t90_resumen.csv",
                                     renombrar=etiquetas)
    comando = [sys.executable, str(PLOT_DIR / "t90_vs_configuracion.py"),
               "--resumen", str(ruta_filtrada),
               "--orden", *etiquetas.values(),
               "--salida", str(ENTREGA_12 / "quad_t90_real.png")]
    subprocess.run(comando, check=True)


def graficar_t90_vs_k(representantes):
    """Misma info que graficar_t90_quad, pero con K como eje numerico (linea
    de tendencia), igual que circulo_t90_vs_radio.png -- t90_vs_configuracion.py
    trata cada config como categoria suelta, sin relacion de orden entre K's."""
    resumen = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    comando = [sys.executable, str(PLOT_DIR / "t90_vs_k.py"),
               "--salida", str(ENTREGA_12 / "quad_t90_vs_k.png")]
    for k in sorted(representantes):
        nombre = f"ga_k{k}_s{representantes[k]}"
        valores = resumen.loc[(resumen["configuracion"] == nombre) & (resumen["t90"] >= 0), "t90"]
        if len(valores):
            comando += ["--punto", str(k), str(valores.mean()), str(valores.std())]
    subprocess.run(comando, check=True)


def graficar_geometrias_quad(representantes):
    import matplotlib.pyplot as plt

    ks = sorted(representantes)
    columnas = estilo.columnas_grilla(len(ks))
    filas = -(-len(ks) // columnas)
    fig, ejes = plt.subplots(filas, columnas,
                              figsize=(5 * columnas, 5 * config.ANCHO / config.LARGO * filas))
    ejes = [ejes] if len(ks) == 1 else list(ejes.flat)

    resumen = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    print("  geometrias quad (t90 real, no fitness del GA):")
    for ax, k in zip(ejes, ks):
        nombre = f"ga_k{k}_s{representantes[k]}"
        valores = resumen.loc[(resumen["configuracion"] == nombre) & (resumen["t90"] >= 0), "t90"]
        titulo = f"K={k}"
        if len(valores):
            titulo += f"   t90 = {valores.mean():.2f} ± {valores.std():.2f} s"
            print(f"    K={k}: t90 = {estilo.formatear_valor(valores.mean(), valores.std(), 's')}")
        diagrama_configs.dibujar_mesa(ax, diagrama_configs.leer_obstaculos(
            config.CONFIGS / f"{nombre}.txt"), titulo=titulo)
    for ax in ejes[len(ks):]:
        ax.axis("off")
    estilo.guardar(fig, ENTREGA_12 / "quad_geometrias.png")


def graficar_snapshots_quad(k, semilla):
    pob_dir = config.RESULTADOS / "genetico" / "quad" / f"K{k}_s{semilla}" / "poblacion"
    if not pob_dir.exists():
        print(f"  sin poblacion logueada para K={k}, se saltea snapshot", file=sys.stderr)
        return
    nombre = f"ga_k{k}_s{semilla}"
    etiqueta = f"Ganador K={k}"
    resumen = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    valores = resumen.loc[(resumen["configuracion"] == nombre) & (resumen["t90"] >= 0), "t90"]
    gen, fitness = generacion_del_mejor(pob_dir.parent / "log.csv")
    if len(valores):
        etiqueta += f"\nt90 = {valores.mean():.2f} ± {valores.std():.2f} s"
    etiqueta += f"   fitness = {fitness:.2f} (gen {gen})"
    tercio = max(QUAD_GENERACIONES // 3, 1)
    comando = [sys.executable, str(PLOT_DIR / "snapshots_poblacion.py"),
               "--population-log", str(pob_dir),
               "--generaciones", "0", str(tercio), str(2 * tercio),
               "--solo-mejor", "--titulo-panel", "completo",
               "--config-final", str(config.CONFIGS / f"{nombre}.txt"),
               "--config-final-etiqueta", etiqueta,
               "--salida", str(ENTREGA_12 / f"quad_snapshots_k{k}.png")]
    subprocess.run(comando, check=True)


def fase_quad_ga():
    inicio = banner("quad_ga")

    # El fitness del GA se mide con pocas semillas comunes por generacion:
    # es ruidoso, y el de menor fitness entre pocas corridas puede haber
    # tenido suerte con esas semillas particulares sin generalizar. En vez
    # de confiar en el fitness para el ganador final, se valida a los
    # QUAD_TOP_N_VALIDAR mejores candidatos de cada K con 100 simulaciones
    # reales y se elige por t90 real -- mismo criterio "filtro barato,
    # validacion cara solo sobre los que sobreviven" que ya usa
    # evaluar_todas_configs.py para hz_k*/nn_k*.
    candidatos_por_k = {}
    for k in QUAD_KS:
        candidatos = []
        for semilla in QUAD_SEEDS:
            args_ga = SimpleNamespace(symmetry="quad", population=QUAD_POBLACION,
                                       generations=QUAD_GENERACIONES, seeds_per_gen=5,
                                       max_radius=None, mutation_gene_rate=None, elitism=None,
                                       threads=None, population_log=True,
                                       population_log_every=5)
            resumen = genetico.correr_ga(k, semilla, args_ga, forzar=False)
            if resumen is None:
                resumen = resumen_de_sidecar_quad(k, semilla)
            if resumen is not None:
                candidatos.append((semilla, resumen["mejor_fitness"]))
        if not candidatos:
            print(f"  K={k}: ninguna semilla funciono, se saltea", file=sys.stderr)
            continue
        candidatos.sort(key=lambda c: c[1])
        top = candidatos[:QUAD_TOP_N_VALIDAR]
        print(f"  K={k}: top {len(top)} por fitness GA (proxy) -- " +
              ", ".join(f"s{s}={f:.3f}" for s, f in top))
        candidatos_por_k[k] = top

    if not candidatos_por_k:
        print("Ningun K funciono en quad_ga, se aborta la fase", file=sys.stderr)
        return

    nombre_de = {}
    for k, top in candidatos_por_k.items():
        for semilla, _ in top:
            origen = config.RESULTADOS / "genetico" / "quad" / f"K{k}_s{semilla}" / "config.txt"
            nombre = f"ga_k{k}_s{semilla}"
            (config.CONFIGS / f"{nombre}.txt").write_text(origen.read_text())
            nombre_de[(k, semilla)] = nombre

    args_sim = SimpleNamespace(valores=list(nombre_de.values()), realizaciones=REALIZACIONES_STATS,
                                forzar=False, cada_eventos=200, particulas=config.PARTICULAS,
                                trayectoria=False)
    run.barrido_configs(args_sim)

    resumen_real = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    representantes = {}
    for k, top in candidatos_por_k.items():
        mejor_semilla, mejor_t90 = None, float("inf")
        for semilla, _ in top:
            valores = resumen_real.loc[(resumen_real["configuracion"] == nombre_de[(k, semilla)]) &
                                        (resumen_real["t90"] >= 0), "t90"]
            if len(valores) and valores.mean() < mejor_t90:
                mejor_t90, mejor_semilla = valores.mean(), semilla
        if mejor_semilla is None:
            print(f"  K={k}: ningun candidato llego a F_u=0.9, se saltea", file=sys.stderr)
            continue
        print(f"  K={k}: ganador real -- semilla {mejor_semilla}, t90 real = {mejor_t90:.3f} s "
              f"(mejor de {len(top)} candidatos validados con {REALIZACIONES_STATS} corridas)")
        representantes[k] = mejor_semilla
        # el/los candidato(s) que perdieron la validacion no quedan como
        # config "oficial" de este K -- solo el ganador real.
        for semilla, _ in top:
            if semilla != mejor_semilla:
                (config.CONFIGS / f"{nombre_de[(k, semilla)]}.txt").unlink(missing_ok=True)

    if not representantes:
        print("Ningun K tuvo un candidato valido en quad_ga, se aborta la fase", file=sys.stderr)
        return

    graficar_convergencia_quad(representantes)
    graficar_t90_quad(representantes)
    graficar_t90_vs_k(representantes)
    graficar_geometrias_quad(representantes)
    for k in (9, 17):
        if k in representantes:
            graficar_snapshots_quad(k, representantes[k])

    fin_banner("quad_ga", inicio)


# --------------------------------------------------------------------------
# Fase 3: pared -- barrido de hiperparametros + corrida final
# --------------------------------------------------------------------------

def correr_ga_pared(grano, perfil, semilla, poblacion, generaciones, directorio,
                     log=True, population_log=False, forzar=False):
    # directorio.with_suffix() rompe con nombres tipo "grain0.015_profile10"
    # (el "." de 0.015 no es una extension): concatenar el sufijo a mano.
    sidecar = directorio.parent / f"{directorio.name}.resumen"
    config_out = directorio / "config.txt"
    log_out = directorio / "log.csv"

    if config_out.exists() and sidecar.exists() and not forzar:
        print(f"  ya registrado, se saltea: {directorio.name}")
        return run.parsear_resumen(sidecar.read_text())

    directorio.mkdir(parents=True, exist_ok=True)
    comando = [
        str(config.EJECUTABLE_GA),
        "--wall-profile", str(perfil),
        "--wall-grain", str(grano),
        "--population", str(poblacion),
        "--generations", str(generaciones),
        "--seed", str(semilla),
        "--config-out", str(config_out),
    ]
    if log:
        comando += ["--log", str(log_out)]
    if population_log:
        poblacion_out = directorio / "poblacion"
        poblacion_out.mkdir(parents=True, exist_ok=True)
        comando += ["--population-log", str(poblacion_out), "--population-log-every", "5"]

    proceso = subprocess.run(comando, stdout=subprocess.PIPE, text=True)
    if proceso.returncode != 0:
        print(f"  FALLO {directorio.name} (ver error arriba)", file=sys.stderr)
        return None
    sidecar.write_text(proceso.stdout)
    print(f"  ok: {directorio.name}")
    return run.parsear_resumen(proceso.stdout)


def graficar_hparams_pared(ruta_resumen):
    subprocess.run([sys.executable, str(PLOT_DIR / "hparams_pared.py"),
                    "--resumen", str(ruta_resumen),
                    "--salida", str(ENTREGA_12 / "pared_hparams.png")], check=True)


def graficar_geometrias_pared(grano_ganador):
    """4 paredes candidatas (una por cantidad de puntos de perfil probada,
    con el grano ganador fijo) con su t90 real -- ojo que estas corrieron
    con el presupuesto exploratorio (PARED_POBLACION_EXPL/GENERACIONES_EXPL),
    no el final pulido, asi que son peores que pared_ganadora en general;
    la comparacion es para mostrar el efecto de la cantidad de puntos, no
    para elegir "la mejor de las 4" como resultado."""
    import matplotlib.pyplot as plt

    nombres = []
    for perfil in PARED_PERFILES:
        origen = (config.RESULTADOS / "genetico" / "pared_hparams" /
                  f"grain{grano_ganador:.3f}_profile{perfil}" / "config.txt")
        if not origen.exists():
            continue
        nombre = f"pared_perfil{perfil}"
        (config.CONFIGS / f"{nombre}.txt").write_text(origen.read_text())
        nombres.append((perfil, nombre))
    if not nombres:
        print("  no hay candidatos de pared para graficar geometrias", file=sys.stderr)
        return

    args_sim = SimpleNamespace(valores=[n for _, n in nombres], realizaciones=REALIZACIONES_STATS,
                                forzar=False, cada_eventos=200, particulas=config.PARTICULAS,
                                trayectoria=False)
    run.barrido_configs(args_sim)

    resumen = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    n = len(nombres)
    columnas = estilo.columnas_grilla(n)
    filas = -(-n // columnas)
    fig, ejes = plt.subplots(filas, columnas,
                              figsize=(5 * columnas, 5 * config.ANCHO / config.LARGO * filas))
    ejes = [ejes] if n == 1 else list(ejes.flat)

    print("  geometrias pared por cantidad de puntos de perfil (t90 real, grano fijo en el "
          "ganador):")
    for ax, (perfil, nombre) in zip(ejes, nombres):
        valores = resumen.loc[(resumen["configuracion"] == nombre) & (resumen["t90"] >= 0), "t90"]
        titulo = f"perfil={perfil}"
        if len(valores):
            titulo += f"   t90 = {valores.mean():.2f} ± {valores.std():.2f} s"
            print(f"    perfil={perfil}: t90 = "
                  f"{estilo.formatear_valor(valores.mean(), valores.std(), 's')}")
        diagrama_configs.dibujar_mesa(ax, diagrama_configs.leer_obstaculos(
            config.CONFIGS / f"{nombre}.txt"), titulo=titulo)
    for ax in ejes[n:]:
        ax.axis("off")
    estilo.guardar(fig, ENTREGA_12 / "pared_geometrias.png")


def graficar_convergencia_pared(ruta_log):
    # convergencia_ga.py grafica el promedio +/- desvio de TODA la poblacion
    # por generacion; para la pared interesa solo el mejor individuo (una
    # linea limpia, sin banda de sombra) -- convergencia_multi_k.py ya hace
    # exactamente eso, se reusa con una sola serie.
    subprocess.run([sys.executable, str(PLOT_DIR / "convergencia_multi_k.py"),
                    "--serie", "Pared ganadora", str(ruta_log),
                    "--salida", str(ENTREGA_12 / "pared_convergencia.png")], check=True)


def graficar_snapshots_pared(ruta_poblacion):
    etiqueta = "Pared ganadora"
    resumen = pd.read_csv(config.RESULTADOS / "configs" / "resumen.csv")
    valores = resumen.loc[(resumen["configuracion"] == "pared_ganadora") & (resumen["t90"] >= 0),
                          "t90"]
    gen, fitness = generacion_del_mejor(ruta_poblacion.parent / "log.csv")
    if len(valores):
        etiqueta += f"\nt90 = {valores.mean():.2f} ± {valores.std():.2f} s"
    etiqueta += f"   fitness = {fitness:.2f} (gen {gen})"
    generaciones = [str(g) for g in range(0, PARED_GENERACIONES_FINAL, 30)]
    subprocess.run([sys.executable, str(PLOT_DIR / "snapshots_poblacion.py"),
                    "--population-log", str(ruta_poblacion),
                    "--generaciones", *generaciones,
                    "--solo-mejor", "--titulo-panel", "completo",
                    "--config-final", str(config.CONFIGS / "pared_ganadora.txt"),
                    "--config-final-etiqueta", etiqueta,
                    "--salida", str(ENTREGA_12 / "pared_snapshots.png")], check=True)


def fase_pared():
    inicio = banner("pared")
    directorio_hparams = config.RESULTADOS / "genetico" / "pared_hparams"
    filas = []

    resultados_grano = {}
    for grano in PARED_GRANOS:
        caso = directorio_hparams / f"grain{grano:.3f}_profile{PARED_PERFIL_BASE}"
        resumen = correr_ga_pared(grano, PARED_PERFIL_BASE, PARED_SEMILLA, PARED_POBLACION_EXPL,
                                   PARED_GENERACIONES_EXPL, caso, log=False)
        if resumen is not None:
            resultados_grano[grano] = resumen["mejor_fitness"]
            filas.append({"variable": "grain", "valor": grano, "fijo": PARED_PERFIL_BASE,
                          "mejor_fitness": resumen["mejor_fitness"]})

    if not resultados_grano:
        print("Ningun punto del barrido de grano funciono, se aborta la fase pared",
              file=sys.stderr)
        return
    grano_ganador = min(resultados_grano, key=resultados_grano.get)
    print(f"  grano ganador: {grano_ganador} (fitness GA={resultados_grano[grano_ganador]:.3f})")

    resultados_perfil = {PARED_PERFIL_BASE: resultados_grano[grano_ganador]}
    for perfil in PARED_PERFILES:
        if perfil == PARED_PERFIL_BASE:
            continue
        caso = directorio_hparams / f"grain{grano_ganador:.3f}_profile{perfil}"
        resumen = correr_ga_pared(grano_ganador, perfil, PARED_SEMILLA, PARED_POBLACION_EXPL,
                                   PARED_GENERACIONES_EXPL, caso, log=False)
        if resumen is not None:
            resultados_perfil[perfil] = resumen["mejor_fitness"]
            filas.append({"variable": "profile", "valor": perfil, "fijo": grano_ganador,
                          "mejor_fitness": resumen["mejor_fitness"]})
    filas.append({"variable": "profile", "valor": PARED_PERFIL_BASE, "fijo": grano_ganador,
                  "mejor_fitness": resultados_perfil[PARED_PERFIL_BASE]})

    perfil_ganador = min(resultados_perfil, key=resultados_perfil.get)
    print(f"  perfil ganador: {perfil_ganador} (fitness GA={resultados_perfil[perfil_ganador]:.3f})")

    ruta_resumen_hparams = directorio_hparams / "resumen.csv"
    guardar_csv(ruta_resumen_hparams, ["variable", "valor", "fijo", "mejor_fitness"], filas)
    graficar_hparams_pared(ruta_resumen_hparams)
    graficar_geometrias_pared(grano_ganador)

    caso_final = config.RESULTADOS / "genetico" / "pared"
    # forzar=True a proposito: este directorio tiene nombre fijo (no
    # incluye grano/perfil en la ruta, a diferencia del barrido
    # exploratorio), asi que si el ganador de hiperparametros cambia entre
    # corridas, "ya registrado" reusaria en silencio el resultado de la
    # combinacion vieja -- exactamente el bug que paso ac.
    resumen_final = correr_ga_pared(grano_ganador, perfil_ganador, PARED_SEMILLA,
                                     PARED_POBLACION_FINAL, PARED_GENERACIONES_FINAL, caso_final,
                                     log=True, population_log=True, forzar=True)
    if resumen_final is None:
        print("La corrida final de la pared fallo, se aborta la fase", file=sys.stderr)
        return

    destino_config = config.CONFIGS / "pared_ganadora.txt"
    destino_config.write_text((caso_final / "config.txt").read_text())

    args_sim = SimpleNamespace(valores=["pared_ganadora"], realizaciones=REALIZACIONES_STATS,
                                forzar=False, cada_eventos=200, particulas=config.PARTICULAS,
                                trayectoria=True)
    run.barrido_configs(args_sim)

    graficar_convergencia_pared(caso_final / "log.csv")
    graficar_snapshots_pared(caso_final / "poblacion")

    ruta_trayectoria = (config.RESULTADOS / "configs" / "pared_ganadora" /
                        f"trayectoria_s{PARED_SEMILLA}.csv")
    if ruta_trayectoria.exists():
        animar_caso("pared_ganadora", ruta_trayectoria, "pared_mejor_caso")

    fin_banner("pared", inicio)


# --------------------------------------------------------------------------
# Comparacion final entre las 3 fases (corre siempre al final, con lo que
# haya disponible: mesa vacia siempre esta, quad/pared dependen de que esas
# fases se hayan corrido al menos una vez antes)
# --------------------------------------------------------------------------

def graficar_comparacion_final():
    ruta_resumen = config.RESULTADOS / "configs" / "resumen.csv"
    if not ruta_resumen.exists():
        return
    resumen = pd.read_csv(ruta_resumen)

    candidatos = {}
    if (resumen["configuracion"] == "vacia").any():
        candidatos["vacia"] = "Mesa vacia"

    mejor_circulo = None
    for ruta in sorted(config.CONFIGS.glob("circulo_r*.txt")):
        nombre = ruta.stem
        valores = resumen.loc[(resumen["configuracion"] == nombre) & (resumen["t90"] >= 0), "t90"]
        if len(valores) and (mejor_circulo is None or valores.mean() < mejor_circulo[1]):
            mejor_circulo = (nombre, valores.mean())
    if mejor_circulo is not None:
        candidatos[mejor_circulo[0]] = "Mejor circulo"

    mejor_quad = None
    for ruta in sorted(config.CONFIGS.glob("ga_k*_s*.txt")):
        nombre = ruta.stem
        valores = resumen.loc[(resumen["configuracion"] == nombre) & (resumen["t90"] >= 0), "t90"]
        if len(valores) and (mejor_quad is None or valores.mean() < mejor_quad[1]):
            m = re.match(r"ga_k(\d+)_s\d+", nombre)
            mejor_quad = (nombre, valores.mean(), m.group(1) if m else "?")
    if mejor_quad is not None:
        candidatos[mejor_quad[0]] = f"Mejor quad (K={mejor_quad[2]})"

    if (config.CONFIGS / "pared_ganadora.txt").exists() and \
            (resumen["configuracion"] == "pared_ganadora").any():
        candidatos["pared_ganadora"] = "Mejor pared"

    if len(candidatos) < 2:
        print("Faltan resultados (vacia/mejor quad/mejor pared) para la comparacion final, "
              "se saltea", file=sys.stderr)
        return

    ruta_filtrada = filtrar_resumen(list(candidatos),
                                     config.RESULTADOS / "comparacion_final_resumen.csv",
                                     renombrar=candidatos)
    comando = [sys.executable, str(PLOT_DIR / "t90_vs_configuracion.py"),
               "--resumen", str(ruta_filtrada),
               "--orden", *candidatos.values(),
               "--salida", str(ENTREGA_12 / "comparacion_final.png")]
    subprocess.run(comando, check=True)


# --------------------------------------------------------------------------

FASES_FUNCIONES = {
    "circulo_naive": fase_circulo_naive,
    "quad_ga": fase_quad_ga,
    "pared": fase_pared,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase", nargs="+", choices=FASES, default=FASES, dest="phase",
                        help="Que fases correr (default: las 3)")
    parser.add_argument("--wipe", action="store_true",
                        help="Borra resultados previos de estas 3 fases y termina, sin correr nada")
    parser.add_argument("--si", action="store_true",
                        help="Con --wipe, no pide confirmacion antes de borrar")
    args = parser.parse_args()

    if args.wipe:
        wipe(confirmar=not args.si)
        return 0

    if not config.EJECUTABLE.exists() or not config.EJECUTABLE_GA.exists():
        print("Falta compilar: no existen simulador/optimizador en build/. "
              "Corre `cmake --build build` primero.", file=sys.stderr)
        return 1

    ruta_log = config.RESULTADOS / "punto_1_2" / f"log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    habilitar_log_tee(ruta_log)
    print(f"Log completo de esta corrida en {ruta_log}\n")

    inicio_total = time.monotonic()
    for fase in args.phase:
        FASES_FUNCIONES[fase]()
    graficar_comparacion_final()
    print(f"\n=== TODO LISTO ({(time.monotonic() - inicio_total) / 60:.1f} min totales) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
