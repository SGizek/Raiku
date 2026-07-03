# blazing-vec

Zero-cost SIMD-friendly vector operations for Rust. Provides generic `Vec2`, `Vec3`, and `Vec4` types.

## Installation

```bash
raiku install blazing-vec
```

## Usage

```rust
use blazing_vec::Vec3;

let a = Vec3::new(1.0f32, 2.0, 3.0);
let b = Vec3::new(4.0f32, 5.0, 6.0);

println!("{}", a.dot(b));          // 32.0
println!("{:?}", a.cross(b));      // Vec3 { x: -3.0, y: 6.0, z: -3.0 }
println!("{:?}", a.normalise());   // unit vector
```

## License

MIT
