#include "MutationStrategy.hpp"

#include <algorithm>

#include "CandidateValidator.hpp"

void GaussianMutation::mutate(std::vector<ObstacleGene>& genome, const GenomeCodec& codec,
                              std::mt19937_64& rng) const {
    std::uniform_real_distribution<double> coin(0.0, 1.0);
    if (coin(rng) > individualRate_) {
        return;
    }

    std::normal_distribution<double> posNoise(0.0, sigmaPosition_);
    std::normal_distribution<double> radiusNoise(0.0, sigmaRadius_);
    constexpr int maxAttempts = 10;

    for (std::size_t i = 0; i < genome.size(); ++i) {
        if (coin(rng) > geneRate_) {
            continue;
        }

        const ObstacleGene original = genome[i];
        const GeneBounds bounds = codec.geneBounds(static_cast<int>(i));
        bool accepted = false;

        for (int attempt = 0; attempt < maxAttempts; ++attempt) {
            ObstacleGene candidate = original;
            candidate.x = std::clamp(candidate.x + posNoise(rng), bounds.xMin, bounds.xMax);
            candidate.y = std::clamp(candidate.y + posNoise(rng), bounds.yMin, bounds.yMax);
            candidate.r = std::clamp(candidate.r + radiusNoise(rng), bounds.rMin, bounds.rMax);
            genome[i] = candidate;

            if (isValidCandidate(codec.expand(genome), config_)) {
                accepted = true;
                break;
            }
        }

        if (!accepted) {
            genome[i] = original;
        }
    }
}
