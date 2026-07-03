# cmatrix

Lightweight 4×4 matrix operations in pure C. No dependencies, no dynamic allocation.

## Installation

```bash
raiku install cmatrix
```

## Usage

```c
#include "cmatrix.h"
#include <stdio.h>

int main(void) {
    Mat4 I = mat4_identity();
    mat4_print(&I);

    Mat4 A = mat4_identity();
    mat4_set(&A, 0, 1, 5.0f);

    Mat4 B = mat4_mul(&A, &I);
    mat4_print(&B);
    return 0;
}
```

Compile:

```bash
gcc -O2 -o my_app my_app.c path/to/cmatrix.c -lm
```

## License

MIT
