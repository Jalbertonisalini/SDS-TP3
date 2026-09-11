#pragma once

#include <vector>

#include "Obstacle.hpp"
#include "OptimizerConfig.hpp"

// Unico criterio de aceptacion de una configuracion candidata (ya expandida
// a obstaculos reales) durante la busqueda genetica. Lo usan por igual la
// generacion de poblacion inicial, la cruza y la mutacion, para no repetir
// la logica en cada operador. Combina:
//   1. validateObstacles() (include/ObstacleConfig.hpp): contencion en el
//      dominio + no solapamiento entre obstaculos, sobre el expandido (así
//      tambien detecta solapamientos entre espejos de la simetria).
//   2. Un filtro barato de factibilidad de empaquetamiento: si no queda
//      area libre razonable para ubicar las N particulas, se descarta antes
//      de siquiera construir un SimulationEngine (que gastaria hasta
//      1e6 intentos fallidos intentando ubicarlas).
//   3. (Opcional, cfg.goalClearance > 0) Un margen minimo libre alrededor de
//      la boca de cada arco, para no desperdiciar evaluaciones en
//      configuraciones que los tapan por completo.
bool isValidCandidate(const std::vector<Obstacle>& obstacles, const OptimizerConfig& config);
