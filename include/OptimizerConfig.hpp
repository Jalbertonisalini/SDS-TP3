#pragma once

#include <stdexcept>
#include <string>

enum class SymmetryMode { None, Horizontal, FourQuadrant };

// Parametros de una corrida de busqueda genetica. Analogo a Config.hpp para
// el motor: todo con default razonable, nada que obligue a recompilar.
struct OptimizerConfig {
    // Geometria del dominio y particulas, iguales a Config.hpp: el motor que
    // arma internamente el Optimizer usa estos mismos valores.
    double length = 1.20;
    double width = 0.68;
    double goalSize = 0.20;
    int particleCount = 100;
    double particleRadius = 0.0175;
    double particleMass = 0.025;
    double initialSpeed = 1.0;
    double maxTime = 100.0;

    // Obstaculos a optimizar. minRadius > particleRadius: un obstaculo mas
    // chico que una particula no tiene sentido como deflector. maxRadius no
    // tiene techo fisico real (solo el dominio y el resto de los
    // obstaculos lo limitan) salvo en los genes de cuadrante/pareados bajo
    // simetria, que tienen un techo geometrico propio cerca de min(L,W)/4
    // sin importar este valor (ver GenomeCodec.hpp).
    int obstacleCount = 4;  // K
    double minRadius = 0.02;
    double maxRadius = 0.25;
    SymmetryMode symmetry = SymmetryMode::None;

    // Fitness (formula de la consigna)
    int targetGoals = 90;  // N_target
    double alpha = 1.0;    // penalizacion por gol faltante, >= 1.0

    // Factibilidad / restricciones de busqueda (no tocan el motor)
    double maxPackingDensity = 0.5;  // empaquetamiento aleatorio de discos
    double goalClearance = 0.0;      // 0 = desactivado

    // Algoritmo genetico
    int populationSize = 64;
    int generations = 100;
    int seedsPerGeneration = 5;  // S, Common Random Numbers
    int tournamentSize = 3;
    int elitism = 2;
    double crossoverAlpha = 0.3;  // alpha del BLX-alpha

    // Con genomas cortos (1 a 3 genes libres bajo simetria) el gateo doble
    // (individual x gen) dejaba la probabilidad efectiva de mutar un gen en
    // 0.3*0.2=6%: casi toda la poblacion eran interpolaciones BLX-alpha
    // puras. individualRate=1.0 saca ese gateo redundante; geneRate solo
    // queda como la unica perilla real.
    double individualMutationRate = 1.0;
    double geneMutationRate = 0.3;

    // El sigma decae geometricamente de *Start (generacion 0, explorar) a
    // *End (ultima generacion, explotar/afinar). Start-position es grande a
    // proposito: el codec ya evita que una mutacion produzca una config
    // invalida (clampea a positionBounds, que depende del radio real), asi
    // que un paso grande solo significa "probar el otro extremo del rango",
    // no arriesgar una excepcion.
    double mutationSigmaPositionStart = 0.06;  // m
    double mutationSigmaPositionEnd = 0.02;    // m
    double mutationSigmaRadiusStart = 0.03;    // m
    double mutationSigmaRadiusEnd = 0.008;     // m

    unsigned long seed = 42;  // RNG maestro: semillas por generacion + operadores geneticos

    // Verifica que obstacleCount sea representable exactamente por el modo de
    // simetria elegido. Tira std::runtime_error con un mensaje claro si no.
    void validate() const {
        if (obstacleCount <= 0) {
            throw std::runtime_error("--obstacles debe ser mayor que cero.");
        }
        if (minRadius <= particleRadius) {
            throw std::runtime_error(
                "--min-radius debe ser mayor que --radius (el radio de las particulas): un "
                "obstaculo mas chico que una particula no tiene sentido como deflector.");
        }
        if (maxRadius < minRadius) {
            throw std::runtime_error("--max-radius debe ser mayor o igual que --min-radius.");
        }
        if (symmetry == SymmetryMode::FourQuadrant && obstacleCount % 4 != 0 &&
            obstacleCount % 4 != 1) {
            throw std::runtime_error(
                "Con --symmetry quad, --obstacles debe ser multiplo de 4, o multiplo de 4 "
                "mas 1 (para el obstaculo central). Valor recibido: " +
                std::to_string(obstacleCount));
        }
        if (populationSize <= 0) {
            throw std::runtime_error("--population debe ser mayor que cero.");
        }
        if (generations <= 0) {
            throw std::runtime_error("--generations debe ser mayor que cero.");
        }
        if (seedsPerGeneration <= 0) {
            throw std::runtime_error("--seeds-per-gen debe ser mayor que cero.");
        }
        if (tournamentSize <= 0) {
            throw std::runtime_error("--tournament-size debe ser mayor que cero.");
        }
        if (elitism < 0 || elitism > populationSize) {
            throw std::runtime_error("--elitism debe estar entre 0 y --population.");
        }
    }
};
