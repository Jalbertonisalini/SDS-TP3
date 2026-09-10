#pragma once

#include <string>
#include <vector>

#include "Obstacle.hpp"

enum class Placement { Random, Hexagonal };

// Parametros de una corrida. Todos vienen de la CLI con default; el motor no
// tiene ninguna constante que obligue a recompilar.
struct Config {
    // Geometria del dominio (mesa de metegol)
    double length = 1.20;  // L [m]
    double width = 0.68;   // W [m]
    double goalSize = 0.20;  // d [m], centrado en y = W/2 sobre x = 0 y x = L

    // Particulas
    int particleCount = 100;      // N
    double particleRadius = 0.0175;  // r [m]
    double particleMass = 0.025;     // m [kg]
    double initialSpeed = 1.0;       // v0 [m/s]

    // Corrida
    double maxTime = 100.0;  // t_max [s]
    unsigned long seed = 42;
    double stopFraction = 1.0;  // Corta apenas F_u alcanza este valor (1.0 = nunca corta antes)

    // Muestreo: se guarda el estado cada eventsPerSample eventos, no en cada evento.
    long eventsPerSample = 100;

    // Entrada / salida
    std::string obstaclesPath;   // Archivo de obstaculos; vacio = mesa vacia
    std::string outputPath = "salida.csv";     // Serie temporal compacta
    std::string trajectoryPath;  // Trayectoria completa; vacio = no se escribe

    // Colocacion de particulas
    Placement placement = Placement::Random;

    std::vector<Obstacle> obstacles;
};
