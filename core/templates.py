"""
Raiku language templates.

Provides per-language scaffolding templates for raiku init.
Each template defines the src/ files that get created.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class TemplateFile:
    """A single file to create inside src/."""
    filename: str
    content_fn: Callable[[dict], str]  # called with context dict


@dataclass
class LanguageTemplate:
    name: str
    language: str
    default_build_command: str
    src_files: list[TemplateFile] = field(default_factory=list)
    extra_root_files: list[TemplateFile] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Template content functions
# ---------------------------------------------------------------------------

def _python_main(ctx: dict) -> str:
    name = ctx["name"]
    safe = name.replace("-", "_")
    return f'''"""
{name} — {ctx.get("description", "A Raiku Python package.")}
"""
from __future__ import annotations


def hello() -> str:
    """Return a greeting string."""
    return "Hello from {name}!"


if __name__ == "__main__":
    print(hello())
'''

def _python_setup(ctx: dict) -> str:
    return f'''[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{ctx["name"]}"
version = "{ctx["version"]}"
description = "{ctx.get("description", "")}"
authors = [{{name = "{ctx["author"]}"}}]
requires-python = ">=3.10"
'''

def _rust_lib(ctx: dict) -> str:
    name = ctx["name"].replace("-", "_")
    return f'''//! {ctx["name"]} — {ctx.get("description", "A Raiku Rust package.")}

/// Returns a greeting string.
pub fn hello() -> &'static str {{
    "Hello from {ctx["name"]}!"
}}

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn test_hello() {{
        assert_eq!(hello(), "Hello from {ctx["name"]}!");
    }}
}}
'''

def _rust_cargo(ctx: dict) -> str:
    return f'''[package]
name = "{ctx["name"]}"
version = "{ctx["version"]}"
edition = "2021"
authors = ["{ctx["author"]}"]
description = "{ctx.get("description", "")}"
license = "{ctx.get("license", "MIT")}"

[lib]
name = "{ctx["name"].replace("-", "_")}"
path = "lib.rs"

[dependencies]
'''

def _c_header(ctx: dict) -> str:
    guard = ctx["name"].upper().replace("-", "_").replace(" ", "_") + "_H"
    return f'''/**
 * {ctx["name"]}.h — {ctx.get("description", "A Raiku C package.")}
 */
#ifndef {guard}
#define {guard}

/**
 * Returns a greeting string.
 */
const char *{ctx["name"].replace("-", "_")}_hello(void);

#endif /* {guard} */
'''

def _c_source(ctx: dict) -> str:
    safe = ctx["name"].replace("-", "_")
    return f'''/**
 * {ctx["name"]}.c — {ctx.get("description", "A Raiku C package.")}
 */
#include "{ctx["name"]}.h"
#include <stdio.h>

const char *{safe}_hello(void) {{
    return "Hello from {ctx["name"]}!";
}}

int main(void) {{
    printf("%s\\n", {safe}_hello());
    return 0;
}}
'''

def _cpp_header(ctx: dict) -> str:
    safe = ctx["name"].replace("-", "_")
    ns = safe
    return f'''/**
 * {ctx["name"]}.hpp — {ctx.get("description", "A Raiku C++ package.")}
 */
#pragma once
#include <string>

namespace {ns} {{

/// Returns a greeting string.
std::string hello();

}} // namespace {ns}
'''

def _cpp_source(ctx: dict) -> str:
    safe = ctx["name"].replace("-", "_")
    return f'''#include "{ctx["name"]}.hpp"

namespace {safe} {{

std::string hello() {{
    return "Hello from {ctx["name"]}!";
}}

}} // namespace {safe}
'''

def _cpp_cmake(ctx: dict) -> str:
    safe = ctx["name"].replace("-", "_")
    return f'''cmake_minimum_required(VERSION 3.16)
project({safe} VERSION {ctx["version"]} LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_library({safe} {safe}.cpp)
target_include_directories({safe} PUBLIC ${{CMAKE_CURRENT_SOURCE_DIR}})
'''

def _zig_source(ctx: dict) -> str:
    return f'''//! {ctx["name"]} — {ctx.get("description", "A Raiku Zig package.")}
const std = @import("std");

/// Returns a greeting string.
pub fn hello() []const u8 {{
    return "Hello from {ctx["name"]}!";
}}

test "hello" {{
    const result = hello();
    try std.testing.expectEqualStrings("Hello from {ctx["name"]}!", result);
}}
'''

def _zig_build(ctx: dict) -> str:
    safe = ctx["name"].replace("-", "_")
    return f'''const std = @import("std");

pub fn build(b: *std.Build) void {{
    const target   = b.standardTargetOptions(.{{}});
    const optimize = b.standardOptimizeOption(.{{}});

    const lib = b.addStaticLibrary(.{{
        .name = "{ctx["name"]}",
        .root_source_file = b.path("{safe}.zig"),
        .target  = target,
        .optimize = optimize,
    }});
    b.installArtifact(lib);

    const unit_tests = b.addTest(.{{
        .root_source_file = b.path("{safe}.zig"),
        .target  = target,
        .optimize = optimize,
    }});
    const run_tests = b.addRunArtifact(unit_tests);
    const test_step = b.step("test", "Run unit tests");
    test_step.dependOn(&run_tests.step);
}}
'''

def _java_source(ctx: dict) -> str:
    pkg = "dev.raiku." + ctx["name"].replace("-", "").lower()
    cls = "".join(w.capitalize() for w in ctx["name"].replace("-", "_").split("_"))
    return f'''package {pkg};

/**
 * {ctx["name"]} — {ctx.get("description", "A Raiku Java package.")}
 */
public final class {cls} {{

    private {cls}() {{}}

    /**
     * Returns a greeting string.
     */
    public static String hello() {{
        return "Hello from {ctx["name"]}!";
    }}

    public static void main(String[] args) {{
        System.out.println(hello());
    }}
}}
'''

def _csharp_source(ctx: dict) -> str:
    ns = "Raiku." + "".join(w.capitalize() for w in ctx["name"].replace("-", "_").split("_"))
    cls = "".join(w.capitalize() for w in ctx["name"].replace("-", "_").split("_"))
    return f'''namespace {ns};

/// <summary>
/// {ctx.get("description", "A Raiku C# package.")}
/// </summary>
public static class {cls}
{{
    /// <summary>Returns a greeting string.</summary>
    public static string Hello() => "Hello from {ctx["name"]}!";
}}
'''

def _csharp_csproj(ctx: dict) -> str:
    return f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
    <LangVersion>12</LangVersion>
    <AssemblyName>{ctx["name"]}</AssemblyName>
    <Version>{ctx["version"]}</Version>
    <Authors>{ctx["author"]}</Authors>
    <Description>{ctx.get("description", "")}</Description>
  </PropertyGroup>
</Project>
'''

def _go_source(ctx: dict) -> str:
    pkg = ctx["name"].replace("-", "")
    return f'''// Package {pkg} — {ctx.get("description", "A Raiku Go package.")}
package {pkg}

// Hello returns a greeting string.
func Hello() string {{
    return "Hello from {ctx["name"]}!"
}}
'''

def _go_test(ctx: dict) -> str:
    pkg = ctx["name"].replace("-", "")
    return f'''package {pkg}_test

import (
    "testing"
    {pkg} "{ctx.get("module", "github.com/SGizek/Raiku/UserSub/Go/" + ctx["name"] + "/src")}"
)

func TestHello(t *testing.T) {{
    got := {pkg}.Hello()
    want := "Hello from {ctx["name"]}!"
    if got != want {{
        t.Errorf("Hello() = %q, want %q", got, want)
    }}
}}
'''

def _go_mod(ctx: dict) -> str:
    mod = ctx.get("module", f'github.com/SGizek/Raiku/UserSub/Go/{ctx["name"]}')
    return f'''module {mod}

go 1.21
'''


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, LanguageTemplate] = {
    "Python": LanguageTemplate(
        name="Python",
        language="Python",
        default_build_command="pip install -e .",
        src_files=[
            TemplateFile("{name_safe}.py", _python_main),
        ],
        extra_root_files=[
            TemplateFile("pyproject.toml", _python_setup),
        ],
    ),
    "Rust": LanguageTemplate(
        name="Rust",
        language="Rust",
        default_build_command="cargo build --release",
        src_files=[
            TemplateFile("lib.rs",     _rust_lib),
            TemplateFile("Cargo.toml", _rust_cargo),
        ],
    ),
    "C": LanguageTemplate(
        name="C",
        language="C",
        default_build_command="gcc -O2 -Wall -o {name} src/{name}.c -lm",
        src_files=[
            TemplateFile("{name}.h", _c_header),
            TemplateFile("{name}.c", _c_source),
        ],
    ),
    "CPP": LanguageTemplate(
        name="CPP",
        language="CPP",
        default_build_command="cmake -S src -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build",
        src_files=[
            TemplateFile("{name}.hpp",    _cpp_header),
            TemplateFile("{name}.cpp",    _cpp_source),
            TemplateFile("CMakeLists.txt", _cpp_cmake),
        ],
    ),
    "Zig": LanguageTemplate(
        name="Zig",
        language="Zig",
        default_build_command="zig build",
        src_files=[
            TemplateFile("{name_safe}.zig", _zig_source),
            TemplateFile("build.zig",       _zig_build),
        ],
    ),
    "Java": LanguageTemplate(
        name="Java",
        language="Java",
        default_build_command="javac -d out src/dev/raiku/{name_safe}/*.java",
        src_files=[
            TemplateFile("dev/raiku/{name_safe}/{cls}.java", _java_source),
        ],
    ),
    "CSharp": LanguageTemplate(
        name="CSharp",
        language="CSharp",
        default_build_command="dotnet build src/{name}.csproj -c Release",
        src_files=[
            TemplateFile("{cls}.cs",         _csharp_source),
            TemplateFile("{name}.csproj",    _csharp_csproj),
        ],
    ),
    "Go": LanguageTemplate(
        name="Go",
        language="Go",
        default_build_command="go build ./...",
        src_files=[
            TemplateFile("{name_safe}.go",      _go_source),
            TemplateFile("{name_safe}_test.go", _go_test),
            TemplateFile("go.mod",              _go_mod),
        ],
    ),
}


def get_template(language: str) -> LanguageTemplate | None:
    return TEMPLATES.get(language)


def expand_filename(filename: str, ctx: dict) -> str:
    """Replace template variables in a filename."""
    return (filename
            .replace("{name}", ctx["name"])
            .replace("{name_safe}", ctx["name_safe"])
            .replace("{cls}", ctx["cls"]))
