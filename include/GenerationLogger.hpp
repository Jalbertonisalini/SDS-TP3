#pragma once

#include <fstream>
#include <ios>
#include <stdexcept>
#include <string>

// Log de convergencia de una corrida del GA: una fila por generacion, para
// poder graficar y comparar variantes (benchmark de piezas).
class GenerationLogger {
public:
    explicit GenerationLogger(const std::string& path) {
        stream_.open(path);
        if (!stream_) {
            throw std::runtime_error("No se pudo abrir el log de convergencia: " + path);
        }
        stream_ << "generacion,mejor_fitness,promedio_fitness,peor_fitness,tiempo_s\n";
        stream_.setf(std::ios::fixed);
        stream_.precision(6);
    }

    void log(int generation, double best, double average, double worst, double elapsedSeconds) {
        stream_ << generation << ',' << best << ',' << average << ',' << worst << ','
                << elapsedSeconds << '\n';
    }

private:
    std::ofstream stream_;
};
