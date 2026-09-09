#include "ObstacleConfig.hpp"

#include <cmath>
#include <fstream>
#include <sstream>
#include <stdexcept>

std::vector<Obstacle> loadObstacles(const std::string& path) {
    std::ifstream file(path);
    if (!file) {
        throw std::runtime_error("No se pudo abrir el archivo de obstaculos: " + path);
    }

    std::vector<Obstacle> obstacles;
    std::string line;
    int lineNumber = 0;
    while (std::getline(file, line)) {
        ++lineNumber;
        // Se saltean comentarios y lineas en blanco para poder documentar la configuracion.
        const std::size_t firstNonSpace = line.find_first_not_of(" \t\r");
        if (firstNonSpace == std::string::npos || line[firstNonSpace] == '#') {
            continue;
        }

        std::istringstream stream(line);
        Obstacle obstacle;
        if (!(stream >> obstacle.center.x >> obstacle.center.y >> obstacle.radius)) {
            throw std::runtime_error("Linea " + std::to_string(lineNumber) + " de " + path +
                                     " mal formada: se esperaba \"x y R\".");
        }
        obstacles.push_back(obstacle);
    }
    return obstacles;
}

std::string validateObstacles(const std::vector<Obstacle>& obstacles, double length, double width) {
    for (std::size_t k = 0; k < obstacles.size(); ++k) {
        const Obstacle& o = obstacles[k];
        const std::string id = "obstaculo " + std::to_string(k);

        if (o.radius <= 0.0) {
            return id + ": el radio debe ser positivo.";
        }
        // Restriccion (i): entra integro en el dominio.
        if (o.center.x - o.radius < 0.0 || o.center.x + o.radius > length ||
            o.center.y - o.radius < 0.0 || o.center.y + o.radius > width) {
            return id + ": no entra integro dentro del dominio.";
        }
        // Restriccion (i): no se solapa con los anteriores.
        for (std::size_t j = 0; j < k; ++j) {
            const Obstacle& other = obstacles[j];
            const double dx = o.center.x - other.center.x;
            const double dy = o.center.y - other.center.y;
            if (std::sqrt(dx * dx + dy * dy) < o.radius + other.radius) {
                return id + " se solapa con el obstaculo " + std::to_string(j) + ".";
            }
        }
    }
    return "";
}
