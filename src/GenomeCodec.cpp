#include "GenomeCodec.hpp"

namespace {
// Margen estricto respecto de un eje de simetria: un gen "pareado" o "de
// cuadrante" nunca puede acercarse tanto al eje que su propio espejo lo
// toque, sea cual sea el radio que le toque dentro de [minR, maxR].
constexpr double kAxisMargin = 1e-3;
}  // namespace

// ---------------------------------------------------------------------------
// IdentityCodec
// ---------------------------------------------------------------------------

IdentityCodec::IdentityCodec(double length, double width, double minRadius, double maxRadius,
                             int obstacleCount)
    : length_(length), width_(width), minRadius_(minRadius), maxRadius_(maxRadius),
      obstacleCount_(obstacleCount) {}

GeneBounds IdentityCodec::geneBounds(int) const {
    return {maxRadius_, length_ - maxRadius_, maxRadius_, width_ - maxRadius_, minRadius_,
            maxRadius_};
}

std::vector<Obstacle> IdentityCodec::expand(const std::vector<ObstacleGene>& freeGenes) const {
    std::vector<Obstacle> obstacles;
    obstacles.reserve(freeGenes.size());
    for (const ObstacleGene& gene : freeGenes) {
        obstacles.push_back({{gene.x, gene.y}, gene.r});
    }
    return obstacles;
}

// ---------------------------------------------------------------------------
// HorizontalSymmetryCodec
// ---------------------------------------------------------------------------

HorizontalSymmetryCodec::HorizontalSymmetryCodec(double length, double width, double minRadius,
                                                 double maxRadius, int obstacleCount)
    : length_(length), width_(width), minRadius_(minRadius), maxRadius_(maxRadius),
      obstacleCount_(obstacleCount), pairedCount_(obstacleCount / 2),
      hasAxisGene_(obstacleCount % 2 == 1),
      freeCount_(obstacleCount / 2 + (obstacleCount % 2)) {}

GeneBounds HorizontalSymmetryCodec::geneBounds(int index) const {
    const double xMin = maxRadius_;
    const double xMax = length_ - maxRadius_;
    if (hasAxisGene_ && index == pairedCount_) {
        // Gen de eje: vive fijo sobre y = W/2, solo x y r son libres.
        return {xMin, xMax, width_ / 2.0, width_ / 2.0, minRadius_, maxRadius_};
    }
    const double yMin = maxRadius_;
    const double yMax = width_ / 2.0 - maxRadius_ - kAxisMargin;
    return {xMin, xMax, yMin, yMax, minRadius_, maxRadius_};
}

std::vector<Obstacle> HorizontalSymmetryCodec::expand(
    const std::vector<ObstacleGene>& freeGenes) const {
    std::vector<Obstacle> obstacles;
    obstacles.reserve(static_cast<std::size_t>(obstacleCount_));
    for (int i = 0; i < pairedCount_; ++i) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(i)];
        obstacles.push_back({{gene.x, gene.y}, gene.r});
        obstacles.push_back({{gene.x, width_ - gene.y}, gene.r});
    }
    if (hasAxisGene_) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(pairedCount_)];
        obstacles.push_back({{gene.x, width_ / 2.0}, gene.r});
    }
    return obstacles;
}

// ---------------------------------------------------------------------------
// FourQuadrantSymmetryCodec
// ---------------------------------------------------------------------------

FourQuadrantSymmetryCodec::FourQuadrantSymmetryCodec(double length, double width,
                                                     double minRadius, double maxRadius,
                                                     int obstacleCount)
    : length_(length), width_(width), minRadius_(minRadius), maxRadius_(maxRadius),
      obstacleCount_(obstacleCount), quadCount_(obstacleCount / 4),
      hasCenterGene_(obstacleCount % 4 == 1),
      freeCount_(obstacleCount / 4 + (obstacleCount % 4 == 1 ? 1 : 0)) {}

GeneBounds FourQuadrantSymmetryCodec::geneBounds(int index) const {
    if (hasCenterGene_ && index == quadCount_) {
        // Gen central: fijo en (L/2, W/2), solo el radio es libre.
        return {length_ / 2.0, length_ / 2.0, width_ / 2.0, width_ / 2.0, minRadius_, maxRadius_};
    }
    const double xMin = maxRadius_;
    const double xMax = length_ / 2.0 - maxRadius_ - kAxisMargin;
    const double yMin = maxRadius_;
    const double yMax = width_ / 2.0 - maxRadius_ - kAxisMargin;
    return {xMin, xMax, yMin, yMax, minRadius_, maxRadius_};
}

std::vector<Obstacle> FourQuadrantSymmetryCodec::expand(
    const std::vector<ObstacleGene>& freeGenes) const {
    std::vector<Obstacle> obstacles;
    obstacles.reserve(static_cast<std::size_t>(obstacleCount_));
    for (int i = 0; i < quadCount_; ++i) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(i)];
        obstacles.push_back({{gene.x, gene.y}, gene.r});
        obstacles.push_back({{length_ - gene.x, gene.y}, gene.r});
        obstacles.push_back({{gene.x, width_ - gene.y}, gene.r});
        obstacles.push_back({{length_ - gene.x, width_ - gene.y}, gene.r});
    }
    if (hasCenterGene_) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(quadCount_)];
        obstacles.push_back({{length_ / 2.0, width_ / 2.0}, gene.r});
    }
    return obstacles;
}
