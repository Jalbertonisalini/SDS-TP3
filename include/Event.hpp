#pragma once

#include <limits>

// Tipo de colision que representa el evento.
enum class EventType {
    ParticleParticle,
    ParticleObstacle,
    VerticalWall,   // Paredes cortas x = 0 y x = L; son las que llevan los arcos
    HorizontalWall  // Paredes largas y = 0 e y = W
};

// Un evento agendado. Guarda las cuentas de colision de los involucrados al
// momento de agendarlo: si al desencolarlo no coinciden, el evento quedo obsoleto.
struct Event {
    double time = std::numeric_limits<double>::infinity();
    EventType type = EventType::VerticalWall;
    int firstParticle = -1;
    int secondParticle = -1;  // Otra particula, indice de obstaculo, o -1
    unsigned long firstCount = 0;
    unsigned long secondCount = 0;

    // La cola de prioridad de la STL es un max-heap: invertimos la comparacion
    // para que salga primero el evento mas cercano en el tiempo.
    bool operator<(const Event& other) const { return time > other.time; }
};
