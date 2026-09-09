#include "SimulationEngine.hpp"

#include <chrono>
#include <cmath>
#include <limits>
#include <random>
#include <stdexcept>

namespace {
constexpr double kInfinity = std::numeric_limits<double>::infinity();
}  // namespace

SimulationEngine::SimulationEngine(const Config& config) : config_(config) {
    placeParticles();
}

// ---------------------------------------------------------------------------
// Condicion inicial
// ---------------------------------------------------------------------------

bool SimulationEngine::overlapsSomething(const Vec2& candidate) const {
    const double r = config_.particleRadius;

    for (const Obstacle& obstacle : config_.obstacles) {
        if ((candidate - obstacle.center).norm() < r + obstacle.radius) {
            return true;
        }
    }
    for (const Particle& other : particles_) {
        if ((candidate - other.position).norm() < 2.0 * r) {
            return true;
        }
    }
    return false;
}

void SimulationEngine::placeParticles() {
    std::mt19937_64 generator(config_.seed);
    const double r = config_.particleRadius;
    std::uniform_real_distribution<double> xDist(r, config_.length - r);
    std::uniform_real_distribution<double> yDist(r, config_.width - r);
    std::uniform_real_distribution<double> angleDist(0.0, 2.0 * M_PI);

    // Cota generosa de intentos: si no alcanza, la configuracion de obstaculos
    // no deja lugar para las N particulas y conviene fallar ruidosamente.
    const int maxAttemptsPerParticle = 100000;

    particles_.reserve(static_cast<std::size_t>(config_.particleCount));
    for (int i = 0; i < config_.particleCount; ++i) {
        Vec2 candidate;
        int attempts = 0;
        do {
            if (++attempts > maxAttemptsPerParticle) {
                throw std::runtime_error(
                    "No se pudieron ubicar las " + std::to_string(config_.particleCount) +
                    " particulas sin solapamientos: la configuracion de obstaculos deja muy poco "
                    "espacio libre.");
            }
            candidate = {xDist(generator), yDist(generator)};
        } while (overlapsSomething(candidate));

        const double angle = angleDist(generator);
        Particle particle;
        particle.position = candidate;
        particle.initialPosition = candidate;
        particle.velocity = {config_.initialSpeed * std::cos(angle),
                             config_.initialSpeed * std::sin(angle)};
        particle.radius = r;
        particle.mass = config_.particleMass;
        particles_.push_back(particle);
    }
}

// ---------------------------------------------------------------------------
// Prediccion de colisiones
// ---------------------------------------------------------------------------

double SimulationEngine::timeToParticle(const Particle& a, const Particle& b) const {
    const Vec2 dr = b.position - a.position;
    const Vec2 dv = b.velocity - a.velocity;
    const double dvdr = dv.dot(dr);
    if (dvdr >= 0.0) {
        return kInfinity;  // Se estan separando
    }

    const double dvdv = dv.norm2();
    if (dvdv == 0.0) {
        return kInfinity;
    }

    const double sigma = a.radius + b.radius;
    const double discriminant = dvdr * dvdr - dvdv * (dr.norm2() - sigma * sigma);
    if (discriminant < 0.0) {
        return kInfinity;  // Las trayectorias no llegan a tocarse
    }

    const double time = -(dvdr + std::sqrt(discriminant)) / dvdv;
    return time > 0.0 ? time : kInfinity;
}

double SimulationEngine::timeToObstacle(const Particle& p, const Obstacle& o) const {
    // Mismo calculo que entre particulas, con el obstaculo quieto.
    const Vec2 dr = o.center - p.position;
    const Vec2 dv = p.velocity * -1.0;
    const double dvdr = dv.dot(dr);
    if (dvdr >= 0.0) {
        return kInfinity;
    }

    const double dvdv = dv.norm2();
    if (dvdv == 0.0) {
        return kInfinity;
    }

    const double sigma = p.radius + o.radius;
    const double discriminant = dvdr * dvdr - dvdv * (dr.norm2() - sigma * sigma);
    if (discriminant < 0.0) {
        return kInfinity;
    }

    const double time = -(dvdr + std::sqrt(discriminant)) / dvdv;
    return time > 0.0 ? time : kInfinity;
}

double SimulationEngine::timeToVerticalWall(const Particle& p) const {
    if (p.velocity.x > 0.0) {
        return (config_.length - p.radius - p.position.x) / p.velocity.x;
    }
    if (p.velocity.x < 0.0) {
        return (p.radius - p.position.x) / p.velocity.x;
    }
    return kInfinity;
}

double SimulationEngine::timeToHorizontalWall(const Particle& p) const {
    if (p.velocity.y > 0.0) {
        return (config_.width - p.radius - p.position.y) / p.velocity.y;
    }
    if (p.velocity.y < 0.0) {
        return (p.radius - p.position.y) / p.velocity.y;
    }
    return kInfinity;
}

void SimulationEngine::scheduleEventsFor(int index) {
    const Particle& p = particles_[static_cast<std::size_t>(index)];

    Event wallX;
    wallX.time = time_ + timeToVerticalWall(p);
    wallX.type = EventType::VerticalWall;
    wallX.firstParticle = index;
    wallX.firstCount = p.collisionCount;
    if (std::isfinite(wallX.time)) {
        queue_.push(wallX);
    }

    Event wallY;
    wallY.time = time_ + timeToHorizontalWall(p);
    wallY.type = EventType::HorizontalWall;
    wallY.firstParticle = index;
    wallY.firstCount = p.collisionCount;
    if (std::isfinite(wallY.time)) {
        queue_.push(wallY);
    }

    for (std::size_t k = 0; k < config_.obstacles.size(); ++k) {
        const double time = timeToObstacle(p, config_.obstacles[k]);
        if (!std::isfinite(time)) {
            continue;
        }
        Event event;
        event.time = time_ + time;
        event.type = EventType::ParticleObstacle;
        event.firstParticle = index;
        event.secondParticle = static_cast<int>(k);
        event.firstCount = p.collisionCount;
        queue_.push(event);
    }

    for (std::size_t j = 0; j < particles_.size(); ++j) {
        if (static_cast<int>(j) == index) {
            continue;
        }
        const double time = timeToParticle(p, particles_[j]);
        if (!std::isfinite(time)) {
            continue;
        }
        Event event;
        event.time = time_ + time;
        event.type = EventType::ParticleParticle;
        event.firstParticle = index;
        event.secondParticle = static_cast<int>(j);
        event.firstCount = p.collisionCount;
        event.secondCount = particles_[j].collisionCount;
        queue_.push(event);
    }
}

// ---------------------------------------------------------------------------
// Resolucion de colisiones
// ---------------------------------------------------------------------------

void SimulationEngine::advanceTo(double newTime) {
    const double dt = newTime - time_;
    if (dt <= 0.0) {
        return;
    }
    for (Particle& p : particles_) {
        p.position += p.velocity * dt;
    }
    time_ = newTime;
}

void SimulationEngine::resolveParticleCollision(int i, int j) {
    Particle& a = particles_[static_cast<std::size_t>(i)];
    Particle& b = particles_[static_cast<std::size_t>(j)];

    const Vec2 dr = b.position - a.position;
    const Vec2 dv = b.velocity - a.velocity;
    const double sigma = a.radius + b.radius;

    // Impulso de una colision elastica entre discos (Teorica 2).
    const double impulse = 2.0 * a.mass * b.mass * dv.dot(dr) / (sigma * (a.mass + b.mass));
    const Vec2 j_vec = {impulse * dr.x / sigma, impulse * dr.y / sigma};

    a.velocity += j_vec * (1.0 / a.mass);
    b.velocity += j_vec * (-1.0 / b.mass);
}

void SimulationEngine::resolveObstacleCollision(int i, int obstacleIndex) {
    Particle& p = particles_[static_cast<std::size_t>(i)];
    const Obstacle& obstacle = config_.obstacles[static_cast<std::size_t>(obstacleIndex)];

    // Masa infinita: la velocidad se refleja respecto de la normal al contacto.
    const Vec2 delta = p.position - obstacle.center;
    const double distance = delta.norm();
    if (distance == 0.0) {
        return;
    }
    const Vec2 normal = delta * (1.0 / distance);
    const double projection = p.velocity.dot(normal);
    p.velocity += normal * (-2.0 * projection);
}

void SimulationEngine::resolveVerticalWall(int i) {
    Particle& p = particles_[static_cast<std::size_t>(i)];

    // El punto de contacto con una pared corta tiene la misma ordenada que el centro.
    const bool insideGoal = std::abs(p.position.y - config_.width / 2.0) <= config_.goalSize / 2.0;
    if (insideGoal && p.state == ParticleState::Fresh) {
        p.state = ParticleState::Used;
        ++goals_;
        const double usedFraction = static_cast<double>(goals_) / config_.particleCount;
        if (timeToNinety_ < 0.0 && usedFraction >= 0.9) {
            timeToNinety_ = time_;
        }
    }

    // La pared es indeformable y esta tambien sobre el arco: la particula rebota siempre.
    p.velocity.x = -p.velocity.x;
}

void SimulationEngine::resolveHorizontalWall(int i) {
    Particle& p = particles_[static_cast<std::size_t>(i)];
    p.velocity.y = -p.velocity.y;
}

// ---------------------------------------------------------------------------
// Observables y bucle principal
// ---------------------------------------------------------------------------

double SimulationEngine::meanSquaredDisplacement() const {
    if (particles_.empty()) {
        return 0.0;
    }
    double total = 0.0;
    for (const Particle& p : particles_) {
        total += (p.position - p.initialPosition).norm2();
    }
    return total / static_cast<double>(particles_.size());
}

void SimulationEngine::sample(OutputWriter& writer) {
    const double usedFraction = static_cast<double>(goals_) / config_.particleCount;
    writer.writeSeries(time_, goals_, usedFraction, meanSquaredDisplacement());
    writer.writeTrajectory(time_, particles_);
}

void SimulationEngine::run(OutputWriter& writer) {
    const auto start = std::chrono::steady_clock::now();

    for (int i = 0; i < config_.particleCount; ++i) {
        scheduleEventsFor(i);
    }
    sample(writer);

    while (!queue_.empty()) {
        const Event event = queue_.top();
        queue_.pop();

        // Evento obsoleto: alguno de los involucrados ya choco con otra cosa.
        const Particle& first = particles_[static_cast<std::size_t>(event.firstParticle)];
        if (first.collisionCount != event.firstCount) {
            continue;
        }
        if (event.type == EventType::ParticleParticle) {
            const Particle& second = particles_[static_cast<std::size_t>(event.secondParticle)];
            if (second.collisionCount != event.secondCount) {
                continue;
            }
        }

        if (event.time > config_.maxTime) {
            break;
        }

        advanceTo(event.time);

        switch (event.type) {
            case EventType::ParticleParticle:
                resolveParticleCollision(event.firstParticle, event.secondParticle);
                break;
            case EventType::ParticleObstacle:
                resolveObstacleCollision(event.firstParticle, event.secondParticle);
                break;
            case EventType::VerticalWall:
                resolveVerticalWall(event.firstParticle);
                break;
            case EventType::HorizontalWall:
                resolveHorizontalWall(event.firstParticle);
                break;
        }

        ++particles_[static_cast<std::size_t>(event.firstParticle)].collisionCount;
        scheduleEventsFor(event.firstParticle);
        if (event.type == EventType::ParticleParticle) {
            ++particles_[static_cast<std::size_t>(event.secondParticle)].collisionCount;
            scheduleEventsFor(event.secondParticle);
        }

        ++processedEvents_;
        if (processedEvents_ % config_.eventsPerSample == 0) {
            sample(writer);
        }

        const double usedFraction = static_cast<double>(goals_) / config_.particleCount;
        if (usedFraction >= config_.stopFraction) {
            break;
        }
    }

    // La corrida siempre llega hasta t_max (salvo corte por stopFraction), asi que
    // el ultimo tramo sin eventos tambien cuenta.
    if (goals_ < static_cast<int>(config_.stopFraction * config_.particleCount)) {
        advanceTo(config_.maxTime);
    }
    sample(writer);

    const auto end = std::chrono::steady_clock::now();
    wallClockSeconds_ = std::chrono::duration<double>(end - start).count();
}
