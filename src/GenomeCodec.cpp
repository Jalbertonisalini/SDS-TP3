#include "GenomeCodec.hpp"

#include <algorithm>
#include <cmath>

namespace {
// Margen estricto respecto de un eje de simetria: un gen "pareado" o "de
// cuadrante" nunca puede acercarse tanto al eje que su propio espejo lo
// toque, sea cual sea el radio que le toque dentro de [minR, maxR].
constexpr double kAxisMargin = 1e-3;

// N circulos de radio `radio` que van de `radio` a `span - radio`, tocando
// AMBOS extremos exacto (reparte el paso real, siempre >= al minimo, en vez
// de dejar un resto sin cubrir al final -- ese resto es justo el canal
// angosto que aprendimos a evitar).
std::vector<double> posicionesFlush(double span, double radio, double pasoMinimo) {
    const int n = static_cast<int>(std::floor((span - 2.0 * radio) / pasoMinimo)) + 1;
    if (n <= 1) {
        return {span / 2.0};
    }
    const double paso = (span - 2.0 * radio) / (n - 1);
    std::vector<double> pos(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        pos[static_cast<std::size_t>(i)] = radio + i * paso;
    }
    return pos;
}
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

double HorizontalSymmetryCodec::radiusCeiling(int index) const {
    if (hasAxisGene_ && index == pairedCount_) {
        // Gen de eje: fijo en y = W/2, sin espejo que lo limite. El techo
        // real es la contencion en el dominio (isValidCandidate se encarga
        // del resto, incluida la restriccion (ii) via isPackingFeasible).
        return std::min(length_, width_) / 2.0;
    }
    return maxRadius_;
}

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
    // Acepta genomas parciales (freeGenes.size() < freeCount()): el sampler
    // secuencial de Optimizer::randomIndividual valida un gen a la vez, sin
    // haber generado todavia el resto.
    std::vector<Obstacle> obstacles;
    obstacles.reserve(static_cast<std::size_t>(obstacleCount_));
    const int paired = std::min(pairedCount_, static_cast<int>(freeGenes.size()));
    for (int i = 0; i < paired; ++i) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(i)];
        obstacles.push_back({{gene.x, gene.y}, gene.r});
        obstacles.push_back({{gene.x, width_ - gene.y}, gene.r});
    }
    if (hasAxisGene_ && static_cast<int>(freeGenes.size()) > pairedCount_) {
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

double FourQuadrantSymmetryCodec::radiusCeiling(int index) const {
    if (hasCenterGene_ && index == quadCount_) {
        // Gen central: sin espejo que lo limite (ver comentario en
        // positionBounds). El techo real es la contencion en el dominio;
        // isValidCandidate se encarga del resto (overlap con los otros
        // obstaculos, restriccion (ii) via isPackingFeasible).
        return std::min(length_, width_) / 2.0;
    }
    return maxRadius_;
}

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
    // Acepta genomas parciales (freeGenes.size() < freeCount()): el sampler
    // secuencial de Optimizer::randomIndividual valida un gen a la vez, sin
    // haber generado todavia el resto.
    std::vector<Obstacle> obstacles;
    obstacles.reserve(static_cast<std::size_t>(obstacleCount_));
    const int quads = std::min(quadCount_, static_cast<int>(freeGenes.size()));
    for (int i = 0; i < quads; ++i) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(i)];
        obstacles.push_back({{gene.x, gene.y}, gene.r});
        obstacles.push_back({{length_ - gene.x, gene.y}, gene.r});
        obstacles.push_back({{gene.x, width_ - gene.y}, gene.r});
        obstacles.push_back({{length_ - gene.x, width_ - gene.y}, gene.r});
    }
    if (hasCenterGene_ && static_cast<int>(freeGenes.size()) > quadCount_) {
        const ObstacleGene& gene = freeGenes[static_cast<std::size_t>(quadCount_)];
        obstacles.push_back({{length_ / 2.0, width_ / 2.0}, gene.r});
    }
    return obstacles;
}

// ---------------------------------------------------------------------------
// WallProfileCodec
// ---------------------------------------------------------------------------

WallProfileCodec::WallProfileCodec(double length, double width, int controlPoints,
                                   double minDepth, double maxDepth, double wallGrain)
    : length_(length), width_(width), controlPoints_(controlPoints), minDepth_(minDepth),
      maxDepth_(maxDepth), wallGrain_(wallGrain) {}

PositionBounds WallProfileCodec::positionBounds(int, double) const {
    // x,y del gen no se usan (expand() solo lee .r, reinterpretado como
    // profundidad); devolver un punto fijo hace que esos campos queden
    // congelados en 0, sampling/mutacion no pierden tiempo perturbandolos.
    return {0.0, 0.0, 0.0, 0.0};
}

std::vector<Obstacle> WallProfileCodec::expand(const std::vector<ObstacleGene>& freeGenes) const {
    const int n = static_cast<int>(freeGenes.size());
    if (n == 0) {
        return {};
    }
    // Puntos de control evenly-spaced en y in [0, W/2] (n==1: profundidad
    // constante en toda la mesa).
    const double halfWidth = width_ / 2.0;

    auto profundidadEn = [&](double y) {
        // Espeja y a [0, W/2]: el perfil es simetrico respecto de y = W/2.
        const double yFold = std::min(y, width_ - y);
        if (n == 1) {
            return freeGenes[0].r;
        }
        const double posicion = yFold / halfWidth * (n - 1);  // in [0, n-1]
        const int idx = std::min(n - 2, static_cast<int>(std::floor(posicion)));
        const double frac = posicion - idx;
        const double d0 = freeGenes[static_cast<std::size_t>(idx)].r;
        const double d1 = freeGenes[static_cast<std::size_t>(idx + 1)].r;
        return d0 + frac * (d1 - d0);
    };

    const double stepMin = 2.0 * wallGrain_ + 1e-4;
    const std::vector<double> ys = posicionesFlush(width_, wallGrain_, stepMin);

    std::vector<Obstacle> obstacles;
    for (double y : ys) {
        const double depth =
            std::clamp(profundidadEn(y), wallGrain_, length_ / 2.0 - wallGrain_);
        const double span = length_ - 2.0 * depth;
        if (span < 2.0 * wallGrain_) {
            continue;  // fila degenerada: las dos camaras se tocarian
        }
        for (double x : posicionesFlush(span, wallGrain_, stepMin)) {
            obstacles.push_back({{depth + x, y}, wallGrain_});
        }
    }
    return obstacles;
    return obstacles;
}
