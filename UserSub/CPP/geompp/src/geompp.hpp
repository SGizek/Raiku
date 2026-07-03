/**
 * geompp.hpp — Header-only 3D geometry primitives for C++17.
 *
 * Provides: Vec3, Ray, AABB, Sphere, Plane, and basic intersection tests.
 * Requires C++17 or later.
 */
#pragma once

#include <cmath>
#include <optional>
#include <ostream>
#include <stdexcept>
#include <string>

namespace geompp {

// ---------------------------------------------------------------------------
// Vec3
// ---------------------------------------------------------------------------

struct Vec3 {
    float x{0.f}, y{0.f}, z{0.f};

    constexpr Vec3() = default;
    constexpr Vec3(float x, float y, float z) : x{x}, y{y}, z{z} {}

    [[nodiscard]] constexpr Vec3 operator+(const Vec3& o) const noexcept {
        return {x + o.x, y + o.y, z + o.z};
    }
    [[nodiscard]] constexpr Vec3 operator-(const Vec3& o) const noexcept {
        return {x - o.x, y - o.y, z - o.z};
    }
    [[nodiscard]] constexpr Vec3 operator*(float s) const noexcept {
        return {x * s, y * s, z * s};
    }
    [[nodiscard]] constexpr Vec3 operator-() const noexcept {
        return {-x, -y, -z};
    }

    [[nodiscard]] constexpr float dot(const Vec3& o) const noexcept {
        return x * o.x + y * o.y + z * o.z;
    }

    [[nodiscard]] constexpr Vec3 cross(const Vec3& o) const noexcept {
        return {y * o.z - z * o.y,
                z * o.x - x * o.z,
                x * o.y - y * o.x};
    }

    [[nodiscard]] float length() const noexcept {
        return std::sqrt(x * x + y * y + z * z);
    }

    [[nodiscard]] Vec3 normalised() const {
        const float len = length();
        if (len < 1e-8f) throw std::runtime_error("Cannot normalise zero vector");
        return *this * (1.f / len);
    }

    [[nodiscard]] Vec3 lerp(const Vec3& to, float t) const noexcept {
        return *this + (to - *this) * t;
    }

    friend std::ostream& operator<<(std::ostream& os, const Vec3& v) {
        return os << "Vec3(" << v.x << ", " << v.y << ", " << v.z << ")";
    }
};

// ---------------------------------------------------------------------------
// Ray
// ---------------------------------------------------------------------------

struct Ray {
    Vec3 origin;
    Vec3 direction;   // Should be normalised by the user

    constexpr Ray(Vec3 origin, Vec3 direction)
        : origin{origin}, direction{direction} {}

    [[nodiscard]] constexpr Vec3 at(float t) const noexcept {
        return origin + direction * t;
    }
};

// ---------------------------------------------------------------------------
// AABB (Axis-Aligned Bounding Box)
// ---------------------------------------------------------------------------

struct AABB {
    Vec3 min;
    Vec3 max;

    constexpr AABB(Vec3 min, Vec3 max) : min{min}, max{max} {}

    /// Slab method ray-AABB intersection. Returns t of hit or nullopt.
    [[nodiscard]] std::optional<float> intersect(const Ray& ray) const noexcept {
        float tmin = 0.f, tmax = 1e38f;
        const float* origin = &ray.origin.x;
        const float* dir    = &ray.direction.x;
        const float* lo     = &min.x;
        const float* hi     = &max.x;

        for (int i = 0; i < 3; ++i) {
            if (std::abs(dir[i]) < 1e-8f) {
                if (origin[i] < lo[i] || origin[i] > hi[i]) return std::nullopt;
            } else {
                float t1 = (lo[i] - origin[i]) / dir[i];
                float t2 = (hi[i] - origin[i]) / dir[i];
                if (t1 > t2) std::swap(t1, t2);
                tmin = std::max(tmin, t1);
                tmax = std::min(tmax, t2);
                if (tmin > tmax) return std::nullopt;
            }
        }
        return tmin;
    }

    [[nodiscard]] bool contains(const Vec3& p) const noexcept {
        return p.x >= min.x && p.x <= max.x &&
               p.y >= min.y && p.y <= max.y &&
               p.z >= min.z && p.z <= max.z;
    }
};

// ---------------------------------------------------------------------------
// Sphere
// ---------------------------------------------------------------------------

struct Sphere {
    Vec3  centre;
    float radius;

    constexpr Sphere(Vec3 centre, float radius)
        : centre{centre}, radius{radius} {}

    /// Analytic ray-sphere intersection. Returns smallest positive t or nullopt.
    [[nodiscard]] std::optional<float> intersect(const Ray& ray) const noexcept {
        const Vec3  oc = ray.origin - centre;
        const float a  = ray.direction.dot(ray.direction);
        const float b  = 2.f * oc.dot(ray.direction);
        const float c  = oc.dot(oc) - radius * radius;
        const float discriminant = b * b - 4.f * a * c;
        if (discriminant < 0.f) return std::nullopt;
        const float sqrtD = std::sqrt(discriminant);
        const float t1 = (-b - sqrtD) / (2.f * a);
        const float t2 = (-b + sqrtD) / (2.f * a);
        if (t1 > 1e-4f) return t1;
        if (t2 > 1e-4f) return t2;
        return std::nullopt;
    }
};

// ---------------------------------------------------------------------------
// Plane (normal form: n·x = d)
// ---------------------------------------------------------------------------

struct Plane {
    Vec3  normal;  // Unit normal
    float d;       // Distance from origin

    Plane(Vec3 normal, float d) : normal{normal.normalised()}, d{d} {}

    /// Ray-plane intersection. Returns t or nullopt if parallel.
    [[nodiscard]] std::optional<float> intersect(const Ray& ray) const noexcept {
        const float denom = normal.dot(ray.direction);
        if (std::abs(denom) < 1e-6f) return std::nullopt;
        const float t = (d - normal.dot(ray.origin)) / denom;
        if (t < 0.f) return std::nullopt;
        return t;
    }
};

} // namespace geompp
