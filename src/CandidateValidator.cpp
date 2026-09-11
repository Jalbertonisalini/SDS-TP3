#include "CandidateValidator.hpp"

#include <cmath>

#include "ObstacleConfig.hpp"

namespace {

bool isPackingFeasible(const std::vector<Obstacle>& obstacles, const OptimizerConfig& config) {
    double occupied = 0.0;
    for (const Obstacle& o : obstacles) {
        occupied += M_PI * o.radius * o.radius;
    }
    const double freeArea = config.length * config.width - occupied;
    const double particleArea = M_PI * config.particleRadius * config.particleRadius;
    const double requiredArea =
        config.particleCount * particleArea / config.maxPackingDensity;
    return freeArea >= requiredArea;
}

// Distancia del centro de un obstaculo al segmento del arco (x = goalX,
// y en [W/2 - d/2, W/2 + d/2]).
double distanceToGoal(const Obstacle& o, double goalX, double width, double goalSize) {
    const double yLow = width / 2.0 - goalSize / 2.0;
    const double yHigh = width / 2.0 + goalSize / 2.0;
    const double dx = o.center.x - goalX;
    if (o.center.y >= yLow && o.center.y <= yHigh) {
        return std::abs(dx);
    }
    const double dy = o.center.y < yLow ? (yLow - o.center.y) : (o.center.y - yHigh);
    return std::sqrt(dx * dx + dy * dy);
}

bool respectsGoalClearance(const std::vector<Obstacle>& obstacles, const OptimizerConfig& config) {
    if (config.goalClearance <= 0.0) {
        return true;
    }
    for (const Obstacle& o : obstacles) {
        const double leftGap = distanceToGoal(o, 0.0, config.width, config.goalSize) - o.radius;
        const double rightGap =
            distanceToGoal(o, config.length, config.width, config.goalSize) - o.radius;
        if (leftGap < config.goalClearance || rightGap < config.goalClearance) {
            return false;
        }
    }
    return true;
}

}  // namespace

bool isValidCandidate(const std::vector<Obstacle>& obstacles, const OptimizerConfig& config) {
    if (!validateObstacles(obstacles, config.length, config.width).empty()) {
        return false;
    }
    if (!isPackingFeasible(obstacles, config)) {
        return false;
    }
    return respectsGoalClearance(obstacles, config);
}
