"""Punto 1.2 (circulo naive): <t90> con barra de error en funcion del radio
de un unico obstaculo circular centrado en la mesa.

    python plot/t90_vs_radio.py --salida ../entrega/1.2/circulo_t90_vs_radio.png

Lee el mismo resumen agregado que arma run.barrido_configs (build/resultados/
configs/resumen.csv), filtra las configuraciones "circulo_rX.XX" mas "vacia"
(que se toma como el punto en radio=0) y usa el radio como eje x numerico en
vez de un eje categorico. Las configuraciones que no llegan a F_u=0.9 dentro
de t_max se marcan aparte: el motor devuelve t90 negativo en ese caso.
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config
import estilo

PATRON_RADIO = re.compile(r"^circulo_r(\d+\.\d+)$")


def radio_de_configuracion(nombre):
    """radio en metros, o None si `nombre` no es parte de este barrido."""
    if nombre == "vacia":
        return 0.0
    m = PATRON_RADIO.match(nombre)
    return float(m.group(1)) if m else None


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resumen", type=Path,
                        default=config.RESULTADOS / "configs" / "resumen.csv",
                        help="CSV agregado del barrido sobre configuraciones")
    parser.add_argument("--salida", type=Path, required=True, help="Archivo PNG de salida")
    args = parser.parse_args()

    if not args.resumen.exists():
        print(f"Falta el resumen del barrido: {args.resumen}", file=sys.stderr)
        return 1

    datos = pd.read_csv(args.resumen)
    datos["radio"] = datos["configuracion"].apply(radio_de_configuracion)
    datos = datos[datos["radio"].notna()]
    if datos.empty:
        print("No hay configuraciones 'circulo_rX.XX' (ni 'vacia') en el resumen",
              file=sys.stderr)
        return 1

    incompletas = sorted(datos.loc[datos["t90"] < 0, "configuracion"].unique())
    if incompletas:
        print("No alcanzan F_u = 0.9 dentro de t_max: " + ", ".join(incompletas), file=sys.stderr)

    validas = datos[datos["t90"] >= 0]
    agrupado = validas.groupby("radio")["t90"].agg(["mean", "std", "count"]).reset_index()
    agrupado = agrupado.sort_values("radio")

    fig, ax = estilo.nueva_figura()
    ax.errorbar(agrupado["radio"], agrupado["mean"], yerr=agrupado["std"].fillna(0.0),
                marker="o", capsize=4, linestyle="-")
    estilo.etiquetar_ejes(ax, "Radio del obstaculo (m)", "t90 (s)")
    estilo.guardar(fig, args.salida)

    # Precision completa aca (es log de corrida, no la tabla/figura final):
    # el recorte a cifras significativas del error es para lo que se muestra
    # en la entrega, no para lo que queda guardado/logueado.
    print(agrupado.to_string(index=False))
    for _, fila in agrupado.iterrows():
        print(f"r = {fila['radio']:.2f} m: t90 = {fila['mean']:.4f} +/- {fila['std']:.4f} s "
              f"(n={int(fila['count'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
