#pragma once

#include <queue>
#include <vector>

#include "Config.hpp"
#include "Event.hpp"
#include "OutputWriter.hpp"
#include "Particle.hpp"

// Dinamica molecular dirigida por eventos para el problema del billar-metegol.
// Entre colisiones las particulas se mueven en linea recta a velocidad constante;
// todas las colisiones son elasticas.
class SimulationEngine {
public:
    explicit SimulationEngine(const Config& config);

    // Corre la simulacion completa y va volcando el estado cada
    // config.eventsPerSample eventos. No hace I/O de inicializacion.
    void run(OutputWriter& writer);

    // Metricas de la corrida, disponibles despues de run().
    double wallClockSeconds() const { return wallClockSeconds_; }
    long processedEvents() const { return processedEvents_; }
    int goals() const { return goals_; }
    double finalTime() const { return time_; }

    // Tiempo en que F_u alcanzo 0.9; negativo si nunca lo alcanzo.
    double timeToNinetyPercent() const { return timeToNinety_; }

private:
    void placeParticles();
    void placeParticlesRandom();
    void placeParticlesHexagonal();
    bool overlapsSomething(const Vec2& candidate) const;

    // Prediccion de colisiones. Devuelven infinito si la colision no ocurre.
    double timeToParticle(const Particle& a, const Particle& b) const;
    double timeToObstacle(const Particle& p, const Obstacle& o) const;
    double timeToVerticalWall(const Particle& p) const;
    double timeToHorizontalWall(const Particle& p) const;

    // Agenda todos los eventos posibles de la particula index contra el resto
    // del sistema. Se la llama cada vez que la particula cambia de velocidad.
    void scheduleEventsFor(int index);

    void advanceTo(double newTime);
    void resolveParticleCollision(int i, int j);
    void resolveObstacleCollision(int i, int obstacleIndex);
    void resolveVerticalWall(int i);
    void resolveHorizontalWall(int i);

    double meanSquaredDisplacement() const;
    void sample(OutputWriter& writer);

    Config config_;
    std::vector<Particle> particles_;
    std::priority_queue<Event> queue_;

    double time_ = 0.0;
    int goals_ = 0;
    double timeToNinety_ = -1.0;
    long processedEvents_ = 0;
    double wallClockSeconds_ = 0.0;
};
