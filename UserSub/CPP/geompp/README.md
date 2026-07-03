# geompp

Header-only 3D geometry primitives for C++17. Zero dependencies.

Provides: `Vec3`, `Ray`, `AABB`, `Sphere`, `Plane` with intersection tests.

## Installation

```bash
raiku install geompp
```

## Usage

```cpp
#include "geompp.hpp"
using namespace geompp;

Ray ray{{0,0,-5}, {0,0,1}};
Sphere s{{0,0,0}, 1.0f};
auto hit = s.intersect(ray);
if (hit) std::cout << "Hit at t=" << *hit << "\n";
```

## License

MIT
