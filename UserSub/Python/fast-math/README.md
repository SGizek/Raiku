# fast-math

High-performance math utilities for numerical computing — pure Python, no mandatory dependencies.

## Features

- Vector arithmetic: dot product, cross product, normalisation, magnitude
- Scalar helpers: `clamp`, `lerp`, `sign`, `is_close`
- Statistics: `mean`, `variance`, `std_dev`

## Installation

```bash
raiku install fast-math
```

## Usage

```python
from fast_math import dot, normalise, cross3, clamp, lerp

print(dot([1, 2, 3], [4, 5, 6]))      # 32
print(normalise([3.0, 4.0]))           # [0.6, 0.8]
print(cross3([1,0,0], [0,1,0]))        # [0, 0, 1]
print(clamp(15.0, 0.0, 10.0))          # 10.0
print(lerp(0.0, 100.0, 0.25))          # 25.0
```

## License

MIT
