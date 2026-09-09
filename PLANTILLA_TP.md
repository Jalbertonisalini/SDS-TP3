# Plantilla de TP — Simulación de Sistemas (ITBA)

Guía reutilizable para arrancar el repositorio de **cualquier** TP de la
materia. El dominio cambia en cada trabajo (autómatas off-lattice, dinámica
molecular, peatones, tráfico, osciladores…), pero la forma del repo no: siempre
hay **generación de datos**, **orquestación/análisis** y **documentos LaTeX**
(informe + presentación).

La guía está en dos niveles:

- **Base** (§2–§4) — lo que se copia sin pensar el día 1. Es barato y siempre
  paga.
- **Cuando duela** (§5) — refactors que valen la pena *cuando aparece el
  síntoma*, no antes. Construirlos de entrada es andamiaje muerto.

Los ejemplos concretos vienen del TP2 (modelo de Vicsek) y están marcados como
tales: ilustran el patrón, no son parte de él.

---

## 1. Las tres capas

| Capa | Responsabilidad | Entrada | Salida |
|------|-----------------|---------|--------|
| **Simulación** | Producir datos crudos | Parámetros por CLI | CSVs |
| **Orquestación / análisis** | Correr barridos, analizar, graficar | CSVs | PNGs / MP4 |
| **Documentos** | Comunicar | PNGs / MP4 | `informe.pdf`, `presentation.pdf` |

Regla que sostiene todo: **el flujo va en una sola dirección**. La simulación
no grafica, los scripts de graficado no simulan, el LaTeX no genera figuras.

Corolario práctico: si un gráfico está mal, se arregla en la capa de análisis
sin volver a simular. Si el modelo está mal, se re-simula sin tocar el
graficado. Esto es lo que hace que el TP sobreviva a las correcciones de
último momento.

---

## 2. Base — estructura mínima

### 2.0 El enunciado manda; esta guía solo dice cómo responder

Esta plantilla **no repite lo que pide el TP**: el enunciado está en el repo y
se lee. Lo que aporta es la respuesta de arquitectura a exigencias que se
repiten trabajo a trabajo (barridos, realizaciones, figuras reproducibles).
Si algo de acá contradice al enunciado, gana el enunciado.

Primer paso del repo nuevo, antes de escribir código: dejar el enunciado en
`docs/` **y convertirlo a texto**, para poder grepearlo y citarlo sin abrir el
PDF.

En esta máquina no hay `pdftotext` ni `mutool`; sí PDFKit vía Swift:

```bash
cat > /tmp/pdftext.swift <<'EOF'
import Foundation
import PDFKit
let url = URL(fileURLWithPath: CommandLine.arguments[1])
if let doc = PDFDocument(url: url) {
    for i in 0..<doc.pageCount {
        print("=== PAGINA \(i+1) ===")
        print(doc.page(at: i)?.string ?? "")
    }
}
EOF
swift /tmp/pdftext.swift docs/TP<n>_Enunciado.pdf > docs/TP<n>_Enunciado.md
```

Del enunciado salen, en este orden: los **entregables** y su fecha (condiciona
todo el cronograma), los **parámetros fijos** (van a `config.py` y a los
defaults del motor), los **puntos a graficar** (uno por script), y las
**restricciones del entregable de código** (§5.7).

### 2.1 Árbol

```
sds-TP<n>/
├── README.md                  # Compilar, correr, graficar. Tabla de flags.
├── .gitignore
├── docs/TP<n>_Enunciado.md
│
├── <build system>             # CMakeLists.txt / pom.xml / pyproject.toml
├── include/  src/             # Motor de simulación (§3)
│
├── python/                    # Orquestación (§4)
│   ├── requirements.txt
│   ├── config.py              # Constantes y rutas: única fuente de verdad
│   ├── run.py                 # Barridos: invoca el binario N veces
│   ├── correr_todo.sh         # Regenera TODAS las simulaciones
│   ├── generar_entrega.sh     # Regenera TODAS las figuras del informe
│   ├── plot/<observable>_vs_<eje>.py
│   └── output/                # Figuras de trabajo (gitignored)
│
├── build/                     # Gitignored
│   ├── <binario>
│   └── resultados/            # CSVs, un archivo por corrida
│
├── entrega/<punto>/           # Figuras finales versionadas, por punto
│
├── informe.tex                # §6
└── presentation.tex           # §7
```

Adaptaciones válidas: si el motor es Java, `src/main/java/` + `pom.xml` en vez
de `include/`+`src/`+CMake; si es Python, un paquete `sim/` en vez de binario.
Lo que **no** cambia es `python/` (orquestación), `build/resultados/` (datos),
`entrega/` (figuras) y los dos `.tex`.

---

## 3. Base — capa de simulación

Aplica igual sea C++, Java o Python.

### 3.1 Contrato del ejecutable

- **Todo parámetro es un flag de CLI con default.** Nada de constantes que
  obliguen a recompilar. Mínimo: los parámetros del modelo, la duración
  (pasos o tiempo total), la semilla y el archivo de salida.
- **La semilla siempre es explícita** (`--seed 42`). Sin eso las corridas no
  son reproducibles y no se pueden defender los resultados.
- El programa **escribe CSV y nada más**: sin gráficos, sin dependencias
  extra, sin lógica de análisis.
- Un solo ejecutable parametrizado, no un ejecutable por punto del enunciado.
- **Los parámetros estructurados van en un archivo de texto**, pasado por flag
  (`--config <archivo>`), no como 30 flags sueltos: cuando el caso a simular
  es una lista de elementos (geometría, elementos fijos, condición inicial), el
  archivo es la unidad que se versiona, se compara y se entrega.
- El motor **reporta su propio tiempo de ejecución** (wall-clock de la corrida,
  sin el I/O de inicialización) en el CSV o por stderr. Si el enunciado pide
  "tiempo de ejecución vs N", medirlo desde Python incluye el arranque del
  proceso y ensucia el resultado.

Ejemplo (TP2):

```bash
./simulador --model standard --density 4 --eta 0.6 --iterations 20000 \
            --seed 42 --output resultados/mi_corrida.csv
```

### 3.2 Dos formatos de salida, no uno

| Formato | Cuándo | Esquema |
|---------|--------|---------|
| **Trayectoria completa** | Solo para animar; pesa mucho | `Time,ID,X,Y,<estado>` |
| **Serie temporal compacta** | Para todo el análisis | `Time,<Obs1>,<Obs2>` |

Los observables escalares (polarización, energía, caudal, densidad media, lo
que pida el TP) se calculan **dentro del motor durante la corrida**, no en
post-proceso. Si no, cada gráfico obliga a releer gigabytes de trayectorias.
Es la decisión que más tiempo ahorra en todo el TP.

Un CSV compacto = una corrida = un punto del barrido.

**Si la simulación es dirigida por eventos**, el paso de tiempo no es
uniforme: la columna `Time` trae los instantes reales de los eventos. Guardar
el estado **cada K eventos** (flag `--cada-eventos`), no en cada uno, o el
disco explota. Las series temporales quedan con muestreo irregular: los
scripts de análisis no pueden asumir `dt` constante (para promediar en el
tiempo hay que pesar por intervalo, o interpolar a una grilla uniforme
primero).

### 3.3 Organización del código

La única regla del día 1: **separar el modelo del I/O**. El bucle de
simulación no sabe de archivos; escribir el CSV es otra pieza.

`main` solo orquesta: parsea argumentos, arma la config, corre, escribe. Sin
lógica de modelo adentro.

Flags de compilación estrictos (`-Wall -Wextra -Wpedantic -O3` en C++).

Las demás piezas (estructura de aceleración, integrador intercambiable) salen
solas cuando el TP las pide — ver §5.1.

---

## 4. Base — orquestación y análisis (Python)

### 4.1 `config.py` — única fuente de verdad

Constantes del modelo y **todas** las rutas, derivadas de `__file__`:

```python
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BUILD = RAIZ / "build"
EJECUTABLE = BUILD / "<binario>"
RESULTADOS = BUILD / "resultados"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
```

Son 10 líneas y evitan que cada script arme rutas a mano o asuma desde qué
directorio se lo invoca.

### 4.2 `run.py` — el barrido

| Opción | Significado |
|--------|-------------|
| `valores...` | Corre solo esos valores del parámetro barrido |
| `--rango INI FIN PASO` | Barrido regular |
| `--forzar` | Re-corre aunque el CSV ya exista |

**Por defecto no re-corre** si el CSV existe: los barridos son largos y se
reanudan a mano muchas veces.

Los resultados van planos en `build/resultados/`, un CSV por corrida, con el
valor barrido en el nombre (`ruido_eta0.60.csv`). Jerarquía solo cuando
aparece una segunda dimensión — §5.2.

### 4.3 Realizaciones múltiples

Cuando el enunciado pide **M realizaciones por caso** (típico: "al menos 5/10
realizaciones, reportar promedio y desvío"), la realización es una dimensión
más del barrido, no un detalle de implementación:

- `run.py` acepta `--realizaciones M` y corre el mismo caso con **M semillas
  distintas y deterministas** (`SEED_BASE + i`, no `random()`): la corrida se
  tiene que poder repetir idéntica al defenderla.
- La semilla va **en el nombre del archivo**: `<caso>_s<seed>.csv`. Así se ve
  de un vistazo qué realizaciones ya existen y `--forzar` sigue siendo
  innecesario.
- El desvío que se grafica es **entre realizaciones**, no dentro de una serie
  temporal. Son cosas distintas y se mezclan fácil: un observable de tipo
  "instante en que se cruza un umbral" da **un escalar por realización**, y la
  barra de error sale de esos M escalares, no de la dispersión de la curva.
- Los observables por realización conviene resumirlos en un CSV agregado
  (`resumen.csv`, una fila por realización) en vez de releer las M series
  cada vez que se grafica.

### 4.4 Scripts de graficado

- **Un script por punto del enunciado**, nombrado por lo que grafica
  (`<observable>_vs_<eje>.py`), no por la letra del punto.
- Interfaz común: `--salida ARCHIVO.png` y lo que necesite para elegir los
  datos.
- Reglas de estilo de las figuras: §8.

### 4.5 Los dos scripts que salvan el TP

1. `correr_todo.sh` — todas las simulaciones.
2. `generar_entrega.sh` — todas las figuras, con `--salida` apuntando a
   `entrega/<punto>/`.

**Ninguna figura del informe se genera a mano.** Si está en el `.tex`, sale de
una línea de `generar_entrega.sh`. Es la única forma de sobrevivir a "che,
corramos todo con 30.000 pasos en vez de 20.000" tres días antes de entregar.

Todos los `.sh` arrancan igual:

```bash
#!/bin/bash
set -e
cd "$(dirname "$0")"

PY="./.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "Falta el virtualenv: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
```

### 4.6 `.gitignore`

Ignorar: `build/`, artefactos del build system, binarios y objetos, `.venv/`,
`__pycache__/`, `python/output/`, `.DS_Store`, y los artefactos LaTeX
(`*.aux *.log *.nav *.out *.snm *.toc *.vrb *.fls *.fdb_latexmk *.synctex.gz
*.bbl *.blg`).

Versionar: código, `entrega/` (figuras y animaciones finales), `docs/`, `.tex`,
`.md` y los PDFs compilados.

> Cuidado con dos patrones heredables que muerden: `Makefile` y `*.log`
> ignorados globalmente. Si el TP nuevo usa un `Makefile` en la raíz, hay que
> hacerle excepción.

---

## 5. Cuando duela — refactors con disparador

Nada de esta sección se construye el día 1. Cada uno tiene un síntoma que lo
dispara; hasta que el síntoma aparece, es complejidad sin usuario.

### 5.1 Extraer la estructura de aceleración

> **Síntoma:** el bucle de vecinos/eventos domina el tiempo de corrida, o el
> enunciado pide analizar el método (complejidad, comparación contra fuerza
> bruta).

Sacar el método a su propia clase con interfaz chica (`vecinos(i)`,
`siguiente_evento()`), para poder medirlo y compararlo aislado.

Ejemplo (TP2): `CellIndexMethod` quedó separado y eso permitió el benchmark
CIM vs fuerza bruta del punto g) sin tocar el motor.

### 5.2 Jerarquía en `build/resultados/`

> **Síntoma:** aparece una **segunda dimensión** además del parámetro barrido
> (dos modelos, varias densidades, dos condiciones iniciales).

Pasar de plano a `build/resultados/<variante>/<parametro><valor>/`.

Ejemplo (TP2): `voter/rho8/`, `standard/rho0.318/`.

Con jerarquía, la variante y el valor se **deducen de la ruta** al graficar; no
se pasan como flag redundante. Los scripts de graficado toman `--directorio`
repetible: una curva por aparición.

Con una sola dimensión, la carpeta plana es más legible y más fácil de
inspeccionar a mano. No adelantarse.

### 5.3 JSON de parámetros de análisis

> **Síntoma:** hay criterios que se eligen **a ojo** (dónde arranca el
> estacionario, qué casos son representativos, qué ventana promediar) y ya
> están escritos como literales en más de un script.

Moverlos a un JSON, indexado por las dimensiones que existan:

```json
{
  "<variante>": {
    "representativos": [<valores>],
    "<parametro>": { "<valor>": <criterio> }
  }
}
```

Ejemplo (TP2): `tinicios.json` guarda el `t_inicio` del estacionario por
modelo + densidad + η. Cambiar de modelo o densidad no requiere tocar código.

El punto no es el JSON: es que esos números **se van a ajustar muchas veces**
mirando gráficos, y no tienen que estar desparramados por el código.

### 5.4 `config_util.py`

> **Síntoma:** el **tercer** script duplica el mismo parseo de nombres de
> directorio, la misma etiqueta de leyenda o la misma lectura del JSON.

Recién ahí extraer el helper compartido. Antes de la tercera repetición, la
duplicación es más barata que la abstracción equivocada.

### 5.5 Documentación extra

> **Síntoma:** el `README` ya no entra en una pantalla, o alguien del grupo
> pregunta "¿con qué parámetros salió esta figura?".

Recién ahí partirlo:

- `python/EXPERIMENTOS.md` — comandos exactos por punto, para reproducir uno
  solo sin correr todo.
- `entrega/PARAMETROS.md` — qué parámetros produjeron cada figura.

Tres documentos que se solapan se desincronizan solos. Mientras el README
alcance, uno solo.

### 5.6 Barrido sobre configuraciones, no sobre un escalar

> **Síntoma:** lo que se busca no es el valor óptimo de un parámetro sino una
> **configuración entera** (geometría, disposición de elementos, condición
> inicial), y hay que justificar cómo se la encontró.

Entonces el "punto del barrido" deja de ser un número y pasa a ser un archivo:

- Un directorio `configs/` versionado, un archivo de texto por configuración
  candidata, con nombre descriptivo de la idea que prueba.
- `run.py` toma `--config` (repetible) y corre M realizaciones de cada una.
- El resumen agregado lleva una fila por (configuración, realización); el
  gráfico compara configuraciones contra la línea de base (el caso vacío).
- Si se automatiza la búsqueda (aleatoria, recocido simulado, genético), el
  buscador es **otro script** de la capa de orquestación que genera configs y
  llama al mismo motor. El motor no sabe que lo están optimizando.

Lo que hace falta guardar para defender el resultado: la config ganadora, las
semillas usadas y el resumen por realización. Con eso se reproduce el número.

### 5.7 Empaquetado del entregable

> **Síntoma:** el enunciado pide un `.zip` con **solo el motor de simulación**,
> con límite de tamaño y sin postprocesamiento, outputs ni figuras.

Un script `empaquetar.sh` que arma el zip desde una lista explícita de rutas
(el código del motor y su build system, nada más). Nunca `zip -r .` con
exclusiones: las exclusiones se olvidan y termina viajando `build/` entero.

La separación en capas de §1 es justamente lo que hace que este script sea de
cinco líneas: el motor ya está aislado de la orquestación.

---

## 6. Informe (`informe.tex`)

### 6.1 Preámbulo base — copiar tal cual

```latex
\documentclass[11pt,a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\decimalpoint                       % 3.5, no 3,5
\usepackage[margin=2.5cm]{geometry}
\usepackage{mathptmx}               % Times New Roman en texto y matemática
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{caption}
\usepackage{placeins}               % \FloatBarrier
\usepackage{float}                  % opción [H]
\usepackage{tikz}
\captionsetup{labelfont=bf, labelsep=colon}

% La cátedra numera tablas y figuras en una única secuencia "Figura N"
\AtBeginDocument{\renewcommand{\tablename}{\figurename}}
\makeatletter
\let\c@table\c@figure
\makeatother

\usepackage{hyperref}
\hypersetup{colorlinks=true, linkcolor=black, citecolor=black, urlcolor=blue}
```

Si hay TikZ con flechas (`->`), después de `\begin{document}`:

```latex
\shorthandoff{<>}   % babel[spanish] hace activos < y >, y rompe TikZ
```

### 6.2 Carátula

`titlepage` centrada, en este orden: ITBA, código y nombre de la materia,
título (`\Huge\bfseries`), subtítulo (`\LARGE`), número de TP, tabla de
integrantes con legajo, y al pie grupo, comisión, cuatrimestre y fecha.
Después: `\tableofcontents` + `\newpage`.

### 6.3 Esqueleto de secciones

Sirve para cualquier TP de la materia:

1. **Introducción** — qué se estudia y por qué; párrafo final que enumera las
   secciones con `\ref` a cada una.
2. **Modelo** — las ecuaciones y las reglas. Sin implementación.
3. **Implementación** — arquitectura del código (diagrama TikZ), estructuras de
   datos, complejidad del método.
4. **Simulaciones** — parámetros fijos, barridos, tabla de casos,
   visualización/animaciones.
5. **Resultados** — una subsección por observable, en el orden del enunciado.
6. **Desempeño** — si el enunciado pide análisis del método.
7. **Conclusiones** — `itemize`, una afirmación por ítem.
8. `thebibliography`.

`\FloatBarrier` antes de cada `\section` para que las figuras no se cuelen a la
sección siguiente.

### 6.4 Figuras

```latex
\begin{figure}[H]
  \centering
  \includegraphics[width=0.8\textwidth]{entrega/b/<figura>.png}
  \caption{<Qué se grafica>, <variante del modelo>, <parámetros fijos con
    unidades>, para <valores del parámetro libre>. <Qué significan los
    elementos gráficos: líneas punteadas, barras de error>. <N> pasos.}
  \label{fig:b-<variante>-<caso>}
\end{figure}
```

- Siempre `[H]` (paquete `float`): la figura queda exactamente donde se escribe.
- Ancho relativo: `0.8\textwidth` para curvas temporales, `0.75\textwidth` para
  barridos.
- **Epígrafe autocontenido**: qué se grafica, con qué variante, qué parámetros
  y qué significan los elementos gráficos. Nunca "Figura del punto b".
- El epígrafe va **debajo**, tanto en figuras como en tablas (comparten
  contador).
- Labels con prefijo del punto: `fig:b-standard-rho2`, `fig:c-voter-3dens`.
- Toda figura se referencia en el texto **antes** de aparecer, con
  `Fig.~\ref{...}` (tilde: evita el salto de línea).
- El texto que precede describe **lo que se ve**: valores concretos,
  tendencias, comparación entre curvas. No repite el epígrafe.

### 6.5 Tablas

```latex
\begin{table}[H]
  \centering
  \begin{tabular}{@{}lccccc@{}}
    \toprule
    <Parámetro> [<unidad>] & ... \\
    \midrule
    <Derivado> & ... \\
    \bottomrule
  \end{tabular}
  \caption{<Qué muestra la tabla>.}
  \label{fig:<nombre>}
\end{table}
```

`booktabs` (`\toprule`/`\midrule`/`\bottomrule`), nunca `\hline` ni líneas
verticales. `@{}` al principio y al final de las columnas. El label lleva
prefijo `fig:` porque comparte contador con las figuras.

### 6.6 Ecuaciones

- `equation` + `\label{eq:nombre}` para toda ecuación referenciada; el resto
  inline.
- Referenciar como `Ec.~\eqref{eq:nombre}` (con paréntesis).
- Introducirlas con "…, según la Ec.~\eqref{eq:x}:" y cerrar con la puntuación
  dentro del display.
- Macros para notación repetida en el preámbulo:
  `\newcommand{\rmed}{\mathbf{r}}`.
- Unidades siempre, en texto y en ejes: `$\rho = 2$ m$^{-2}$`.
- Miles con espacio fino: `$30\,000$`.

### 6.7 Bibliografía

`thebibliography` manual (sin BibTeX), formato APS/IEEE, claves `apellido+año`:

```latex
\bibitem{vicsek1995}
T. Vicsek, A. Czirók, E. Ben-Jacob, I. Cohen, O. Shochet,
``Novel type of phase transition in a system of self-driven particles,''
\emph{Physical Review Letters}, vol.\ 75, no.\ 6, pp.\ 1226--1229 (1995).
```

Comillas LaTeX (```` ``…'' ````), `\emph` para la revista, `\ ` después de las
abreviaturas (`vol.\ `, `no.\ `, `pp.\ `).

### 6.8 Redacción

Español impersonal ("se implementa", "se observa"), en presente. Comentario en
el `.tex` cada vez que se usa un truco no evidente (`\shorthandoff`,
unificación de contadores, `\FloatBarrier`). Sin tildes en los comentarios del
código; sí en el texto.

---

## 7. Presentación (`presentation.tex`)

Beamer 16:9, **una idea por diapositiva**, mínimo texto, máximo gráfico.

### 7.1 Preámbulo base

```latex
\documentclass[aspectratio=169]{beamer}

% Toggle version impresa (PDF) vs presentacion en vivo con animaciones
\newif\ifpptprint
\pptprinttrue

\usecolortheme{dolphin}
\setbeamertemplate{navigation symbols}{}

% Footline: solo el numero de diapositiva (guia 1.2)
\setbeamertemplate{footline}{%
  \hbox to\paperwidth{\hfill
    \small\color{black!65}\insertframenumber\,/\,\inserttotalframenumber
    \hskip1.4em}%
  \vskip6pt
}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot]{babel}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tikz}
\usepackage{hyperref}
```

### 7.2 Macros que conviene arrastrar a todos los TPs

| Macro | Para qué |
|-------|----------|
| `\seccion{Título}` | Diapositiva separadora, solo el título centrado |
| `\libre{...}` | Parámetro libre a la derecha del título de la diapositiva |
| `\figuno{ruta}` | Una figura al máximo tamaño posible |
| `\figdos{izq}{tit}{der}{tit}` | Dos figuras lado a lado con su rótulo |
| `\animdos{...}` | Dos animaciones con el link explícito debajo |
| `\vv{x}` / `\uu{m}` | Vectores en negrita / unidades en romano |

Detalle no obvio de `\libre`: el título de beamer va en `\raggedright`
(`\rightskip = 0pt plus 1fil`), así que un `\hfill` normal queda a media asta.
Hay que usar `\hskip 0pt plus 1filll`.

### 7.3 Reglas de contenido

- **Las condiciones de simulación se enuncian una sola vez**, en una
  diapositiva "Parámetros del estudio". En cada diapositiva de figura solo se
  repite el **parámetro libre**, a la derecha del título (`\libre`).
- Headline con indicador de progreso: puntos agrupados por sección, el actual
  resaltado. Ojo: los rangos de frames están hardcodeados y hay que
  actualizarlos si se agregan o quitan diapositivas.
- Diapositiva de ecuaciones: `\Large`, títulos en negrita sobre cada bloque,
  displays sin numerar (`\[ \]`), a dos columnas si son cuatro.
- `itemize` con `\setlength{\itemsep}{1em}`, máximo 3-4 ítems, una línea cada
  uno.
- Animaciones: link explícito y visible debajo del video, para que funcione
  también en la versión impresa.
- Mismo orden narrativo que el informe: Intro → Implementación → Simulaciones →
  Resultados → Conclusiones.

---

## 8. Estilo de las figuras (matplotlib)

Alineado con la guía de presentaciones de la cátedra. Vale para informe y para
presentación: se genera **una sola vez** y se usa en los dos.

```python
import matplotlib
matplotlib.use("Agg")          # sin display: scripts batch
import matplotlib.pyplot as plt

FUENTE = 20                    # mínimo exigido por la cátedra
TAM_FIG = (13, 6)

fig, ax = plt.subplots(figsize=TAM_FIG)
ax.errorbar(x, y, yerr=err, marker="o", capsize=4, label="<serie>")
ax.set_xlabel("<Magnitud> (<unidad>)", fontsize=FUENTE)   # en palabras
ax.set_ylabel("<Magnitud> (<unidad>)", fontsize=FUENTE)
ax.tick_params(labelsize=FUENTE)
ax.legend(loc="best", fontsize=FUENTE)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(archivo_salida, dpi=150)
```

- **Sin título dentro de la figura** — el contexto lo da el epígrafe del `.tex`.
- Ejes rotulados **en palabras** ("Ruido", "Polarización", "Tiempo"), no con el
  símbolo, y con unidades.
- Fuente ≥ 20 en labels, ticks y leyenda.
- Toda magnitud promediada va con **barras de error** y marcador visible;
  nunca línea pelada.
- Las barras de error de magnitudes acotadas se recortan al dominio físico
  (una fracción no puede pasar de 1) usando errores asimétricos.
- `dpi=150` y `tight_layout()` siempre.
- Nombre de archivo: `<punto>_<variante>_<caso>.png`, guardado en
  `entrega/<punto>/`.

---

## 9. Compilación del LaTeX

`render.sh` + `render_latex.py` compilan con **tectonic** (no hace falta TeX
Live completo) y soportan `--watch`: recompilan al guardar el `.tex` o
cualquier figura incluida (se parsean los `\includegraphics` para armar la
lista de archivos observados).

```bash
cd python
./render.sh                        # una compilación del default
./render.sh --watch                # recompila al guardar
./render.sh ../informe.tex --watch --open
```

Es infraestructura copiable tal cual entre TPs: no hace falta rehacerla.

---

## 10. Checklist

### Día 1 (base)

- [ ] Un solo ejecutable parametrizado, sin constantes recompilables.
- [ ] `--seed` explícita.
- [ ] Dos formatos de CSV: trayectoria completa y serie compacta.
- [ ] Observables calculados dentro del motor, no en post-proceso.
- [ ] Modelo separado del I/O; `main` solo orquesta.
- [ ] `python/config.py` con rutas derivadas de `__file__`.
- [ ] `run.py` con `--rango` y `--forzar`; no re-corre por defecto.
- [ ] Realizaciones con semillas deterministas y la semilla en el nombre del CSV.
- [ ] Un script de graficado por punto, con `--salida`.
- [ ] `correr_todo.sh` y `generar_entrega.sh` regeneran todo desde cero.
- [ ] `entrega/<punto>/` con las figuras finales versionadas.
- [ ] `README.md` con compilación, ejecución y tabla de flags.
- [ ] `.gitignore` cubre `build/`, `.venv/`, `python/output/` y artefactos TeX.

### Cuando aparezca el síntoma

- [ ] Método de búsqueda/eventos aislado → el enunciado pide medirlo (§5.1).
- [ ] Jerarquía en `resultados/` → segunda dimensión de barrido (§5.2).
- [ ] JSON de análisis → criterios elegidos a ojo, repetidos (§5.3).
- [ ] `config_util.py` → tercera repetición del mismo helper (§5.4).
- [ ] `configs/` + `run.py --config` → se busca una configuración, no un escalar (§5.6).
- [ ] `empaquetar.sh` → el enunciado pide un zip con solo el motor (§5.7).
- [ ] `EXPERIMENTOS.md` / `PARAMETROS.md` → el README ya no alcanza (§5.5).

### Documentos

- [ ] `informe.tex` con el preámbulo base y contadores tabla/figura unificados.
- [ ] `\FloatBarrier` antes de cada sección; figuras `[H]` con epígrafe autocontenido.
- [ ] `presentation.tex` 16:9, condiciones una sola vez, parámetro libre por diapositiva.
- [ ] Figuras sin título, ejes en palabras, fuente ≥ 20, barras de error.
- [ ] `render.sh` funcionando con tectonic.
