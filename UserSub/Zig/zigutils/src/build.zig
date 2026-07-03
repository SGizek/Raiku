const std = @import("std");

pub fn build(b: *std.Build) void {
    const target   = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Static library
    const lib = b.addStaticLibrary(.{
        .name    = "zigutils",
        .root_source_file = b.path("zigutils.zig"),
        .target  = target,
        .optimize = optimize,
    });
    b.installArtifact(lib);

    // Unit tests
    const unit_tests = b.addTest(.{
        .root_source_file = b.path("zigutils.zig"),
        .target  = target,
        .optimize = optimize,
    });
    const run_tests = b.addRunArtifact(unit_tests);
    const test_step = b.step("test", "Run zigutils unit tests");
    test_step.dependOn(&run_tests.step);
}
