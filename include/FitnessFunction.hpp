#pragma once

#include <vector>

#include "GoalEvent.hpp"

// Fitness de una corrida (a minimizar). Interfaz separada del motor: recibe
// el registro de goles que devuelve el motor y calcula ella misma los
// observables que necesite; no sabe nada de eventos ni particulas.
class FitnessFunction {
public:
    virtual ~FitnessFunction() = default;
    virtual double evaluate(const std::vector<GoalEvent>& goals, int particleCount,
                            double maxTime) const = 0;
};

// f(ind, s) de la consigna: t90 si se alcanzo Fu >= 0.90 dentro de tmax,
// si no tmax + (targetGoals - goles a tmax) * alpha.
class GoalPenalizedFitness : public FitnessFunction {
public:
    GoalPenalizedFitness(int targetGoals, double alpha) : targetGoals_(targetGoals), alpha_(alpha) {}

    double evaluate(const std::vector<GoalEvent>& goals, int particleCount,
                    double maxTime) const override {
        const double t90 = timeToUsedFraction(goals, particleCount, kUsedFractionT90);
        if (t90 >= 0.0) {
            return t90;
        }
        const int goalCount = static_cast<int>(goals.size());
        return maxTime + static_cast<double>(targetGoals_ - goalCount) * alpha_;
    }

private:
    static constexpr double kUsedFractionT90 = 0.9;

    // Instante del gol con el que F_u alcanza `fraction`; negativo si no se
    // alcanzo. Los goles llegan en orden temporal desde el motor.
    static double timeToUsedFraction(const std::vector<GoalEvent>& goals, int particleCount,
                                     double fraction) {
        for (std::size_t k = 0; k < goals.size(); ++k) {
            const double usedFraction = static_cast<double>(k + 1) / particleCount;
            if (usedFraction >= fraction) {
                return goals[k].time;
            }
        }
        return -1.0;
    }

    int targetGoals_;
    double alpha_;
};
