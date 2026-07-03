/// blazing-vec: Zero-cost SIMD-friendly vector operations for Rust.
///
/// Provides generic Vec2, Vec3, and Vec4 types with common linear-algebra
/// operations.  All operations compile down to scalar code that LLVM can
/// auto-vectorise.

use std::ops::{Add, Sub, Mul, Neg};

// ---------------------------------------------------------------------------
// Vec2
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Vec2<T> {
    pub x: T,
    pub y: T,
}

impl<T: Copy + Add<Output = T> + Mul<Output = T>> Vec2<T> {
    /// Create a new Vec2.
    #[inline]
    pub fn new(x: T, y: T) -> Self {
        Self { x, y }
    }

    /// Dot product.
    #[inline]
    pub fn dot(self, rhs: Self) -> T {
        self.x * rhs.x + self.y * rhs.y
    }
}

impl Vec2<f32> {
    /// Euclidean magnitude.
    #[inline]
    pub fn magnitude(self) -> f32 {
        (self.x * self.x + self.y * self.y).sqrt()
    }

    /// Return a unit vector.
    #[inline]
    pub fn normalise(self) -> Self {
        let mag = self.magnitude();
        Self { x: self.x / mag, y: self.y / mag }
    }

    /// Linear interpolation.
    #[inline]
    pub fn lerp(self, other: Self, t: f32) -> Self {
        Self {
            x: self.x + (other.x - self.x) * t,
            y: self.y + (other.y - self.y) * t,
        }
    }
}

// ---------------------------------------------------------------------------
// Vec3
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Vec3<T> {
    pub x: T,
    pub y: T,
    pub z: T,
}

impl<T: Copy + Add<Output = T> + Sub<Output = T> + Mul<Output = T>> Vec3<T> {
    #[inline]
    pub fn new(x: T, y: T, z: T) -> Self {
        Self { x, y, z }
    }

    /// Dot product.
    #[inline]
    pub fn dot(self, rhs: Self) -> T {
        self.x * rhs.x + self.y * rhs.y + self.z * rhs.z
    }

    /// Cross product.
    #[inline]
    pub fn cross(self, rhs: Self) -> Self {
        Self {
            x: self.y * rhs.z - self.z * rhs.y,
            y: self.z * rhs.x - self.x * rhs.z,
            z: self.x * rhs.y - self.y * rhs.x,
        }
    }
}

impl Vec3<f32> {
    #[inline]
    pub fn magnitude(self) -> f32 {
        (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
    }

    #[inline]
    pub fn normalise(self) -> Self {
        let mag = self.magnitude();
        Self { x: self.x / mag, y: self.y / mag, z: self.z / mag }
    }

    #[inline]
    pub fn lerp(self, other: Self, t: f32) -> Self {
        Self {
            x: self.x + (other.x - self.x) * t,
            y: self.y + (other.y - self.y) * t,
            z: self.z + (other.z - self.z) * t,
        }
    }
}

// Operator impls for Vec3<f32>
impl Add for Vec3<f32> {
    type Output = Self;
    fn add(self, rhs: Self) -> Self {
        Self { x: self.x + rhs.x, y: self.y + rhs.y, z: self.z + rhs.z }
    }
}

impl Sub for Vec3<f32> {
    type Output = Self;
    fn sub(self, rhs: Self) -> Self {
        Self { x: self.x - rhs.x, y: self.y - rhs.y, z: self.z - rhs.z }
    }
}

impl Mul<f32> for Vec3<f32> {
    type Output = Self;
    fn mul(self, s: f32) -> Self {
        Self { x: self.x * s, y: self.y * s, z: self.z * s }
    }
}

impl Neg for Vec3<f32> {
    type Output = Self;
    fn neg(self) -> Self {
        Self { x: -self.x, y: -self.y, z: -self.z }
    }
}

// ---------------------------------------------------------------------------
// Vec4
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Vec4<T> {
    pub x: T,
    pub y: T,
    pub z: T,
    pub w: T,
}

impl<T: Copy + Add<Output = T> + Mul<Output = T>> Vec4<T> {
    #[inline]
    pub fn new(x: T, y: T, z: T, w: T) -> Self {
        Self { x, y, z, w }
    }

    #[inline]
    pub fn dot(self, rhs: Self) -> T {
        self.x * rhs.x + self.y * rhs.y + self.z * rhs.z + self.w * rhs.w
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vec3_dot() {
        let a = Vec3::new(1.0f32, 2.0, 3.0);
        let b = Vec3::new(4.0f32, 5.0, 6.0);
        assert!((a.dot(b) - 32.0).abs() < 1e-6);
    }

    #[test]
    fn test_vec3_cross() {
        let x = Vec3::new(1.0f32, 0.0, 0.0);
        let y = Vec3::new(0.0f32, 1.0, 0.0);
        let z = x.cross(y);
        assert!((z.z - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_vec3_normalise() {
        let v = Vec3::new(3.0f32, 4.0, 0.0);
        let n = v.normalise();
        assert!((n.magnitude() - 1.0).abs() < 1e-6);
    }
}
