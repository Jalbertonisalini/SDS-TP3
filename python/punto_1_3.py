"""Punto 1.3: coeficiente de difusion D de cada configuracion y su relacion con <t90>.

    python punto_1_3.py                   # corre lo que falte, calcula y grafica
    python punto_1_3.py --forzar          # re-corre todas las simulaciones
    python punto_1_3.py --solo-graficos   # solo calcula y grafica (lo usa generar_entrega.sh)

Consigna: DCM promediado sobre todas las particulas moviles (frescas y usadas)
de UNA realizacion, ajuste lineal con el metodo de la Teorica 0 (DCM = 4 D t
en 2D), D para la mesa vacia y para cada configuracion estudiada, y ver si hay
correlacion entre D y <t90>.

Como pidio la catedra, el tramo lineal de cada configuracion se elige a ojo
sobre la curva de una realizacion (se marca en dcm_comparacion.png) y D se
ajusta solo en ese tramo. Ademas se repite el ajuste, con la misma ventana, en
cada realizacion, para reportar <D> +/- desvio y compararlo con <t90>.

El motor no calcula ningun observable: DCM y t90 salen de observables.py a
partir de sus archivos de salida. Todo vive en build/resultados/punto_1_3/,
aparte de configs/ (los datos de las figuras de 1.2 no se tocan):
- t90/<config>/N100_s<semilla>.csv: registro de goles de cada realizacion
  hasta t_max, de donde sale t90 y <t90> +/- desvio.
- dcm/<config>/trayectoria_N100_s<semilla>.csv: estado de todas las
  particulas cada CADA_EVENTOS_DCM eventos, para resolver el tramo lineal,
  que dura pocos segundos antes de saturar por el tamano finito de la mesa.
- dcm/<config>/dcm_N100_s<semilla>.csv: DCM(t) calculado desde esa
  trayectoria (se guarda para no releer varios GB en cada grafico).
"""

import argparse
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config
import observables
import run
from plot import estilo
from plot.dcm_vs_tiempo import DIMENSION, barrer_pendiente, dibujar_dcm, dibujar_error

# Las configuraciones de la comparacion final de 1.2 (nombre en configs/ ->
# etiqueta de figura), con las mismas etiquetas que comparacion_final.png.
CONFIGURACIONES = {
    "vacia": "Mesa vacia",
    "circulo_r0.34": "Mejor circulo",
    "ga_k9_s1003": "Mejor quad (K=9)",
    "pared_ganadora": "Mejor pared",
}

# Igual que REALIZACIONES_STATS de punto_1_2.py: mismas semillas, asi que <t90>
# coincide con el que reporta 1.2 (la consigna pide al menos 5).
REALIZACIONES = 100
SEMILLA_DCM = config.SEMILLA_BASE
CADA_EVENTOS_DCM = 10  # 200 (default de run.py) deja ~0.2 s entre muestras en la mesa vacia

# Las trayectorias para el DCM llegan hasta TMAX_DCM: solo interesa el tramo
# lineal y el comienzo de la saturacion, y cortar antes mantiene los archivos
# chicos (igual pesan ~10-30 MB por realizacion).
TMAX_DCM = 20.0  # s

# Fin del tramo lineal de cada configuracion (ajuste DCM = c t sobre [0, t]),
# elegido a ojo sobre la curva de SEMILLA_DCM en dcm_comparacion.png, donde se
# marca con una linea vertical. Se usa la misma ventana en todas las
# realizaciones, asi que tambien se chequeo contra el DCM promedio de las
# REALIZACIONES, que se aparta de la recta un poco antes que la realizacion
# mostrada.
VENTANA_AJUSTE = {  # s
    "vacia": 1.5,
    "circulo_r0.34": 1.2,
    "ga_k9_s1003": 1.0,
    "pared_ganadora": 1.4,
}
TMAX_GRAFICO = 10.0  # s, muestra el tramo ajustado y el comienzo de la saturacion
SEPARACION_GRILLA = 3.0  # espacio entre paneles de las figuras 2x2 (ver estilo.guardar)

DIRECTORIO_RESULTADOS = config.RESULTADOS / "punto_1_3"
DIRECTORIO_T90 = DIRECTORIO_RESULTADOS / "t90"
DIRECTORIO_DCM = DIRECTORIO_RESULTADOS / "dcm"
DIRECTORIO_ENTREGA = config.ENTREGA / "1.3"
TABLA = DIRECTORIO_RESULTADOS / "difusion_vs_t90.csv"


def semillas():
    return config.SEMILLA_BASE + np.arange(REALIZACIONES)


def ruta_goles_t90(nombre, semilla):
    return DIRECTORIO_T90 / nombre / f"N{config.PARTICULAS}_s{semilla}.csv"


def ruta_goles_dcm(nombre, semilla):
    return DIRECTORIO_DCM / nombre / f"N{config.PARTICULAS}_s{semilla}.csv"


def ruta_trayectoria(nombre, semilla):
    return DIRECTORIO_DCM / nombre / f"trayectoria_N{config.PARTICULAS}_s{semilla}.csv"


def ruta_serie_dcm(nombre, semilla=SEMILLA_DCM):
    return DIRECTORIO_DCM / nombre / f"dcm_N{config.PARTICULAS}_s{semilla}.csv"


def nombre_de_archivo(nombre):
    """LaTeX interpreta el punto de "circulo_r0.34" como extension en \\includegraphics."""
    return nombre.replace(".", "p")


def argumentos_base(nombre, semilla):
    return [
        "--config", str(config.CONFIGS / f"{nombre}.txt"),
        "--particles", str(config.PARTICULAS),
        "--seed", str(semilla),
    ]


def simular_t90(forzar):
    """Registro de goles de cada realizacion hasta t_max (sin trayectoria)."""
    for nombre in CONFIGURACIONES:
        for semilla in semillas():
            argumentos = argumentos_base(nombre, semilla) + ["--tmax", str(config.TIEMPO_MAXIMO)]
            run.correr(ruta_goles_t90(nombre, semilla), argumentos, forzar)


def simular_dcm(forzar):
    """Trayectoria de cada realizacion hasta TMAX_DCM y su DCM(t) calculado en postproceso."""
    for nombre in CONFIGURACIONES:
        for semilla in semillas():
            argumentos = argumentos_base(nombre, semilla) + [
                "--tmax", str(TMAX_DCM),
                "--cada-eventos", str(CADA_EVENTOS_DCM),
                "--trajectory", str(ruta_trayectoria(nombre, semilla)),
            ]
            run.correr(ruta_goles_dcm(nombre, semilla), argumentos, forzar)
            if forzar or not ruta_serie_dcm(nombre, semilla).exists():
                calcular_dcm(nombre, semilla)


def calcular_dcm(nombre, semilla):
    trayectoria = observables.leer_trayectoria(ruta_trayectoria(nombre, semilla))
    observables.dcm(trayectoria).to_csv(ruta_serie_dcm(nombre, semilla), index=False)


def estadistica_t90():
    """<t90>, desvio y cantidad de realizaciones por configuracion, con t90
    calculado desde el registro de goles de cada realizacion."""
    filas = []
    for nombre in CONFIGURACIONES:
        for semilla in semillas():
            ruta = ruta_goles_t90(nombre, semilla)
            if not ruta.exists():
                sys.exit(f"Falta el registro de goles {ruta}: correr sin --solo-graficos.")
            goles = observables.leer_goles(ruta)
            filas.append({"configuracion": nombre,
                          "t90": observables.t90(goles, config.PARTICULAS)})
    resumen = pd.DataFrame(filas)

    # t90 = -1 si no se llego al 90% antes de t_max: ese caso no tiene un
    # <t90> definido y hay que tratarlo aparte.
    if (resumen["t90"] < 0).any():
        sys.exit("Alguna realizacion no alcanzo el 90% de usadas antes de t_max.")
    return resumen.groupby("configuracion")["t90"].agg(["mean", "std", "count"])


def ajustar(nombre, semilla=SEMILLA_DCM):
    """Metodo de la Teorica 0 sobre [0, VENTANA_AJUSTE[nombre]] para una realizacion.

    Devuelve un dict con la serie completa, los tiempos ajustados, el barrido
    (pendientes, errores) y la pendiente optima c* = 4 D."""
    serie = pd.read_csv(ruta_serie_dcm(nombre, semilla))
    ventana = serie[serie["Time"] <= VENTANA_AJUSTE[nombre]]
    tiempos = ventana["Time"].to_numpy()
    pendientes, errores, pendiente = barrer_pendiente(tiempos, ventana["DCM"].to_numpy())
    return {"serie": serie, "tiempos": tiempos, "pendientes": pendientes,
            "errores": errores, "pendiente": pendiente}


def coeficiente_difusion(nombre, semilla=SEMILLA_DCM):
    return ajustar(nombre, semilla)["pendiente"] / (2.0 * DIMENSION)


def estadistica_difusion(nombre):
    """<D> y desvio sobre las REALIZACIONES, con la ventana de la configuracion."""
    faltantes = [s for s in semillas() if not ruta_serie_dcm(nombre, s).exists()]
    if faltantes:
        sys.exit(f"Faltan {len(faltantes)} series de DCM de {nombre}: correr sin --solo-graficos.")
    valores = np.array([coeficiente_difusion(nombre, semilla) for semilla in semillas()])
    return valores.mean(), valores.std(ddof=1)


def armar_tabla():
    t90 = estadistica_t90()
    filas = []
    for nombre, etiqueta in CONFIGURACIONES.items():
        d_medio, d_desvio = estadistica_difusion(nombre)
        filas.append({
            "configuracion": nombre,
            "etiqueta": etiqueta,
            "ventana_ajuste_s": VENTANA_AJUSTE[nombre],
            "D_m2_s": coeficiente_difusion(nombre),
            "D_medio_m2_s": d_medio,
            "D_desvio_m2_s": d_desvio,
            "t90_medio_s": t90.loc[nombre, "mean"],
            "t90_desvio_s": t90.loc[nombre, "std"],
            "realizaciones": int(t90.loc[nombre, "count"]),
        })
    return pd.DataFrame(filas)


def reportar(tabla):
    TABLA.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(TABLA, index=False)
    print(f"\nTabla guardada en {TABLA}\n")
    for fila in tabla.itertuples():
        d_medio = estilo.formatear_valor(fila.D_medio_m2_s, fila.D_desvio_m2_s, "m^2/s")
        t90 = estilo.formatear_valor(fila.t90_medio_s, fila.t90_desvio_s, "s")
        print(f"  {fila.etiqueta:18} ventana 0-{fila.ventana_ajuste_s} s   "
              f"D(s{SEMILLA_DCM}) = {fila.D_m2_s:#.2g} m^2/s   <D> = {d_medio}   <t90> = {t90}")

    # Con tan pocos puntos la correlacion es orientativa: se informa, no se testea.
    pearson = np.corrcoef(tabla["D_medio_m2_s"], tabla["t90_medio_s"])[0, 1]
    spearman = tabla["D_medio_m2_s"].rank().corr(tabla["t90_medio_s"].rank())
    print(f"\n  Correlacion <D> vs <t90>: Pearson r = {pearson:.2f}, "
          f"Spearman rho = {spearman:.2f} (n = {len(tabla)})")


def grilla_por_configuracion():
    """Figura 2x2 con un panel por configuracion (en el orden de CONFIGURACIONES)."""
    columnas = estilo.columnas_grilla(len(CONFIGURACIONES))
    filas = -(-len(CONFIGURACIONES) // columnas)  # division redondeando hacia arriba
    ancho, alto = config.TAM_FIG
    fig, ejes = plt.subplots(filas, columnas, figsize=(ancho * 1.4, alto * 2))
    return fig, ejes.flatten()


def graficar_dcm_por_configuracion():
    """DCM de cada configuracion con su recta DCM = 4 D t, un panel por config."""
    fig, ejes = grilla_por_configuracion()
    for ax, (nombre, etiqueta) in zip(ejes, CONFIGURACIONES.items()):
        ajuste = ajustar(nombre)
        serie = ajuste["serie"][ajuste["serie"]["Time"] <= TMAX_GRAFICO]
        dibujar_dcm(ax, serie, ajuste["tiempos"], ajuste["pendiente"], etiqueta=etiqueta)
        ax.legend(loc="lower right", fontsize=config.FUENTE * 0.8)
    estilo.guardar(fig, DIRECTORIO_ENTREGA / "dcm_por_configuracion.png", SEPARACION_GRILLA)


def graficar_error_por_configuracion():
    """Curva E(c) de cada configuracion con su minimo c*, un panel por config."""
    fig, ejes = grilla_por_configuracion()
    for ax, (nombre, etiqueta) in zip(ejes, CONFIGURACIONES.items()):
        ajuste = ajustar(nombre)
        dibujar_error(ax, ajuste["pendientes"], ajuste["errores"], ajuste["pendiente"])
        # Sin titulos (guia de la catedra): la configuracion va como entrada de leyenda.
        ax.plot([], [], linestyle="none", label=etiqueta)
        ax.legend(loc="upper center", fontsize=config.FUENTE * 0.8)
    unificar_potencias(ejes, "x", "Pendiente c", "m$^2$/s")
    unificar_potencias(ejes, "y", "E(c)", "m$^4$")
    estilo.guardar(fig, DIRECTORIO_ENTREGA / "error_ajuste_por_configuracion.png", SEPARACION_GRILLA)


def unificar_potencias(ejes, eje, nombre, unidad):
    """Misma potencia de 10 en todos los paneles, para que las unidades se lean
    igual en toda la figura. Cada panel conserva su propio rango. Se usa la
    potencia mas chica: la de los paneles con valores mas pequenos."""
    exponente = min(estilo.exponente_de_eje(ax, eje) for ax in ejes)
    for ax in ejes:
        estilo.etiquetar_eje_con_potencia(ax, eje, nombre, unidad, exponente)


def graficar_dcm_comparacion(tabla):
    """DCM de una realizacion (SEMILLA_DCM) de cada configuracion, con una linea
    vertical de su color donde termina el tramo lineal elegido para el ajuste."""
    fig, ax = estilo.nueva_figura()
    for fila in tabla.itertuples():
        serie = pd.read_csv(ruta_serie_dcm(fila.configuracion))
        serie = serie[serie["Time"] <= TMAX_GRAFICO]
        linea, = ax.plot(serie["Time"], serie["DCM"], label=fila.etiqueta)
        ax.axvline(fila.ventana_ajuste_s, linestyle="--", color=linea.get_color())
    ax.legend(loc="best", fontsize=config.FUENTE * 0.8)
    estilo.etiquetar_ejes(ax, "Tiempo (s)", "DCM (m$^2$)")
    estilo.guardar(fig, DIRECTORIO_ENTREGA / "dcm_comparacion.png")


def graficar_t90_vs_difusion(tabla):
    """<t90> vs <D>, ambos con su desvio sobre las realizaciones, un color y
    marcador por configuracion. Circulo y quad caen
    casi en el mismo D, asi que se identifican por leyenda y no con etiquetas
    de texto junto a cada punto. Los colores siguen el ciclo por defecto en el
    orden de CONFIGURACIONES, igual que en dcm_comparacion.png."""
    marcadores = ["o", "s", "^", "D"]
    fig, ax = estilo.nueva_figura()
    for indice, fila in enumerate(tabla.itertuples()):
        ax.errorbar(fila.D_medio_m2_s, fila.t90_medio_s,
                    xerr=fila.D_desvio_m2_s, yerr=fila.t90_desvio_s,
                    fmt=marcadores[indice % len(marcadores)], color=f"C{indice}",
                    markersize=10, capsize=6, label=fila.etiqueta)
    # D >= 0; margen para la barra de error de la mesa vacia
    ax.set_xlim(0.0, (tabla["D_medio_m2_s"] + tabla["D_desvio_m2_s"]).max() * 1.1)
    ax.legend(loc="upper left", fontsize=config.FUENTE * 0.8)
    estilo.etiquetar_ejes(ax, ylabel=r"$\langle t_{90} \rangle$ (s)")
    estilo.etiquetar_eje_con_potencia(ax, "x", r"$\langle D \rangle$", "m$^2$/s")
    estilo.guardar(fig, DIRECTORIO_ENTREGA / "t90_vs_difusion.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--forzar", action="store_true",
                        help="Re-corre las simulaciones aunque ya existan")
    parser.add_argument("--solo-graficos", action="store_true",
                        help="No simula: usa lo que ya hay en build/resultados/")
    args = parser.parse_args()

    if not args.solo_graficos:
        simular_t90(args.forzar)
        simular_dcm(args.forzar)

    tabla = armar_tabla()
    reportar(tabla)
    graficar_dcm_por_configuracion()
    graficar_error_por_configuracion()
    graficar_dcm_comparacion(tabla)
    graficar_t90_vs_difusion(tabla)
    return 0


if __name__ == "__main__":
    sys.exit(main())
