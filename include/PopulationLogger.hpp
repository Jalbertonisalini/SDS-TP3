#pragma once

#include <string>
#include <vector>

#include "GenomeCodec.hpp"
#include "Individual.hpp"

// Log detallado de una corrida del GA: cada `interval` generaciones, vuelca
// la poblacion completa (obstaculos ya expandidos, con fitness) a un CSV
// propio dentro de `directory` (gen_00000.csv, gen_00005.csv, ...) e imprime
// una linea de progreso por stdout. Pensado para una corrida chica y
// puntual que se quiere animar generacion a generacion -- no para el
// barrido grande, cada archivo pesa poblacion x obstaculos filas.
class PopulationLogger {
public:
    // totalGenerations se usa solo para no perderse la ultima generacion
    // aunque no caiga justo en un multiplo de interval.
    PopulationLogger(const std::string& directory, int interval, int totalGenerations);

    // No hace nada si generation no es multiplo de interval ni es la ultima
    // generacion de la corrida.
    void log(int generation, const std::vector<Individual>& population, const GenomeCodec& codec);

private:
    std::string directory_;
    int interval_;
    int totalGenerations_;
};
