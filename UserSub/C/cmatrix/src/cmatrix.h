/**
 * cmatrix.h — Lightweight 4x4 matrix operations in pure C.
 *
 * All matrices are stored in row-major order as flat float[16] arrays.
 * No dynamic allocation is performed.
 */
#ifndef CMATRIX_H
#define CMATRIX_H

#include <stddef.h>

/* A 4x4 matrix stored row-major in a flat array. */
typedef struct {
    float m[16];
} Mat4;

/* Return the identity matrix. */
Mat4 mat4_identity(void);

/* Multiply two 4x4 matrices: result = a * b */
Mat4 mat4_mul(const Mat4 *a, const Mat4 *b);

/* Transpose a matrix. */
Mat4 mat4_transpose(const Mat4 *m);

/* Multiply all elements by scalar s. */
Mat4 mat4_scale(const Mat4 *m, float s);

/* Add two matrices element-wise. */
Mat4 mat4_add(const Mat4 *a, const Mat4 *b);

/* Access element at row r, column c (0-indexed). */
float mat4_get(const Mat4 *m, int r, int c);

/* Set element at row r, column c. */
void mat4_set(Mat4 *m, int r, int c, float val);

/* Print matrix to stdout (for debugging). */
void mat4_print(const Mat4 *m);

#endif /* CMATRIX_H */
