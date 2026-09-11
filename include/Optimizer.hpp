#pragma once

#include <memory>
#include <random>
#include <vector>

#include "CrossoverStrategy.hpp"
#include "FitnessFunction.hpp"
#include "GenerationLogger.hpp"
#include "GenomeCodec.hpp"
#include "Individual.hpp"
#include "MutationStrategy.hpp"
#include "OptimizerConfig.hpp"
#include "PopulationLogger.hpp"
#include "SelectionStrategy.hpp"

// Orquestador del algoritmo genetico. No sabe nada de fisica: arma un
// Config del motor por evaluacion (mismo Config.hpp que usa `simulador`) y
// llama a SimulationEngine::runSilent(). Todas las piezas (codec de
// simetria, fitness, seleccion, cruza, mutacion) se inyectan por interfaz
// para poder benchmarkear variantes sin tocar esta clase.
class Optimizer {
public:
    Optimizer(OptimizerConfig config, std::unique_ptr<GenomeCodec> codec,
             std::unique_ptr<FitnessFunction> fitness,
             std::unique_ptr<SelectionStrategy> selection,
             std::unique_ptr<CrossoverStrategy> crossover,
             std::unique_ptr<MutationStrategy> mutation);

    // Corre config_.generations generaciones y devuelve el mejor individuo
    // visto en toda la corrida (no solo el de la ultima generacion). Si
    // logger no es nullptr, se loguea una fila de convergencia por
    // generacion. Si populationLogger no es nullptr, se vuelca la poblacion
    // completa (obstaculos + fitness) de cada generacion -- pensado para una
    // corrida chica y puntual que se quiere animar, no para el barrido
    // grande.
    Individual run(GenerationLogger* logger = nullptr, PopulationLogger* populationLogger = nullptr);

    const GenomeCodec& codec() const { return *codec_; }

private:
    Individual randomIndividual(std::mt19937_64& rng) const;
    double evaluateIndividual(const std::vector<ObstacleGene>& genome,
                              const std::vector<unsigned long>& seeds) const;

    OptimizerConfig config_;
    std::unique_ptr<GenomeCodec> codec_;
    std::unique_ptr<FitnessFunction> fitness_;
    std::unique_ptr<SelectionStrategy> selection_;
    std::unique_ptr<CrossoverStrategy> crossover_;
    std::unique_ptr<MutationStrategy> mutation_;
};
