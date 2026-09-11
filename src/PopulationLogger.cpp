#include "PopulationLogger.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <ios>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>

#include "Obstacle.hpp"

namespace {
std::string generationFileName(int generation) {
    std::ostringstream name;
    name << "gen_" << std::setw(5) << std::setfill('0') << generation << ".csv";
    return name.str();
}
}  // namespace

PopulationLogger::PopulationLogger(const std::string& directory, int interval,
                                   int totalGenerations)
    : directory_(directory), interval_(interval), totalGenerations_(totalGenerations) {
    std::filesystem::create_directories(directory_);
}

void PopulationLogger::log(int generation, const std::vector<Individual>& population,
                           const GenomeCodec& codec) {
    const bool isLast = generation == totalGenerations_ - 1;
    if (interval_ <= 0 || (generation % interval_ != 0 && !isLast)) {
        return;
    }

    const std::string path = directory_ + "/" + generationFileName(generation);
    std::ofstream stream(path);
    if (!stream) {
        throw std::runtime_error("No se pudo abrir " + path + " para el log de poblacion.");
    }
    stream << "individuo,obstaculo,x,y,r,fitness\n";
    stream.setf(std::ios::fixed);
    stream.precision(6);

    double best = std::numeric_limits<double>::infinity();
    for (std::size_t i = 0; i < population.size(); ++i) {
        best = std::min(best, population[i].fitness);
        const std::vector<Obstacle> obstacles = codec.expand(population[i].genome);
        for (std::size_t o = 0; o < obstacles.size(); ++o) {
            stream << i << ',' << o << ',' << obstacles[o].center.x << ','
                   << obstacles[o].center.y << ',' << obstacles[o].radius << ','
                   << population[i].fitness << '\n';
        }
    }

    std::cout << "[offsprings] gen " << generation << "  mejor=" << std::fixed
               << std::setprecision(3) << best << "  -> " << path << '\n';
}
