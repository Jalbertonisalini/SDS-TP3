#pragma once

#include <cmath>

// Vector 2D minimo: solo lo que usa el motor.
struct Vec2 {
    double x = 0.0;
    double y = 0.0;

    Vec2 operator+(const Vec2& o) const { return {x + o.x, y + o.y}; }
    Vec2 operator-(const Vec2& o) const { return {x - o.x, y - o.y}; }
    Vec2 operator*(double s) const { return {x * s, y * s}; }

    Vec2& operator+=(const Vec2& o) {
        x += o.x;
        y += o.y;
        return *this;
    }

    double dot(const Vec2& o) const { return x * o.x + y * o.y; }
    double norm2() const { return x * x + y * y; }
    double norm() const { return std::sqrt(norm2()); }
};
