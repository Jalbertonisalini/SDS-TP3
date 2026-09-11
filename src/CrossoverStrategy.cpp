#include "CrossoverStrategy.hpp"

#include <algorithm>

#include "CandidateValidator.hpp"

double BlxAlphaCrossover::blend(double a, double b, double lo, double hi,
                                std::mt19937_64& rng) const {
    const double lower = std::min(a, b);
    const double upper = std::max(a, b);
    const double range = upper - lower;

    double extendedLow = std::max(lower - alpha_ * range, lo);
    double extendedHigh = std::min(upper + alpha_ * range, hi);
    if (extendedHigh <= extendedLow) {
        return std::clamp((a + b) / 2.0, lo, hi);
    }

    std::uniform_real_distribution<double> dist(extendedLow, extendedHigh);
    return dist(rng);
}

std::vector<ObstacleGene> BlxAlphaCrossover::cross(const std::vector<ObstacleGene>& parentA,
                                                    const std::vector<ObstacleGene>& parentB,
                                                    const GenomeCodec& codec,
                                                    std::mt19937_64& rng) const {
    constexpr int maxAttempts = 10;

    for (int attempt = 0; attempt < maxAttempts; ++attempt) {
        std::vector<ObstacleGene> child;
        child.reserve(parentA.size());

        for (std::size_t i = 0; i < parentA.size(); ++i) {
            ObstacleGene gene;
            gene.r = blend(parentA[i].r, parentB[i].r, codec.minRadius(), codec.maxRadius(), rng);
            const PositionBounds pos = codec.positionBounds(static_cast<int>(i), gene.r);
            gene.x = blend(parentA[i].x, parentB[i].x, pos.xMin, pos.xMax, rng);
            gene.y = blend(parentA[i].y, parentB[i].y, pos.yMin, pos.yMax, rng);
            child.push_back(gene);
        }

        if (isValidCandidate(codec.expand(child), config_)) {
            return child;
        }
    }

    return parentA;  // Cruza fallida: hereda directo del padre A.
}
