/// zigutils — General-purpose utility functions for Zig projects.
///
/// Provides string helpers, math utilities, and slice operations.
const std = @import("std");

// ---------------------------------------------------------------------------
// Math utilities
// ---------------------------------------------------------------------------

/// Clamp a value to [lo, hi].
pub fn clamp(comptime T: type, value: T, lo: T, hi: T) T {
    if (value < lo) return lo;
    if (value > hi) return hi;
    return value;
}

/// Linear interpolation between a and b by factor t in [0, 1].
pub fn lerp(a: f64, b: f64, t: f64) f64 {
    return a + (b - a) * t;
}

/// Return true if n is a power of two (n > 0).
pub fn isPowerOfTwo(n: u64) bool {
    return n > 0 and (n & (n - 1)) == 0;
}

/// Integer absolute value.
pub fn absi(x: i64) i64 {
    return if (x < 0) -x else x;
}

// ---------------------------------------------------------------------------
// Slice utilities
// ---------------------------------------------------------------------------

/// Return true if haystack contains needle.
pub fn contains(comptime T: type, haystack: []const T, needle: T) bool {
    for (haystack) |item| {
        if (item == needle) return true;
    }
    return false;
}

/// Return the first index of needle in haystack, or null if not found.
pub fn indexOf(comptime T: type, haystack: []const T, needle: T) ?usize {
    for (haystack, 0..) |item, i| {
        if (item == needle) return i;
    }
    return null;
}

/// Return a sub-slice with leading and trailing spaces removed.
pub fn trimSpace(s: []const u8) []const u8 {
    var start: usize = 0;
    while (start < s.len and s[start] == ' ') : (start += 1) {}
    var end: usize = s.len;
    while (end > start and s[end - 1] == ' ') : (end -= 1) {}
    return s[start..end];
}

/// Return true if s starts with prefix.
pub fn startsWith(s: []const u8, prefix: []const u8) bool {
    if (prefix.len > s.len) return false;
    return std.mem.eql(u8, s[0..prefix.len], prefix);
}

/// Return true if s ends with suffix.
pub fn endsWith(s: []const u8, suffix: []const u8) bool {
    if (suffix.len > s.len) return false;
    return std.mem.eql(u8, s[s.len - suffix.len ..], suffix);
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test "clamp" {
    try std.testing.expectEqual(@as(i32, 0),  clamp(i32, -5, 0, 10));
    try std.testing.expectEqual(@as(i32, 10), clamp(i32, 15, 0, 10));
    try std.testing.expectEqual(@as(i32, 5),  clamp(i32,  5, 0, 10));
}

test "lerp" {
    const result = lerp(0.0, 100.0, 0.25);
    try std.testing.expectApproxEqAbs(result, 25.0, 1e-9);
}

test "isPowerOfTwo" {
    try std.testing.expect(isPowerOfTwo(1));
    try std.testing.expect(isPowerOfTwo(4));
    try std.testing.expect(isPowerOfTwo(1024));
    try std.testing.expect(!isPowerOfTwo(3));
    try std.testing.expect(!isPowerOfTwo(0));
}

test "contains and indexOf" {
    const arr = [_]i32{ 1, 2, 3, 4, 5 };
    try std.testing.expect(contains(i32, &arr, 3));
    try std.testing.expect(!contains(i32, &arr, 9));
    try std.testing.expectEqual(@as(?usize, 2), indexOf(i32, &arr, 3));
    try std.testing.expectEqual(@as(?usize, null), indexOf(i32, &arr, 99));
}

test "string helpers" {
    try std.testing.expectEqualStrings("hello", trimSpace("  hello  "));
    try std.testing.expect(startsWith("hello world", "hello"));
    try std.testing.expect(endsWith("hello world", "world"));
    try std.testing.expect(!startsWith("hello", "world"));
}
