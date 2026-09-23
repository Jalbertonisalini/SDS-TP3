#include "Optimizer.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <iostream>
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
    // Sampler secuencial: coloca un gen a la vez y lo valida contra lo ya
    // puesto (no contra el genoma completo, todavia inexistente), igual que
    // SimulationEngine::placeParticlesRandom hace con las particulas. Muchisimo
    // mas eficiente que tirar los freeCount genes juntos y descartar todo el
    // individuo si cualquiera de ellos choca -- esa version (sample-then-reject
    // en bloque) es la que dejaba a K=21 sin poder generar ni un individuo en
    // 10000 intentos: con 5 genes de cuadrante compitiendo por lugar, la
    // chance de que los 5 caigan bien a la vez es minuscula aunque sobre area.
    constexpr int maxAttemptsPerGene = 2000;
    constexpr int maxRestarts = 200;
    const int freeCount = codec_->freeCount();

    for (int restart = 0; restart < maxRestarts; ++restart) {
        std::vector<ObstacleGene> genome;
        genome.reserve(static_cast<std::size_t>(freeCount));
        bool stuck = false;

        for (int i = 0; i < freeCount; ++i) {
            bool placed = false;
            for (int attempt = 0; attempt < maxAttemptsPerGene; ++attempt) {
                const double r = sampleInBounds(codec_->minRadius(), codec_->radiusCeiling(i), rng);
                const PositionBounds pos = codec_->positionBounds(i, r);
                genome.push_back({
                    sampleInBounds(pos.xMin, pos.xMax, rng),
                    sampleInBounds(pos.yMin, pos.yMax, rng),
                    r,
                });
                if (isValidCandidate(codec_->expand(genome), config_)) {
                    placed = true;
                    break;
                }
                genome.pop_back();
            }
            if (!placed) {
                stuck = true;
                break;
            }
        }

        if (!stuck) {
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
        std::vector<GoalEvent> goals;
        try {
            SimulationEngine engine(simConfig);
            goals = engine.runSilent();
        } catch (const std::exception&) {
        }

        total += fitness_->evaluate(goals, config_.particleCount, config_.maxTime);
    }
    return total / static_cast<double>(seeds.size());
}

Individual Optimizer::run(GenerationLogger* logger, PopulationLogger* populationLogger) {
    const auto start = std::chrono::steady_clock::now();
    std::cerr << std::fixed << std::setprecision(3);

    std::mt19937_64 masterRng(config_.seed);

    std::vector<Individual> population;
    population.reserve(static_cast<std::size_t>(config_.populationSize));
    if (!seedGenome_.empty()) {
        // Poblacion inicial ancla en seedGenome_: el individuo 0 queda tal
        // cual (referencia exacta), el resto son mutaciones de exploracion
        // (progress=0 => sigma grande) a partir de esa misma base, para
        // explorar el entorno del seed en vez de partir de cero.
        population.push_back({seedGenome_, std::numeric_limits<double>::infinity()});
        for (int i = 1; i < config_.populationSize; ++i) {
            std::vector<ObstacleGene> genome = seedGenome_;
            mutation_->mutate(genome, *codec_, /*progress=*/0.0, masterRng);
            population.push_back({std::move(genome), std::numeric_limits<double>::infinity()});
        }
    } else {
        for (int i = 0; i < config_.populationSize; ++i) {
            population.push_back(randomIndividual(masterRng));
        }
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
        double sumSq = 0.0;
        double worst = -std::numeric_limits<double>::infinity();
        for (const Individual& individual : population) {
            sum += individual.fitness;
            sumSq += individual.fitness * individual.fitness;
            worst = std::max(worst, individual.fitness);
            if (individual.fitness < best.fitness) {
                best = individual;
            }
        }

        if (populationLogger != nullptr) {
            populationLogger->log(generation, population, *codec_);
        }

        const double elapsed =
            std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
        std::sort(population.begin(), population.end(),
                 [](const Individual& a, const Individual& b) { return a.fitness < b.fitness; });
        const double n = static_cast<double>(population.size());
        const double mean = sum / n;
        const double variance = std::max(0.0, sumSq / n - mean * mean);

        // A stderr (no stdout: ahi solo va el resumen final que parsean los
        // scripts) para poder seguir el progreso en foreground con `tail -f`
        // o simplemente mirando la terminal, sin ensuciar el output parseable.
        std::cerr << "  [gen " << (generation + 1) << "/" << config_.generations << "] "
                  << "mejor=" << population.front().fitness << " promedio=" << mean
                  << " desvio=" << std::sqrt(variance) << " peor=" << worst
                  << " t=" << elapsed << "s\n";

        if (logger != nullptr) {
            logger->log(generation, population.front().fitness, mean, std::sqrt(variance), worst,
                       elapsed);
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
