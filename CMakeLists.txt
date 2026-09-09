cmake_minimum_required(VERSION 3.15)
project(SimulacionSistemas_TP3 VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_EXTENSIONS False)

# Flags estrictos: el motor tiene que compilar limpio
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wpedantic -O3")

include_directories(include)

add_executable(simulador
    src/main.cpp
    src/ObstacleConfig.cpp
    src/OutputWriter.cpp
    src/SimulationEngine.cpp
)
