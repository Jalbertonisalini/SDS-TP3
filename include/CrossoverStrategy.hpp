#pragma once

#include <random>
#include <vector>

#include "GenomeCodec.hpp"
#include "ObstacleGene.hpp"
#include "OptimizerConfig.hpp"

class CrossoverStrategy {
public:
    virtual ~CrossoverStrategy() = default;
    virtual std::vector<ObstacleGene> cross(const std::vector<ObstacleGene>& parentA,
                                             const std::vector<ObstacleGene>& parentB,
                                             const GenomeCodec& codec,
                                             std::mt19937_64& rng) const = 0;
};

// Blend crossover (BLX-alpha): por cada gen, sortea un valor en el intervalo
// extendido [min(a,b) - alpha*rango, max(a,b) + alpha*rango] (recortado a
// las cotas del gen), gen a gen e independientemente para x, y, r. Reintenta
// hasta 10 veces si el hijo expandido no es una configuracion valida; si
// ninguno lo es, hereda directo del padre A.
class BlxAlphaCrossover : public CrossoverStrategy {
public:
    BlxAlphaCrossover(OptimizerConfig config, double alpha) : config_(config), alpha_(alpha) {}

    std::vector<ObstacleGene> cross(const std::vector<ObstacleGene>& parentA,
                                     const std::vector<ObstacleGene>& parentB,
                                     const GenomeCodec& codec,
                                     std::mt19937_64& rng) const override;

private:
    double blend(double a, double b, double lo, double hi, std::mt19937_64& rng) const;

    OptimizerConfig config_;
    double alpha_;
};
