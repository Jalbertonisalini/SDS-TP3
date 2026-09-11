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
class OutputWriter
{
public:
    // Si noOutput es true no se abre ningun archivo y las escrituras son no-ops;
    // pensado para corridas masivas donde solo importa
    // el resumen por stdout y escribir a disco llenaria el disco rapido.
    OutputWriter(const std::string &seriesPath, const std::string &trajectoryPath,
                 bool noOutput = false);

    bool writesTrajectory() const { return trajectory_.is_open(); }

    void writeSeries(double time, int goals, double usedFraction, double meanSquaredDisplacement);
    void writeTrajectory(double time, const std::vector<Particle> &particles);

private:
    std::ofstream series_;
    std::ofstream trajectory_;
};
