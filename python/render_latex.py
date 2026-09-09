#!/usr/bin/env python3
"""Compila la presentacion LaTeX a PDF con tectonic.

Con --watch queda escuchando cambios en el .tex (y en las figuras que
incluye) y recompila cada vez que se guarda alguno, para ver el PDF en vivo.

Uso:
    .venv/bin/python render_latex.py            # una compilacion
    .venv/bin/python render_latex.py --watch    # recompila al guardar
    .venv/bin/python render_latex.py --watch --open   # ademas abre el PDF
"""

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TEX_POR_DEFECTO = RAIZ / "presentation.tex"
INTERVALO_SONDEO = 0.5  # segundos entre chequeos de mtime

# \includegraphics[...]{ruta}
PATRON_INCLUDE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}")


def archivos_observados(tex):
    """El .tex mas las figuras que incluye (las rutas son relativas a RAIZ)."""
    archivos = [tex]
    try:
        fuente = tex.read_text(encoding="utf-8")
    except OSError:
        return archivos
    for ruta in PATRON_INCLUDE.findall(fuente):
        candidato = (RAIZ / ruta.strip()).resolve()
        if candidato.exists():
            archivos.append(candidato)
    return archivos


def huella(archivos):
    """Instantanea de mtimes; sirve para detectar cualquier cambio."""
    return tuple((f, f.stat().st_mtime_ns if f.exists() else -1) for f in archivos)


def compilar(tex, una_pasada=False):
    """Compila el .tex. Con `una_pasada` corre una sola vez el motor: es ~40%
    mas rapido, pero el total de diapositivas del pie sale del .aux de la
    corrida anterior, asi que queda desactualizado el build en que agregas o
    sacas una diapositiva. Se usa solo en --watch; el build final va completo."""
    orden = ["tectonic", "-X", "compile", str(tex),
             "--outdir", str(tex.parent), "--keep-logs"]
    if una_pasada:
        orden += ["-r", "0"]

    inicio = time.monotonic()
    resultado = subprocess.run(orden, capture_output=True, text=True)
    segundos = time.monotonic() - inicio

    if resultado.returncode != 0:
        # Solo las lineas utiles del error, no el log entero.
        for linea in resultado.stderr.splitlines():
            if linea.startswith(("error", "note: error", "Error")) or "!" in linea:
                print(f"  {linea}")
        print(f"[falló] {tex.name} en {segundos:.1f} s")
        return False

    pdf = tex.with_suffix(".pdf")
    print(f"[ok] {pdf.name} ({pdf.stat().st_size / 1e6:.1f} MB) en {segundos:.1f} s")
    avisar_de_advertencias(tex.with_suffix(".log"))
    return True


def avisar_de_advertencias(log):
    """Lista las cajas desbordadas: son las que rompen el layout de una slide."""
    if not log.exists():
        return
    desbordes = [
        linea.strip()
        for linea in log.read_text(encoding="utf-8", errors="replace").splitlines()
        if linea.startswith(("Overfull \\hbox", "Overfull \\vbox"))
    ]
    for linea in desbordes:
        print(f"  aviso: {linea}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tex", nargs="?", default=str(TEX_POR_DEFECTO),
                        help="Archivo .tex a compilar")
    parser.add_argument("--watch", action="store_true",
                        help="Recompilar cada vez que cambie el .tex o una figura")
    parser.add_argument("--open", action="store_true",
                        help="Abrir el PDF despues de la primera compilacion")
    args = parser.parse_args()

    if shutil.which("tectonic") is None:
        sys.exit("Falta tectonic. Instalar con: brew install tectonic")

    tex = Path(args.tex).resolve()
    if not tex.exists():
        sys.exit(f"No existe {tex}")

    ok = compilar(tex)

    if args.open and ok:
        subprocess.run(["open", str(tex.with_suffix(".pdf"))])

    if not args.watch:
        return 0 if ok else 1

    observados = archivos_observados(tex)
    print(f"Observando {len(observados)} archivos. Ctrl+C para salir.")
    print("(los rebuilds usan una sola pasada; corré sin --watch para el PDF final)")
    anterior = huella(observados)
    try:
        while True:
            time.sleep(INTERVALO_SONDEO)
            # La lista se recalcula: el .tex puede haber agregado figuras nuevas.
            observados = archivos_observados(tex)
            actual = huella(observados)
            if actual != anterior:
                anterior = actual
                print(f"\n--- cambio detectado {time.strftime('%H:%M:%S')} ---")
                compilar(tex, una_pasada=True)
    except KeyboardInterrupt:
        print("\nListo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
