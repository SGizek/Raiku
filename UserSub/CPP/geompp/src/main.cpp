/**
 * geompp smoke-test / usage example.
 */
#include "geompp.hpp"
#include <cassert>
#include <iostream>

int main() {
    using namespace geompp;

    // Vec3 arithmetic
    Vec3 a{1.f, 2.f, 3.f};
    Vec3 b{4.f, 5.f, 6.f};
    std::cout << "dot(a,b) = " << a.dot(b) << "\n";     // 32
    std::cout << "cross(a,b) = " << a.cross(b) << "\n"; // (-3, 6, -3)

    // Ray-Sphere intersection
    Ray   ray{{0.f, 0.f, -5.f}, {0.f, 0.f, 1.f}};
    Sphere sphere{{0.f, 0.f, 0.f}, 1.f};
    auto hit = sphere.intersect(ray);
    assert(hit.has_value());
    std::cout << "Ray hits sphere at t = " << *hit << "\n"; // ~4.0

    // Ray-AABB
    AABB box{{-1.f,-1.f,-1.f}, {1.f,1.f,1.f}};
    auto box_hit = box.intersect(ray);
    assert(box_hit.has_value());
    std::cout << "Ray hits AABB at t = " << *box_hit << "\n";

    std::cout << "All geompp tests passed.\n";
    return 0;
}
