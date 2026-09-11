#include "Optimizer.hpp"

#include <algorithm>
#include <chrono>
#include <limits>
#include <stdexcept>

#include "CandidateValidator.hpp"
#include "Config.hpp"
#include "ParallelFor.hpp"
#include "SimulationEngine.hpp"

namespace {

// uniform_real_distribution requiere lo < hi; un gen de eje/central tiene
// lo == hi (esta fijo), asi que lo devolvemos directo sin pasar por la
// distribucion.
double sampleInBounds(double lo, double hi, std::mt19937_64& rng) {
    if (hi <= lo) {
        return lo;
    }
    std::uniform_real_distribution<double> dist(lo, hi);
    return dist(rng);
}

}  // namespace

Optimizer::Optimizer(OptimizerConfig config, std::unique_ptr<GenomeCodec> codec,
                     std::unique_ptr<FitnessFunction> fitness,
                     std::unique_ptr<SelectionStrategy> selection,
                     std::unique_ptr<CrossoverStrategy> crossover,
                     std::unique_ptr<MutationStrategy> mutation)
    : config_(config),
      codec_(std::move(codec)),
      fitness_(std::move(fitness)),
      selection_(std::move(selection)),
      crossover_(std::move(crossover)),
      mutation_(std::move(mutation)) {}

Individual Optimizer::randomIndividual(std::mt19937_64& rng) const {
    constexpr int maxAttempts = 10000;
    const int freeCount = codec_->freeCount();

    for (int attempt = 0; attempt < maxAttempts; ++attempt) {
        std::vector<ObstacleGene> genome(static_cast<std::size_t>(freeCount));
        for (int i = 0; i < freeCount; ++i) {
            const double r = sampleInBounds(codec_->minRadius(), codec_->maxRadius(), rng);
            const PositionBounds pos = codec_->positionBounds(i, r);
            genome[static_cast<std::size_t>(i)] = {
                sampleInBounds(pos.xMin, pos.xMax, rng),
                sampleInBounds(pos.yMin, pos.yMax, rng),
                r,
            };
        }
        if (isValidCandidate(codec_->expand(genome), config_)) {
            return {genome, std::numeric_limits<double>::infinity()};
        }
    }

    throw std::runtime_error(
        "No se pudo generar un individuo valido: revisar --obstacles, "
        "--min-radius/--max-radius o --max-packing-density.");
}

double Optimizer::evaluateIndividual(const std::vector<ObstacleGene>& genome,
                                     const std::vector<unsigned long>& seeds) const {
    const std::vector<Obstacle> obstacles = codec_->expand(genome);

    double total = 0.0;
    for (unsigned long seed : seeds) {
        Config simConfig;
        simConfig.length = config_.length;
        simConfig.width = config_.width;
        simConfig.goalSize = config_.goalSize;
        simConfig.particleCount = config_.particleCount;
        simConfig.particleRadius = config_.particleRadius;
        simConfig.particleMass = config_.particleMass;
        simConfig.initialSpeed = config_.initialSpeed;
        simConfig.maxTime = config_.maxTime;
        simConfig.seed = seed;
        simConfig.stopFraction =
            static_cast<double>(config_.targetGoals) / config_.particleCount;
        simConfig.obstacles = obstacles;

        // Config invalida o no entran las N particulas: peor caso posible,
        // no se cae la corrida por una configuracion patologica que se
        // haya colado (isValidCandidate ya filtra la enorme mayoria).
        SimulationEngine::RunResult result{-1.0, 0};
        try {
            SimulationEngine engine(simConfig);
            result = engine.runSilent();
        } catch (const std::exception&) {
        }

        total += fitness_->evaluate(result, config_.maxTime);
    }
    return total / static_cast<double>(seeds.size());
}

Individual Optimizer::run(GenerationLogger* logger, PopulationLogger* populationLogger) {
    const auto start = std::chrono::steady_clock::now();

    std::mt19937_64 masterRng(config_.seed);

    std::vector<Individual> population;
    population.reserve(static_cast<std::size_t>(config_.populationSize));
    for (int i = 0; i < config_.populationSize; ++i) {
        population.push_back(randomIndividual(masterRng));
    }

    Individual best;
    best.fitness = std::numeric_limits<double>::infinity();

    for (int generation = 0; generation < config_.generations; ++generation) {
        // Common Random Numbers: mismas S semillas para toda la poblacion de
        // esta generacion, se renuevan en la siguiente.
        std::vector<unsigned long> seeds(static_cast<std::size_t>(config_.seedsPerGeneration));
        for (unsigned long& seed : seeds) {
            seed = masterRng();
        }

        parallelFor(config_.populationSize, [&](int i) {
            population[static_cast<std::size_t>(i)].fitness =
                evaluateIndividual(population[static_cast<std::size_t>(i)].genome, seeds);
        });

        double sum = 0.0;
        double worst = -std::numeric_limits<double>::infinity();
        for (const Individual& individual : population) {
            sum += individual.fitness;
            worst = std::max(worst, individual.fitness);
            if (individual.fitness < best.fitness) {
                best = individual;
            }
        }

        if (populationLogger != nullptr) {
            populationLogger->log(generation, population, *codec_);
        }

        if (logger != nullptr) {
            const double elapsed =
                std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
            std::sort(population.begin(), population.end(),
                     [](const Individual& a, const Individual& b) { return a.fitness < b.fitness; });
            logger->log(generation, population.front().fitness,
                       sum / static_cast<double>(population.size()), worst, elapsed);
        } else {
            std::sort(population.begin(), population.end(),
                     [](const Individual& a, const Individual& b) { return a.fitness < b.fitness; });
        }

        if (generation + 1 == config_.generations) {
            break;  // Ultima generacion: no hace falta armar la siguiente.
        }

        // 0 en la primera generacion, 1 en la ultima: la mutacion arranca
        // explorando pasos grandes y termina afinando cerca del optimo.
        const double progress = config_.generations > 1
                                    ? static_cast<double>(generation) /
                                          static_cast<double>(config_.generations - 1)
                                    : 1.0;

        std::vector<Individual> next;
        next.reserve(static_cast<std::size_t>(config_.populationSize));
        for (int i = 0; i < config_.elitism; ++i) {
            next.push_back({population[static_cast<std::size_t>(i)].genome,
                            std::numeric_limits<double>::infinity()});
        }
        while (static_cast<int>(next.size()) < config_.populationSize) {
            const Individual& parentA = selection_->select(population, masterRng);
            const Individual& parentB = selection_->select(population, masterRng);
            std::vector<ObstacleGene> childGenome =
                crossover_->cross(parentA.genome, parentB.genome, *codec_, masterRng);
            mutation_->mutate(childGenome, *codec_, progress, masterRng);
            next.push_back({childGenome, std::numeric_limits<double>::infinity()});
        }
        population = std::move(next);
    }

    return best;
}
