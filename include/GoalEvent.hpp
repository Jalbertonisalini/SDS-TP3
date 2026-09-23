#pragma once

// Primer gol de una particula: el instante exacto en que choca con un arco
// estando fresca. Es un evento del sistema (cambio de estado Fresh -> Used),
// no un observable: F_u(t), t90 y la cantidad de goles se calculan a partir de
// estos eventos en postproceso.
struct GoalEvent {
    double time;
    int particle;
};
