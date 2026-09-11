#pragma once

#include <limits>
#include <vector>

#include "ObstacleGene.hpp"

// Un individuo de la poblacion: el genoma libre (antes de expandir por
// simetria) y su fitness (a minimizar). infinity() marca "todavia no evaluado".
struct Individual {
    std::vector<ObstacleGene> genome;
    double fitness = std::numeric_limits<double>::infinity();
};
