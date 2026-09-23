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
#include "ObstacleGene.hpp"
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

    // Si se setea, la poblacion inicial arranca de este genoma (el individuo
    // 0 sin mutar, el resto con una mutacion de exploracion aplicada) en vez
    // de sampleo aleatorio puro -- refinamiento local alrededor de una config
    // ya conocida, en vez de buscar desde cero. Pensado para romper simetria
    // localmente: arrancar de un ganador simetrico y dejar que --symmetry
    // none lo perturbe libremente a ver si una version asimetrica mejora.
    // El genoma debe ser compatible con el codec (mismo tamano que
    // codec().freeCount()); con IdentityCodec eso es simplemente la lista de
    // obstaculos tal cual.
    void setSeedGenome(std::vector<ObstacleGene> genome) { seedGenome_ = std::move(genome); }

    const GenomeCodec& codec() const { return *codec_; }

private:
    Individual randomIndividual(std::mt19937_64& rng) const;
    double evaluateIndividual(const std::vector<ObstacleGene>& genome,
                              const std::vector<unsigned long>& seeds) const;

    OptimizerConfig config_;
    std::vector<ObstacleGene> seedGenome_;
    std::unique_ptr<GenomeCodec> codec_;
    std::unique_ptr<FitnessFunction> fitness_;
    std::unique_ptr<SelectionStrategy> selection_;
    std::unique_ptr<CrossoverStrategy> crossover_;
    std::unique_ptr<MutationStrategy> mutation_;
};
