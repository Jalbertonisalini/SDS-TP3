#pragma once

#include <fstream>
#include <string>
#include <vector>

#include "GoalEvent.hpp"
#include "Particle.hpp"

// Escribe los dos formatos de salida del motor. Solo vuelca estado y eventos:
// no calcula ningun observable (eso es trabajo del postproceso).
//
//  - Registro de goles ("Time,ID"): el instante exacto del primer gol de cada
//    particula. De aca salen F_u(t), t90 y la cantidad de goles.
//  - Trayectoria ("Time,ID,X,Y,VX,VY,State"): estado de todas las particulas
//    cada config.eventsPerSample eventos. De aca sale el DCM y la animacion.
//    Los obstaculos no van aca; la animacion los lee del mismo archivo de
//    configuracion que recibio el motor.
class OutputWriter
{
public:
    // Si noOutput es true no se abre ningun archivo y las escrituras son no-ops;
    // pensado para corridas masivas donde solo importa
    // el resumen por stdout y escribir a disco llenaria el disco rapido.
    OutputWriter(const std::string &goalsPath, const std::string &trajectoryPath,
                 bool noOutput = false);

    bool writesTrajectory() const { return trajectory_.is_open(); }

    void writeGoals(const std::vector<GoalEvent> &goals);
    void writeTrajectory(double time, const std::vector<Particle> &particles);

private:
    std::ofstream goals_;
    std::ofstream trajectory_;
};
