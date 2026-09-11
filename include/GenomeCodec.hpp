#pragma once

#include <vector>

#include "Obstacle.hpp"
#include "ObstacleGene.hpp"

// Rango valido de un gen libre. Es una cota conservadora (calculada con el
// radio maximo posible) que usan los operadores geneticos para muestrear y
// clampear; la validez real de una configuracion la decide siempre
// isValidCandidate() sobre el genoma expandido, no estas cotas.
struct GeneBounds {
    double xMin, xMax;
    double yMin, yMax;
    double rMin, rMax;
};

// Codifica la reduccion del espacio de busqueda por simetria (o la ausencia
// de ella): mapea un genoma "libre" de tamano fijo a los K obstaculos reales
// de la mesa. El tamano del fenotipo (K) es siempre el mismo sea cual sea el
// valor de los genes -- cada implementacion restringe geneBounds() para que
// eso sea cierto por construccion, no por chequeo posterior.
class GenomeCodec {
public:
    virtual ~GenomeCodec() = default;

    virtual int freeCount() const = 0;
    virtual GeneBounds geneBounds(int index) const = 0;
    virtual std::vector<Obstacle> expand(const std::vector<ObstacleGene>& freeGenes) const = 0;
};

// Sin simetria: el genoma libre ES la lista de obstaculos.
class IdentityCodec : public GenomeCodec {
public:
    IdentityCodec(double length, double width, double minRadius, double maxRadius, int obstacleCount);

    int freeCount() const override { return obstacleCount_; }
    GeneBounds geneBounds(int index) const override;
    std::vector<Obstacle> expand(const std::vector<ObstacleGene>& freeGenes) const override;

private:
    double length_;
    double width_;
    double minRadius_;
    double maxRadius_;
    int obstacleCount_;
};

// Simetria especular respecto de y = W/2. Genes "pareados" viven
// estrictamente de un lado del eje y expanden a 2 obstaculos; si K es impar,
// el ultimo gen vive fijo sobre el eje y expande a 1.
class HorizontalSymmetryCodec : public GenomeCodec {
public:
    HorizontalSymmetryCodec(double length, double width, double minRadius, double maxRadius,
                            int obstacleCount);

    int freeCount() const override { return freeCount_; }
    GeneBounds geneBounds(int index) const override;
    std::vector<Obstacle> expand(const std::vector<ObstacleGene>& freeGenes) const override;

private:
    double length_;
    double width_;
    double minRadius_;
    double maxRadius_;
    int obstacleCount_;
    int pairedCount_;  // floor(K/2)
    bool hasAxisGene_;  // K impar
    int freeCount_;
};

// Simetria de 4 cuadrantes (espejo en x = L/2 e y = W/2). Genes de cuadrante
// viven estrictamente dentro del primer cuadrante y expanden a 4 obstaculos;
// si K mod 4 == 1, el ultimo gen es un obstaculo central fijo en (L/2, W/2)
// con solo el radio libre.
class FourQuadrantSymmetryCodec : public GenomeCodec {
public:
    FourQuadrantSymmetryCodec(double length, double width, double minRadius, double maxRadius,
                              int obstacleCount);

    int freeCount() const override { return freeCount_; }
    GeneBounds geneBounds(int index) const override;
    std::vector<Obstacle> expand(const std::vector<ObstacleGene>& freeGenes) const override;

private:
    double length_;
    double width_;
    double minRadius_;
    double maxRadius_;
    int obstacleCount_;
    int quadCount_;      // floor(K/4)
    bool hasCenterGene_;  // K mod 4 == 1
    int freeCount_;
};
