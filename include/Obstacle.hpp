#pragma once

#include "Vec2.hpp"

// Obstaculo circular fijo, de masa infinita.
struct Obstacle {
    Vec2 center;
    double radius = 0.0;
};
