#pragma once

#include "SimulationEngine.hpp"

// Fitness de una corrida (a minimizar). Interfaz separada del motor: recibe
// el resultado ya calculado, no sabe nada de eventos ni particulas.
class FitnessFunction {
public:
    virtual ~FitnessFunction() = default;
    virtual double evaluate(const SimulationEngine::RunResult& result, double maxTime) const = 0;
};

// f(ind, s) de la consigna: t90 si se alcanzo Fu >= 0.90 dentro de tmax,
// si no tmax + (targetGoals - goles a tmax) * alpha.
class GoalPenalizedFitness : public FitnessFunction {
public:
    GoalPenalizedFitness(int targetGoals, double alpha) : targetGoals_(targetGoals), alpha_(alpha) {}

    double evaluate(const SimulationEngine::RunResult& result, double maxTime) const override {
        if (result.t90 >= 0.0) {
            return result.t90;
        }
        return maxTime + static_cast<double>(targetGoals_ - result.goals) * alpha_;
    }

private:
    int targetGoals_;
    double alpha_;
};
