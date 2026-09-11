#include <chrono>
#include <exception>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "CrossoverStrategy.hpp"
#include "FitnessFunction.hpp"
#include "GenerationLogger.hpp"
#include "GenomeCodec.hpp"
#include "MutationStrategy.hpp"
#include "Optimizer.hpp"
#include "OptimizerConfig.hpp"
#include "SelectionStrategy.hpp"

namespace {

void printUsage() {
    std::cout
        << "Uso: optimizador [opciones]\n\n"
        << "Busqueda genetica de una configuracion de obstaculos que minimice t90\n"
        << "(SdS TP3, punto 1.2).\n\n"
        << "Dominio y particulas (igual que simulador):\n"
        << "  --length VALOR         Largo L de la mesa en m (default 1.20)\n"
        << "  --width VALOR          Ancho W de la mesa en m (default 0.68)\n"
        << "  --goal-size VALOR      Largo d del arco en m (default 0.20)\n"
        << "  --particles N          Cantidad de particulas (default 100)\n"
        << "  --radius VALOR         Radio r de las particulas en m (default 0.0175)\n"
        << "  --mass VALOR           Masa m en kg (default 0.025)\n"
        << "  --v0 VALOR             Modulo de la velocidad inicial en m/s (default 1.0)\n"
        << "  --tmax VALOR           Tiempo maximo simulado en s (default 100)\n\n"
        << "Obstaculos a optimizar:\n"
        << "  --obstacles K          Cantidad de obstaculos (default 4)\n"
        << "  --symmetry VALOR       none (default), horizontal o quad\n"
        << "  --min-radius VALOR     Radio minimo de obstaculo en m, > --radius (default 0.02)\n"
        << "  --max-radius VALOR     Radio maximo de obstaculo en m (default 0.25). Los genes\n"
        << "                         de cuadrante/pareados (--symmetry != none) tienen un\n"
        << "                         techo geometrico propio cerca de min(L,W)/4 sin importar\n"
        << "                         este valor; el gen central no\n"
        << "  --max-packing-density VALOR\n"
        << "                         Factor de seguridad del filtro de factibilidad\n"
        << "                         de empaquetamiento (default 0.5)\n"
        << "  --goal-clearance VALOR Distancia minima libre a cada arco en m\n"
        << "                         (default 0.0, desactivado)\n\n"
        << "Fitness:\n"
        << "  --target-goals N       Goles objetivo N_target (default 90)\n"
        << "  --alpha VALOR          Penalizacion por gol faltante, >= 1.0 (default 1.0)\n\n"
        << "Algoritmo genetico:\n"
        << "  --population N         Tamano de poblacion (default 64)\n"
        << "  --generations N        Cantidad de generaciones (default 100)\n"
        << "  --seeds-per-gen N      Semillas comunes por generacion, S (default 5)\n"
        << "  --tournament-size N    Tamano del torneo de seleccion (default 3)\n"
        << "  --elitism N            Individuos que pasan directo (default 2)\n"
        << "  --crossover-alpha VALOR\n"
        << "                         Alpha del BLX-alpha (default 0.3)\n"
        << "  --mutation-individual-rate VALOR\n"
        << "                         Probabilidad de mutar un individuo (default 1.0)\n"
        << "  --mutation-gene-rate VALOR\n"
        << "                         Probabilidad de mutar cada gen (default 0.3)\n"
        << "  --mutation-sigma-position-start VALOR\n"
        << "                         Sigma en x,y en la generacion 0 (default 0.06 m)\n"
        << "  --mutation-sigma-position-end VALOR\n"
        << "                         Sigma en x,y en la ultima generacion (default 0.02 m)\n"
        << "  --mutation-sigma-radius-start VALOR\n"
        << "                         Sigma en r en la generacion 0 (default 0.03 m)\n"
        << "  --mutation-sigma-radius-end VALOR\n"
        << "                         Sigma en r en la ultima generacion (default 0.008 m)\n"
        << "  --seed VALOR           Semilla del RNG maestro (default 42)\n"
        << "  --threads N            Hilos OpenMP a usar (default: todos los disponibles)\n\n"
        << "Salida:\n"
        << "  --config-out ARCHIVO   Mejor configuracion encontrada, formato \"x y R\"\n"
        << "                         cargable con simulador --config (default mejor_config.txt)\n"
        << "  --log ARCHIVO          CSV de convergencia por generacion (default: no se escribe)\n"
        << "  --help                 Muestra esta ayuda\n";
}

std::string takeValue(const std::vector<std::string>& args, std::size_t& index) {
    if (index + 1 >= args.size()) {
        throw std::runtime_error("Falta el valor del flag " + args[index]);
    }
    return args[++index];
}

struct CliOptions {
    OptimizerConfig config;
    std::string configOutPath = "mejor_config.txt";
    std::string logPath;
    int threads = 0;  // 0 = no tocar el default de OpenMP
};

CliOptions parseArguments(const std::vector<std::string>& args, bool& showHelp) {
    CliOptions options;

    for (std::size_t i = 0; i < args.size(); ++i) {
        const std::string& flag = args[i];
        if (flag == "--help" || flag == "-h") {
            showHelp = true;
            return options;
        } else if (flag == "--length") {
            options.config.length = std::stod(takeValue(args, i));
        } else if (flag == "--width") {
            options.config.width = std::stod(takeValue(args, i));
        } else if (flag == "--goal-size") {
            options.config.goalSize = std::stod(takeValue(args, i));
        } else if (flag == "--particles") {
            options.config.particleCount = std::stoi(takeValue(args, i));
        } else if (flag == "--radius") {
            options.config.particleRadius = std::stod(takeValue(args, i));
        } else if (flag == "--mass") {
            options.config.particleMass = std::stod(takeValue(args, i));
        } else if (flag == "--v0") {
            options.config.initialSpeed = std::stod(takeValue(args, i));
        } else if (flag == "--tmax") {
            options.config.maxTime = std::stod(takeValue(args, i));
        } else if (flag == "--obstacles") {
            options.config.obstacleCount = std::stoi(takeValue(args, i));
        } else if (flag == "--symmetry") {
            const std::string val = takeValue(args, i);
            if (val == "none") {
                options.config.symmetry = SymmetryMode::None;
            } else if (val == "horizontal") {
                options.config.symmetry = SymmetryMode::Horizontal;
            } else if (val == "quad") {
                options.config.symmetry = SymmetryMode::FourQuadrant;
            } else {
                throw std::runtime_error("Valor invalido para --symmetry: " + val);
            }
        } else if (flag == "--min-radius") {
            options.config.minRadius = std::stod(takeValue(args, i));
        } else if (flag == "--max-radius") {
            options.config.maxRadius = std::stod(takeValue(args, i));
        } else if (flag == "--max-packing-density") {
            options.config.maxPackingDensity = std::stod(takeValue(args, i));
        } else if (flag == "--goal-clearance") {
            options.config.goalClearance = std::stod(takeValue(args, i));
        } else if (flag == "--target-goals") {
            options.config.targetGoals = std::stoi(takeValue(args, i));
        } else if (flag == "--alpha") {
            options.config.alpha = std::stod(takeValue(args, i));
        } else if (flag == "--population") {
            options.config.populationSize = std::stoi(takeValue(args, i));
        } else if (flag == "--generations") {
            options.config.generations = std::stoi(takeValue(args, i));
        } else if (flag == "--seeds-per-gen") {
            options.config.seedsPerGeneration = std::stoi(takeValue(args, i));
        } else if (flag == "--tournament-size") {
            options.config.tournamentSize = std::stoi(takeValue(args, i));
        } else if (flag == "--elitism") {
            options.config.elitism = std::stoi(takeValue(args, i));
        } else if (flag == "--crossover-alpha") {
            options.config.crossoverAlpha = std::stod(takeValue(args, i));
        } else if (flag == "--mutation-individual-rate") {
            options.config.individualMutationRate = std::stod(takeValue(args, i));
        } else if (flag == "--mutation-gene-rate") {
            options.config.geneMutationRate = std::stod(takeValue(args, i));
        } else if (flag == "--mutation-sigma-position-start") {
            options.config.mutationSigmaPositionStart = std::stod(takeValue(args, i));
        } else if (flag == "--mutation-sigma-position-end") {
            options.config.mutationSigmaPositionEnd = std::stod(takeValue(args, i));
        } else if (flag == "--mutation-sigma-radius-start") {
            options.config.mutationSigmaRadiusStart = std::stod(takeValue(args, i));
        } else if (flag == "--mutation-sigma-radius-end") {
            options.config.mutationSigmaRadiusEnd = std::stod(takeValue(args, i));
        } else if (flag == "--seed") {
            options.config.seed = std::stoul(takeValue(args, i));
        } else if (flag == "--threads") {
            options.threads = std::stoi(takeValue(args, i));
        } else if (flag == "--config-out") {
            options.configOutPath = takeValue(args, i);
        } else if (flag == "--log") {
            options.logPath = takeValue(args, i);
        } else {
            throw std::runtime_error("Flag desconocido: " + flag);
        }
    }
    return options;
}

std::unique_ptr<GenomeCodec> buildCodec(const OptimizerConfig& config) {
    switch (config.symmetry) {
        case SymmetryMode::Horizontal:
            return std::make_unique<HorizontalSymmetryCodec>(
                config.length, config.width, config.minRadius, config.maxRadius,
                config.obstacleCount);
        case SymmetryMode::FourQuadrant:
            return std::make_unique<FourQuadrantSymmetryCodec>(
                config.length, config.width, config.minRadius, config.maxRadius,
                config.obstacleCount);
        case SymmetryMode::None:
        default:
            return std::make_unique<IdentityCodec>(config.length, config.width, config.minRadius,
                                                    config.maxRadius, config.obstacleCount);
    }
}

void writeConfigOut(const std::string& path, const std::vector<Obstacle>& obstacles,
                    const OptimizerConfig& config, double bestFitness) {
    std::ofstream out(path);
    if (!out) {
        throw std::runtime_error("No se pudo abrir --config-out: " + path);
    }
    out << "# Generado por optimizador (busqueda genetica)\n"
        << "# obstaculos=" << config.obstacleCount << " semilla=" << config.seed
        << " mejor_fitness=" << std::fixed << std::setprecision(6) << bestFitness << '\n';
    out.setf(std::ios::fixed);
    out.precision(6);
    for (const Obstacle& o : obstacles) {
        out << o.center.x << ' ' << o.center.y << ' ' << o.radius << '\n';
    }
}

}  // namespace

int main(int argc, char** argv) {
    const std::vector<std::string> args(argv + 1, argv + argc);

    try {
        bool showHelp = false;
        CliOptions options = parseArguments(args, showHelp);
        if (showHelp) {
            printUsage();
            return 0;
        }

        options.config.validate();

#ifdef _OPENMP
        if (options.threads > 0) {
            omp_set_num_threads(options.threads);
        }
#endif

        std::unique_ptr<GenomeCodec> codec = buildCodec(options.config);
        auto fitness = std::make_unique<GoalPenalizedFitness>(options.config.targetGoals,
                                                               options.config.alpha);
        auto selection = std::make_unique<TournamentSelection>(options.config.tournamentSize);
        auto crossover =
            std::make_unique<BlxAlphaCrossover>(options.config, options.config.crossoverAlpha);
        auto mutation = std::make_unique<GaussianMutation>(
            options.config, options.config.individualMutationRate,
            options.config.geneMutationRate, options.config.mutationSigmaPositionStart,
            options.config.mutationSigmaPositionEnd, options.config.mutationSigmaRadiusStart,
            options.config.mutationSigmaRadiusEnd);

        Optimizer optimizer(options.config, std::move(codec), std::move(fitness),
                            std::move(selection), std::move(crossover), std::move(mutation));

        std::unique_ptr<GenerationLogger> logger;
        if (!options.logPath.empty()) {
            logger = std::make_unique<GenerationLogger>(options.logPath);
        }

        const auto start = std::chrono::steady_clock::now();
        Individual best = optimizer.run(logger.get());
        const auto end = std::chrono::steady_clock::now();

        const std::vector<Obstacle> bestObstacles = optimizer.codec().expand(best.genome);
        writeConfigOut(options.configOutPath, bestObstacles, options.config, best.fitness);

        std::cout << std::fixed << std::setprecision(6)
                  << "tiempo_ejecucion_s="
                  << std::chrono::duration<double>(end - start).count() << '\n'
                  << "mejor_fitness=" << best.fitness << '\n'
                  << "generaciones=" << options.config.generations << '\n'
                  << "poblacion=" << options.config.populationSize << '\n'
                  << "obstaculos=" << options.config.obstacleCount << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
