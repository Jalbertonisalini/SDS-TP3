#include "MutationStrategy.hpp"

#include <algorithm>
#include <cmath>

#include "CandidateValidator.hpp"

namespace {
// Interpolacion geometrica: natural para un parametro de escala (sigma), a
// diferencia de la lineal no favorece que la mayor parte del recorrido pase
// cerca del extremo grande.
double geometricLerp(double start, double end, double progress) {
    return start * std::pow(end / start, progress);
}
}  // namespace

void GaussianMutation::mutate(std::vector<ObstacleGene>& genome, const GenomeCodec& codec,
                              double progress, std::mt19937_64& rng) const {
    std::uniform_real_distribution<double> coin(0.0, 1.0);
    if (coin(rng) > individualRate_) {
        return;
    }

    const double sigmaPosition = geometricLerp(sigmaPositionStart_, sigmaPositionEnd_, progress);
    const double sigmaRadius = geometricLerp(sigmaRadiusStart_, sigmaRadiusEnd_, progress);
    std::normal_distribution<double> posNoise(0.0, sigmaPosition);
    std::normal_distribution<double> radiusNoise(0.0, sigmaRadius);
    constexpr int maxAttempts = 10;

    for (std::size_t i = 0; i < genome.size(); ++i) {
        if (coin(rng) > geneRate_) {
            continue;
        }

        const ObstacleGene original = genome[i];
        bool accepted = false;

        for (int attempt = 0; attempt < maxAttempts; ++attempt) {
            ObstacleGene candidate = original;
            candidate.r =
                std::clamp(candidate.r + radiusNoise(rng), codec.minRadius(), codec.maxRadius());
            const PositionBounds bounds = codec.positionBounds(static_cast<int>(i), candidate.r);
            candidate.x = std::clamp(candidate.x + posNoise(rng), bounds.xMin, bounds.xMax);
            candidate.y = std::clamp(candidate.y + posNoise(rng), bounds.yMin, bounds.yMax);
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
