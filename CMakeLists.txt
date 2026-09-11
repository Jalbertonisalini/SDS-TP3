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

add_executable(optimizador
    src/optimizer_main.cpp
    src/Optimizer.cpp
    src/GenomeCodec.cpp
    src/CandidateValidator.cpp
    src/CrossoverStrategy.cpp
    src/MutationStrategy.cpp
    src/PopulationLogger.cpp
    src/ObstacleConfig.cpp
    src/OutputWriter.cpp
    src/SimulationEngine.cpp
)

# OpenMP paraleliza la evaluacion de poblacion en `optimizador`. find_package
# lo resuelve directo en Linux (gcc). Apple clang no trae OpenMP nativo: si
# esta instalado via Homebrew ("brew install libomp") lo enganchamos a mano.
# Si no se encuentra de ninguna forma, optimizador compila igual y corre
# serial (ParallelFor.hpp cae a un for comun sin _OPENMP definido).
find_package(OpenMP QUIET)
if(OpenMP_CXX_FOUND)
    target_link_libraries(optimizador PRIVATE OpenMP::OpenMP_CXX)
elseif(APPLE)
    execute_process(
        COMMAND brew --prefix libomp
        OUTPUT_VARIABLE LIBOMP_PREFIX
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(LIBOMP_PREFIX AND EXISTS "${LIBOMP_PREFIX}/include/omp.h")
        message(STATUS "OpenMP: usando libomp de Homebrew en ${LIBOMP_PREFIX}")
        target_compile_options(optimizador PRIVATE -Xpreprocessor -fopenmp)
        target_include_directories(optimizador PRIVATE "${LIBOMP_PREFIX}/include")
        target_link_libraries(optimizador PRIVATE "${LIBOMP_PREFIX}/lib/libomp.dylib")
    else()
        message(STATUS "OpenMP no encontrado (ni nativo ni via 'brew install libomp'): "
                       "optimizador compila serial.")
    endif()
else()
    message(STATUS "OpenMP no encontrado: optimizador compila serial.")
endif()
