#pragma once

#include <random>
#include <vector>

#include "Individual.hpp"

class SelectionStrategy {
public:
    virtual ~SelectionStrategy() = default;
    virtual const Individual& select(const std::vector<Individual>& population,
                                      std::mt19937_64& rng) const = 0;
};

// Selecciona el mejor (menor fitness) de k individuos elegidos al azar.
class TournamentSelection : public SelectionStrategy {
public:
    explicit TournamentSelection(int tournamentSize) : tournamentSize_(tournamentSize) {}

    const Individual& select(const std::vector<Individual>& population,
                             std::mt19937_64& rng) const override {
        std::uniform_int_distribution<std::size_t> dist(0, population.size() - 1);
        const Individual* best = &population[dist(rng)];
        for (int i = 1; i < tournamentSize_; ++i) {
            const Individual& candidate = population[dist(rng)];
            if (candidate.fitness < best->fitness) {
                best = &candidate;
            }
        }
        return *best;
    }

private:
    int tournamentSize_;
};
