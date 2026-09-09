#include <exception>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

#include "Config.hpp"
#include "ObstacleConfig.hpp"
#include "OutputWriter.hpp"
#include "SimulationEngine.hpp"

namespace {

void printUsage() {
    std::cout
        << "Uso: simulador [opciones]\n\n"
        << "Simulacion dirigida por eventos del billar-metegol (SdS TP3).\n\n"
        << "Dominio:\n"
        << "  --length VALOR         Largo L de la mesa en m (default 1.20)\n"
        << "  --width VALOR          Ancho W de la mesa en m (default 0.68)\n"
        << "  --goal-size VALOR      Largo d del arco en m (default 0.20)\n"
        << "  --config ARCHIVO       Obstaculos, una linea \"x y R\" por obstaculo\n"
        << "                         (default: mesa vacia)\n\n"
        << "Particulas:\n"
        << "  --particles N          Cantidad de particulas (default 100)\n"
        << "  --radius VALOR         Radio r en m (default 0.0175)\n"
        << "  --mass VALOR           Masa m en kg (default 0.025)\n"
        << "  --v0 VALOR             Modulo de la velocidad inicial en m/s (default 1.0)\n\n"
        << "Corrida:\n"
        << "  --tmax VALOR           Tiempo maximo simulado en s (default 100)\n"
        << "  --seed VALOR           Semilla del generador (default 42)\n"
        << "  --stop-fraction VALOR  Corta al alcanzar esta F_u; >1 desactiva el corte\n"
        << "                         (default 2.0)\n"
        << "  --cada-eventos N       Guarda el estado cada N eventos (default 100)\n\n"
        << "Salida:\n"
        << "  --output ARCHIVO       Serie temporal compacta (default salida.csv)\n"
        << "  --trajectory ARCHIVO   Trayectoria completa para animar (default: no se escribe)\n"
        << "  --help                 Muestra esta ayuda\n";
}

// Devuelve el valor del flag actual y avanza el indice; aborta si falta el valor.
std::string takeValue(const std::vector<std::string>& args, std::size_t& index) {
    if (index + 1 >= args.size()) {
        throw std::runtime_error("Falta el valor del flag " + args[index]);
    }
    return args[++index];
}

Config parseArguments(const std::vector<std::string>& args, bool& showHelp) {
    Config config;
    config.stopFraction = 2.0;  // Por default no se corta antes de t_max

    for (std::size_t i = 0; i < args.size(); ++i) {
        const std::string& flag = args[i];
        if (flag == "--help" || flag == "-h") {
            showHelp = true;
            return config;
        } else if (flag == "--length") {
            config.length = std::stod(takeValue(args, i));
        } else if (flag == "--width") {
            config.width = std::stod(takeValue(args, i));
        } else if (flag == "--goal-size") {
            config.goalSize = std::stod(takeValue(args, i));
        } else if (flag == "--config") {
            config.obstaclesPath = takeValue(args, i);
        } else if (flag == "--particles") {
            config.particleCount = std::stoi(takeValue(args, i));
        } else if (flag == "--radius") {
            config.particleRadius = std::stod(takeValue(args, i));
        } else if (flag == "--mass") {
            config.particleMass = std::stod(takeValue(args, i));
        } else if (flag == "--v0") {
            config.initialSpeed = std::stod(takeValue(args, i));
        } else if (flag == "--tmax") {
            config.maxTime = std::stod(takeValue(args, i));
        } else if (flag == "--seed") {
            config.seed = std::stoul(takeValue(args, i));
        } else if (flag == "--stop-fraction") {
            config.stopFraction = std::stod(takeValue(args, i));
        } else if (flag == "--cada-eventos") {
            config.eventsPerSample = std::stol(takeValue(args, i));
        } else if (flag == "--output") {
            config.outputPath = takeValue(args, i);
        } else if (flag == "--trajectory") {
            config.trajectoryPath = takeValue(args, i);
        } else {
            throw std::runtime_error("Flag desconocido: " + flag);
        }
    }
    return config;
}

}  // namespace

int main(int argc, char** argv) {
    const std::vector<std::string> args(argv + 1, argv + argc);

    try {
        bool showHelp = false;
        Config config = parseArguments(args, showHelp);
        if (showHelp) {
            printUsage();
            return 0;
        }

        if (config.eventsPerSample <= 0) {
            throw std::runtime_error("--cada-eventos debe ser mayor que cero.");
        }

        if (!config.obstaclesPath.empty()) {
            config.obstacles = loadObstacles(config.obstaclesPath);
            const std::string error =
                validateObstacles(config.obstacles, config.length, config.width);
            if (!error.empty()) {
                throw std::runtime_error("Configuracion de obstaculos invalida: " + error);
            }
        }

        SimulationEngine engine(config);
        OutputWriter writer(config.outputPath, config.trajectoryPath);
        engine.run(writer);

        // Resumen en "clave=valor" para que la capa de orquestacion lo parsee sin
        // tener que releer el CSV. El tiempo de ejecucion lo mide el motor.
        std::cout << std::fixed << std::setprecision(6)
                  << "tiempo_ejecucion_s=" << engine.wallClockSeconds() << '\n'
                  << "eventos=" << engine.processedEvents() << '\n'
                  << "goles=" << engine.goals() << '\n'
                  << "t90=" << engine.timeToNinetyPercent() << '\n'
                  << "tiempo_final=" << engine.finalTime() << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
