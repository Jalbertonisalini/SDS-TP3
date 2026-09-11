#pragma once

#include <random>
#include <vector>

#include "GenomeCodec.hpp"
#include "ObstacleGene.hpp"
#include "OptimizerConfig.hpp"

class MutationStrategy {
public:
    virtual ~MutationStrategy() = default;
    virtual void mutate(std::vector<ObstacleGene>& genome, const GenomeCodec& codec,
                        std::mt19937_64& rng) const = 0;
};

// Con probabilidad individualRate, el individuo muta; si muta, cada gen se
// perturba con ruido gaussiano independiente con probabilidad geneRate. Si
// el resultado expandido no es valido, se descarta el intento (hasta 10
// reintentos) y el gen queda como estaba.
class GaussianMutation : public MutationStrategy {
public:
    GaussianMutation(OptimizerConfig config, double individualRate, double geneRate,
                     double sigmaPosition, double sigmaRadius)
        : config_(config),
          individualRate_(individualRate),
          geneRate_(geneRate),
          sigmaPosition_(sigmaPosition),
          sigmaRadius_(sigmaRadius) {}

    void mutate(std::vector<ObstacleGene>& genome, const GenomeCodec& codec,
               std::mt19937_64& rng) const override;

private:
    OptimizerConfig config_;
    double individualRate_;
    double geneRate_;
    double sigmaPosition_;
    double sigmaRadius_;
};
