#include "GenomeCodec.hpp"

#include <algorithm>

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

PositionBounds IdentityCodec::positionBounds(int, double radius) const {
    // std::max evita cotas invertidas si radius es mayor a medio dominio:
    // colapsan a un punto en vez de [xMin > xMax] (UB en clamp/uniform_real).
    return {radius, std::max(radius, length_ - radius), radius, std::max(radius, width_ - radius)};
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

PositionBounds HorizontalSymmetryCodec::positionBounds(int index, double radius) const {
    const double xMin = radius;
    const double xMax = std::max(xMin, length_ - radius);
    if (hasAxisGene_ && index == pairedCount_) {
        // Gen de eje: vive fijo sobre y = W/2, solo x y r son libres.
        return {xMin, xMax, width_ / 2.0, width_ / 2.0};
    }
    const double yMin = radius;
    // Si el radio ya no entra en la mitad de la mesa, colapsa a un punto: el
    // espejo va a solaparse consigo mismo y isValidCandidate lo va a
    // rechazar, pero las cotas en si nunca quedan invertidas.
    const double yMax = std::max(yMin, width_ / 2.0 - radius - kAxisMargin);
    return {xMin, xMax, yMin, yMax};
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

PositionBounds FourQuadrantSymmetryCodec::positionBounds(int index, double radius) const {
    if (hasCenterGene_ && index == quadCount_) {
        // Gen central: fijo en (L/2, W/2), solo el radio es libre. Sin
        // espejo cercano: no tiene el techo geometrico de los genes de
        // cuadrante, puede crecer hasta donde lo permitan el dominio y el
        // resto de los obstaculos.
        return {length_ / 2.0, length_ / 2.0, width_ / 2.0, width_ / 2.0};
    }
    // Techo geometrico: si radius > ~min(L,W)/4, el propio espejo se
    // solapa consigo mismo. Las cotas colapsan a un punto (nunca se
    // invierten) y isValidCandidate rechaza el resto.
    const double xMin = radius;
    const double xMax = std::max(xMin, length_ / 2.0 - radius - kAxisMargin);
    const double yMin = radius;
    const double yMax = std::max(yMin, width_ / 2.0 - radius - kAxisMargin);
    return {xMin, xMax, yMin, yMax};
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
