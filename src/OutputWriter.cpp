#include "OutputWriter.hpp"

#include <ios>
#include <stdexcept>

OutputWriter::OutputWriter(const std::string &seriesPath, const std::string &trajectoryPath,
                           bool noOutput)
{
    if (noOutput)
    {
        return;
    }

    series_.open(seriesPath);
    if (!series_)
    {
        throw std::runtime_error("No se pudo abrir el archivo de salida: " + seriesPath);
    }
    series_ << "Time,Goals,UsedFraction,MSD\n";
    series_.setf(std::ios::fixed);
    series_.precision(6);

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

void OutputWriter::writeSeries(double time, int goals, double usedFraction,
                               double meanSquaredDisplacement)
{
    if (!series_.is_open())
    {
        return;
    }
    series_ << time << ',' << goals << ',' << usedFraction << ',' << meanSquaredDisplacement << '\n';
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
