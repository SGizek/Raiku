# zigutils

General-purpose utility functions for Zig projects.

## Installation

```bash
raiku install zigutils
```

## Usage

```zig
const utils = @import("zigutils.zig");

const v = utils.clamp(i32, 15, 0, 10);  // 10
const t = utils.lerp(0.0, 100.0, 0.5); // 50.0
const ok = utils.isPowerOfTwo(16);      // true

const trimmed = utils.trimSpace("  hello  "); // "hello"
```

## License

MIT
