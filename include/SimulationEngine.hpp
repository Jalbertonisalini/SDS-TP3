#pragma once

#include <queue>
#include <vector>

#include "Config.hpp"
#include "Event.hpp"
#include "GoalEvent.hpp"
#include "OutputWriter.hpp"
#include "Particle.hpp"

// Dinamica molecular dirigida por eventos para el problema del billar-metegol.
// Entre colisiones las particulas se mueven en linea recta a velocidad constante;
// todas las colisiones son elasticas.
//
// El motor solo evoluciona el estado y lo entrega: no calcula observables.
// F_u, t90, DCM, etc. se calculan en postproceso a partir de su salida.
class SimulationEngine {
public:
    explicit SimulationEngine(const Config& config);

    // Corre la simulacion completa: vuelca el estado de las particulas cada
    // config.eventsPerSample eventos y, al final, el registro de goles.
    void run(OutputWriter& writer);

    // Igual que run(), pero sin OutputWriter: corre exclusivamente en memoria
    // y devuelve el registro de goles. Pensada para evaluaciones masivas
    // (p.ej. busqueda genetica); el fitness se calcula afuera del motor.
    std::vector<GoalEvent> runSilent();

    // Metricas de rendimiento de la corrida (no son observables fisicos),
    // disponibles despues de run().
    double wallClockSeconds() const { return wallClockSeconds_; }
    long processedEvents() const { return processedEvents_; }
    double finalTime() const { return time_; }

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

    void sample(OutputWriter* writer);

    // Bucle de eventos compartido por run() y runSilent(). writer == nullptr
    // significa "sin I/O": sample() no se llama en ningun punto.
    void runLoop(OutputWriter* writer);

    Config config_;
    std::vector<Particle> particles_;
    std::priority_queue<Event> queue_;

    double time_ = 0.0;
    std::vector<GoalEvent> goalEvents_;
    long processedEvents_ = 0;
    double wallClockSeconds_ = 0.0;
};
