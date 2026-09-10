# SdS TP3 — Billar-Metegol (simulación dirigida por eventos)

Trabajo práctico 3 de Simulación de Sistemas (ITBA). Se simula un conjunto de
partículas que se mueven en línea recta entre colisiones elásticas dentro de una
mesa rectangular con dos arcos, y se busca la configuración de obstáculos que
minimiza `<t90>`, el tiempo hasta que el 90 % de las partículas convirtió un gol.

El enunciado está en [`docs/TP3_Enunciado.md`](docs/TP3_Enunciado.md).

## Estructura

El flujo va en una sola dirección: la simulación produce CSVs, los scripts de
Python los analizan y grafican, y el LaTeX consume las figuras.

```
include/  src/            Motor de simulación en C++17 (produce CSVs y nada más)
configs/                  Configuraciones de obstáculos candidatas
python/                   Orquestación: barridos, análisis y graficado
build/resultados/         CSVs de las corridas (gitignored)
entrega/<punto>/          Figuras finales versionadas
informe.tex               Informe
presentation.tex          Presentación
empaquetar.sh             Arma el .zip del entregable (c)
```

## Prerequisitos

| Herramienta | Para qué | Instalación (macOS) |
|-------------|----------|---------------------|
| CMake + compilador C++17 | Motor de simulación | `brew install cmake` |
| Python 3.9+ | Orquestación y graficado | `brew install python` |
| [tectonic](https://tectonic-typesetting.github.io/) | Compilar `informe.tex` y `presentation.tex` sin TeX Live completo | `brew install tectonic` |

`ffmpeg` **no** hace falta instalarlo aparte: matplotlib no codifica video por sí
mismo, sino que lanza el ejecutable de `ffmpeg` como subproceso, y el paquete
`imageio-ffmpeg` de `requirements.txt` trae ese binario adentro.
`plot/animacion.py` le apunta a ese, así que alcanza con el virtualenv.

## Compilar el motor

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

Queda el ejecutable en `build/simulador`.

## Correr una simulación

```bash
./build/simulador --config configs/embudo.txt --particles 100 --tmax 100 \
                  --seed 1000 --cada-eventos 200 --output build/resultados/prueba.csv
```

### Flags

| Flag | Default | Significado |
|------|---------|-------------|
| `--length VALOR` | `1.20` | Largo `L` de la mesa [m] |
| `--width VALOR` | `0.68` | Ancho `W` de la mesa [m] |
| `--goal-size VALOR` | `0.20` | Largo `d` del arco [m] |
| `--config ARCHIVO` | mesa vacía | Obstáculos, una línea `x y R` por obstáculo |
| `--particles N` | `100` | Cantidad de partículas `N` |
| `--radius VALOR` | `0.0175` | Radio `r` de las partículas [m] |
| `--mass VALOR` | `0.025` | Masa `m` de las partículas [kg] |
| `--v0 VALOR` | `1.0` | Módulo de la velocidad inicial [m/s] |
| `--tmax VALOR` | `100` | Tiempo máximo simulado [s] |
| `--seed VALOR` | `42` | Semilla del generador |
| `--stop-fraction VALOR` | `2.0` | Corta al alcanzar esa `F_u`; un valor mayor que 1 desactiva el corte |
| `--cada-eventos N` | `100` | Guarda el estado cada `N` eventos |
| `--output ARCHIVO` | `salida.csv` | Serie temporal compacta |
| `--trajectory ARCHIVO` | — | Trayectoria completa, solo para animar |
| `--placement VALOR` | `random` | Colocación de partículas: `random` o `hex` (hexagonal) |

### Salidas

Dos formatos, con propósitos distintos:

- **Serie temporal compacta** (`--output`): `Time,Goals,UsedFraction,MSD`. Es la
  que se usa para todo el análisis. Los observables se calculan dentro del motor
  durante la corrida.
- **Trayectoria completa** (`--trajectory`): `Time,ID,X,Y,VX,VY,State`, con
  `State` = 0 (fresca) o 1 (usada). Pesa mucho: solo para las animaciones. Los
  obstáculos no van acá — la animación los lee del mismo archivo `--config`.

Como la simulación es dirigida por eventos, la columna `Time` trae los instantes
reales de los eventos y el muestreo es **irregular**: los scripts de análisis no
asumen un `dt` constante.

Además, el motor imprime por stdout un resumen en formato `clave=valor` con
`tiempo_ejecucion_s`, `eventos`, `goles`, `t90` y `tiempo_final`. El tiempo de
ejecución lo mide el propio motor (wall-clock del bucle de eventos), para que no
incluya el arranque del proceso. `t90` es negativo si nunca se alcanzó `F_u = 0.9`.

## Configuraciones de obstáculos

Un archivo de texto por configuración candidata en `configs/`, con una línea
`x_k y_k R_k` por obstáculo, en metros. Se ignoran las líneas vacías y las que
empiezan con `#`. El motor valida las restricciones del punto 1.2 (obstáculos
íntegros dentro del dominio y sin solaparse) y aborta si no se cumplen.

## Orquestación y figuras

```bash
cd python
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./correr_todo.sh        # regenera TODAS las simulaciones
./generar_entrega.sh    # regenera TODAS las figuras de entrega/
```

Barridos sueltos:

```bash
.venv/bin/python run.py particulas --rango 50 500 25 --realizaciones 10
.venv/bin/python run.py particulas --rango 300 700 25 --realizaciones 10 --placement hex
.venv/bin/python run.py configs vacia embudo --realizaciones 5 --trayectoria
```

Por defecto `run.py` **no re-corre** un caso cuyo CSV ya existe; con `--forzar`
sí. Las realizaciones usan semillas deterministas (`SEMILLA_BASE + i`) y la
semilla va en el nombre del archivo, así que se ve de un vistazo qué falta.

Cada corrida exitosa deja un *sidecar* `<csv>.resumen` al lado del CSV con las
métricas del motor (tiempo de ejecución, eventos, goles, t90). El
`resumen.csv` se reconstruye fusionando esos sidecars, así que un barrido
cortado a la mitad no pierde los tiempos: alcanza con volver a correr el mismo
comando (los casos completos se saltean y el resumen se regenera igual).

Cada barrido deja un `resumen.csv` con una fila por realización, que es lo que
leen los scripts de graficado.

## Documentos

```bash
cd python
./render.sh                        # compila informe.tex con tectonic
./render.sh ../presentation.tex --watch --open
```

## Entregables

```bash
./empaquetar.sh G00CS              # SdS_TP3_2026Q2G00CS_Codigo.zip, < 100 KB
```

La configuración para la competencia es el archivo de `configs/` elegido,
renombrado a `SdS_TP3_2026Q2GXXCSS_Config.txt`.
