#pragma once

#include <fstream>
#include <string>
#include <vector>

#include "Particle.hpp"

// Escribe los dos formatos de salida del motor. No calcula nada: los observables
// llegan ya computados desde el motor.
//
//  - Serie temporal compacta ("Time,Goals,UsedFraction,MSD"): es la que se usa
//    para todo el analisis.
//  - Trayectoria completa ("Time,ID,X,Y,VX,VY,State"): solo para animar, pesa mucho.
//    Los obstaculos no van aca; la animacion los lee del mismo archivo de configuracion
//    que recibio el motor.
class OutputWriter {
public:
    OutputWriter(const std::string& seriesPath, const std::string& trajectoryPath);

    bool writesTrajectory() const { return trajectory_.is_open(); }

    void writeSeries(double time, int goals, double usedFraction, double meanSquaredDisplacement);
    void writeTrajectory(double time, const std::vector<Particle>& particles);

private:
    std::ofstream series_;
    std::ofstream trajectory_;
};
