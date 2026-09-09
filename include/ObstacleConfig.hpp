#pragma once

#include <string>
#include <vector>

#include "Obstacle.hpp"

// Lee un archivo de configuracion de obstaculos: una linea por obstaculo con
// "x y R" en metros. Se ignoran las lineas vacias y las que empiezan con '#'.
// Lanza std::runtime_error si el archivo no existe o alguna linea esta mal formada.
std::vector<Obstacle> loadObstacles(const std::string& path);

// Verifica las restricciones del enunciado (punto 1.2): los obstaculos entran
// enteros en el dominio y no se solapan entre si. Devuelve un mensaje de error
// vacio si la configuracion es valida.
std::string validateObstacles(const std::vector<Obstacle>& obstacles, double length, double width);
