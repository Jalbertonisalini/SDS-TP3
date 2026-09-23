#pragma once

#include <random>
#include <vector>

#include "GenomeCodec.hpp"
#include "ObstacleGene.hpp"
#include "OptimizerConfig.hpp"

class MutationStrategy {
public:
    virtual ~MutationStrategy() = default;
    // progress in [0,1]: 0 en la primera generacion, 1 en la ultima. Las
    // implementaciones lo usan para variar la intensidad de la mutacion
    // (explorar al principio, explotar al final).
    virtual void mutate(std::vector<ObstacleGene>& genome, const GenomeCodec& codec,
                        double progress, std::mt19937_64& rng) const = 0;
};

// Con probabilidad individualRate, el individuo muta; si muta, cada gen se
// perturba con ruido gaussiano independiente con probabilidad geneRate. El
// sigma (posicion y radio) decae geometricamente de sigmaStart (progress=0)
// a sigmaEnd (progress=1): arranca explorando pasos grandes y termina
// afinando el ajuste fino cerca del optimo encontrado. Si el resultado
// expandido no es valido, se descarta el intento (hasta 10 reintentos) y el
// gen queda como estaba.
class GaussianMutation : public MutationStrategy {
public:
    GaussianMutation(OptimizerConfig config, double individualRate, double geneRate,
                     double sigmaPositionStart, double sigmaPositionEnd,
                     double sigmaRadiusStart, double sigmaRadiusEnd)
        : config_(config),
          individualRate_(individualRate),
          geneRate_(geneRate),
          sigmaPositionStart_(sigmaPositionStart),
          sigmaPositionEnd_(sigmaPositionEnd),
          sigmaRadiusStart_(sigmaRadiusStart),
          sigmaRadiusEnd_(sigmaRadiusEnd) {}

    void mutate(std::vector<ObstacleGene>& genome, const GenomeCodec& codec, double progress,
               std::mt19937_64& rng) const override;

private:
    OptimizerConfig config_;
    double individualRate_;
    double geneRate_;
    double sigmaPositionStart_;
    double sigmaPositionEnd_;
    double sigmaRadiusStart_;
    double sigmaRadiusEnd_;
};
