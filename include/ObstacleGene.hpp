#pragma once

// Gen libre del genoma de la busqueda genetica: una terna (x, y, r) antes de
// pasar por el GenomeCodec que la expande a los obstaculos reales de la mesa.
struct ObstacleGene {
    double x = 0.0;
    double y = 0.0;
    double r = 0.0;
};
