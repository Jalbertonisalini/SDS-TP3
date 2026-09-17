#pragma once

#include <vector>

#include "Obstacle.hpp"
#include "ObstacleGene.hpp"

// Rango valido de x,y para un gen, dado el radio que ya se le asigno. Depende
// del radio (no de una cota fija) para no desperdiciar muestreo: un gen con
// radio chico tiene mucho mas margen que uno con radio grande, sobre todo en
// los codecs con simetria.
struct PositionBounds {
    double xMin, xMax;
    double yMin, yMax;
};

// Codifica la reduccion del espacio de busqueda por simetria (o la ausencia
// de ella): mapea un genoma "libre" de tamano fijo a los K obstaculos reales
// de la mesa. El tamano del fenotipo (K) es siempre el mismo sea cual sea el
// valor de los genes -- cada implementacion restringe positionBounds() para
// que eso sea cierto por construccion, no por chequeo posterior.
class GenomeCodec {
public:
    virtual ~GenomeCodec() = default;

    virtual int freeCount() const = 0;
    virtual double minRadius() const = 0;
    virtual double maxRadius() const = 0;
    // Techo de radio efectivo para samplear/mutar el gen `index`. Por
    // default coincide con maxRadius(); los codecs con un gen sin espejo
    // (eje/centro, sin restriccion de solapamiento contra si mismo) lo
    // overridean para no caparlo antes de que isPackingFeasible() (el
    // filtro real de la restriccion (ii)) entre en juego.
    virtual double radiusCeiling(int /*index*/) const { return maxRadius(); }
    // Cotas de x,y para el gen `index`, dado que su radio ya vale `radius`.
    virtual PositionBounds positionBounds(int index, double radius) const = 0;
    virtual std::vector<Obstacle> expand(const std::vector<ObstacleGene>& freeGenes) const = 0;
};

// Sin simetria: el genoma libre ES la lista de obstaculos.
class IdentityCodec : public GenomeCodec {
public:
    IdentityCodec(double length, double width, double minRadius, double maxRadius, int obstacleCount);

    int freeCount() const override { return obstacleCount_; }
    double minRadius() const override { return minRadius_; }
    double maxRadius() const override { return maxRadius_; }
    PositionBounds positionBounds(int index, double radius) const override;
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
    double minRadius() const override { return minRadius_; }
    double maxRadius() const override { return maxRadius_; }
    double radiusCeiling(int index) const override;
    PositionBounds positionBounds(int index, double radius) const override;
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
// con solo el radio libre. Los genes de cuadrante tienen un techo geometrico
// en el radio cerca de W/4 (o L/4): mas alla, el propio espejo se solapa
// consigo mismo sin importar --max-radius. El gen central no tiene ese techo.
class FourQuadrantSymmetryCodec : public GenomeCodec {
public:
    FourQuadrantSymmetryCodec(double length, double width, double minRadius, double maxRadius,
                              int obstacleCount);

    int freeCount() const override { return freeCount_; }
    double minRadius() const override { return minRadius_; }
    double maxRadius() const override { return maxRadius_; }
    double radiusCeiling(int index) const override;
    PositionBounds positionBounds(int index, double radius) const override;
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

// Fuerza al GA a buscar unicamente dentro de la topologia "muro solido que
// parte la mesa en dos camaras" (la que goleamos empiricamente): el genoma
// libre no son circulos independientes, son N profundidades de un perfil de
// muro en puntos de control fijos en y, espejado en y = W/2 (arriba/abajo) y
// en x = L/2 (las dos camaras comparten perfil). El campo `r` de cada gen se
// reinterpreta como "profundidad" en ese punto de control -- por eso
// minRadius()/maxRadius() son en realidad las cotas de profundidad, lo que
// deja reusar sampling/mutacion/cruza tal cual (ya clampean `.r` entre esas
// cotas). expand() rasteriza el perfil interpolado linealmente entre puntos
// de control en una grilla de circulos chicos (mismo radio para todos, fijo,
// no es parte del genoma) que llega exacta a las 4 paredes, sin canales.
class WallProfileCodec : public GenomeCodec {
public:
    WallProfileCodec(double length, double width, int controlPoints, double minDepth,
                     double maxDepth, double wallGrain);

    int freeCount() const override { return controlPoints_; }
    double minRadius() const override { return minDepth_; }
    double maxRadius() const override { return maxDepth_; }
    PositionBounds positionBounds(int index, double depth) const override;
    std::vector<Obstacle> expand(const std::vector<ObstacleGene>& freeGenes) const override;

private:
    double length_;
    double width_;
    int controlPoints_;   // N puntos de control en y in [0, W/2]
    double minDepth_;
    double maxDepth_;
    double wallGrain_;    // radio (fijo) de los circulos chicos que arman el muro
};
