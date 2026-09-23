#include "OutputWriter.hpp"

#include <ios>
#include <stdexcept>

OutputWriter::OutputWriter(const std::string &goalsPath, const std::string &trajectoryPath,
                           bool noOutput)
{
    if (noOutput)
    {
        return;
    }

    goals_.open(goalsPath);
    if (!goals_)
    {
        throw std::runtime_error("No se pudo abrir el archivo de salida: " + goalsPath);
    }
    goals_ << "Time,ID\n";
    goals_.setf(std::ios::fixed);
    goals_.precision(6);

    if (!trajectoryPath.empty())
    {
        trajectory_.open(trajectoryPath);
        if (!trajectory_)
        {
            throw std::runtime_error("No se pudo abrir el archivo de trayectoria: " + trajectoryPath);
        }
        trajectory_ << "Time,ID,X,Y,VX,VY,State\n";
        trajectory_.setf(std::ios::fixed);
        trajectory_.precision(6);
    }
}

void OutputWriter::writeGoals(const std::vector<GoalEvent> &goals)
{
    if (!goals_.is_open())
    {
        return;
    }
    for (const GoalEvent &goal : goals)
    {
        goals_ << goal.time << ',' << goal.particle << '\n';
    }
}

void OutputWriter::writeTrajectory(double time, const std::vector<Particle> &particles)
{
    if (!trajectory_.is_open())
    {
        return;
    }
    for (std::size_t i = 0; i < particles.size(); ++i)
    {
        const Particle &p = particles[i];
        trajectory_ << time << ',' << i << ',' << p.position.x << ',' << p.position.y << ','
                    << p.velocity.x << ',' << p.velocity.y << ','
                    << static_cast<int>(p.state) << '\n';
    }
}
