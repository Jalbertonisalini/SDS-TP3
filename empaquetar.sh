#!/bin/bash
# Arma el .zip del entregable (c): solo el motor de simulacion, nada mas.
# El enunciado exige que pese menos de 100 KB y que no lleve postprocesamiento,
# outputs, figuras ni documentacion extra.
set -e
cd "$(dirname "$0")"

GRUPO="${1:?Uso: ./empaquetar.sh <GXXCSS>}"
DESTINO="SdS_TP3_2026Q2${GRUPO}_Codigo.zip"

rm -f "$DESTINO"
# Lista explicita de rutas: nunca "zip -r ." con exclusiones, que se olvidan.
zip -q "$DESTINO" \
  CMakeLists.txt \
  include/Config.hpp \
  include/Event.hpp \
  include/Obstacle.hpp \
  include/ObstacleConfig.hpp \
  include/OutputWriter.hpp \
  include/Particle.hpp \
  include/SimulationEngine.hpp \
  include/Vec2.hpp \
  src/main.cpp \
  src/ObstacleConfig.cpp \
  src/OutputWriter.cpp \
  src/SimulationEngine.cpp

echo "$DESTINO ($(du -h "$DESTINO" | cut -f1))"
unzip -l "$DESTINO"
