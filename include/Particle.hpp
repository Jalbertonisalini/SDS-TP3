#pragma once

#include "Vec2.hpp"

// Estado de "uso" de una particula: fresca (azul) hasta el primer gol, usada (roja) despues.
enum class ParticleState { Fresh = 0, Used = 1 };

struct Particle {
    Vec2 position;
    Vec2 velocity;
    Vec2 initialPosition;  // Referencia para el desplazamiento cuadratico medio
    double radius = 0.0;
    double mass = 0.0;
    ParticleState state = ParticleState::Fresh;

    // Cuenta de colisiones sufridas. Sirve para invalidar eventos viejos en la cola
    // sin tener que buscarlos y borrarlos.
    unsigned long collisionCount = 0;
};
