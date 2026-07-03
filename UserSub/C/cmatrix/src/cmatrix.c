/**
 * cmatrix.c — Lightweight 4x4 matrix operations in pure C.
 */
#include "cmatrix.h"
#include <stdio.h>
#include <string.h>

/* Helper: element index for row r, column c in a 4x4 row-major matrix. */
#define IDX(r, c) ((r) * 4 + (c))

Mat4 mat4_identity(void) {
    Mat4 result;
    memset(result.m, 0, sizeof(result.m));
    result.m[IDX(0,0)] = 1.0f;
    result.m[IDX(1,1)] = 1.0f;
    result.m[IDX(2,2)] = 1.0f;
    result.m[IDX(3,3)] = 1.0f;
    return result;
}

Mat4 mat4_mul(const Mat4 *a, const Mat4 *b) {
    Mat4 result;
    memset(result.m, 0, sizeof(result.m));
    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 4; c++) {
            float sum = 0.0f;
            for (int k = 0; k < 4; k++) {
                sum += a->m[IDX(r, k)] * b->m[IDX(k, c)];
            }
            result.m[IDX(r, c)] = sum;
        }
    }
    return result;
}

Mat4 mat4_transpose(const Mat4 *m) {
    Mat4 result;
    for (int r = 0; r < 4; r++) {
        for (int c = 0; c < 4; c++) {
            result.m[IDX(r, c)] = m->m[IDX(c, r)];
        }
    }
    return result;
}

Mat4 mat4_scale(const Mat4 *m, float s) {
    Mat4 result;
    for (int i = 0; i < 16; i++) {
        result.m[i] = m->m[i] * s;
    }
    return result;
}

Mat4 mat4_add(const Mat4 *a, const Mat4 *b) {
    Mat4 result;
    for (int i = 0; i < 16; i++) {
        result.m[i] = a->m[i] + b->m[i];
    }
    return result;
}

float mat4_get(const Mat4 *m, int r, int c) {
    return m->m[IDX(r, c)];
}

void mat4_set(Mat4 *m, int r, int c, float val) {
    m->m[IDX(r, c)] = val;
}

void mat4_print(const Mat4 *m) {
    for (int r = 0; r < 4; r++) {
        printf("| %8.4f %8.4f %8.4f %8.4f |\n",
               m->m[IDX(r,0)], m->m[IDX(r,1)],
               m->m[IDX(r,2)], m->m[IDX(r,3)]);
    }
}

/* Simple self-test when compiled as an executable. */
int main(void) {
    Mat4 I = mat4_identity();
    printf("Identity matrix:\n");
    mat4_print(&I);

    Mat4 A = mat4_identity();
    mat4_set(&A, 0, 1, 2.0f);
    mat4_set(&A, 1, 0, 3.0f);

    Mat4 B = mat4_mul(&A, &I);
    printf("\nA * I (should equal A):\n");
    mat4_print(&B);

    Mat4 T = mat4_transpose(&A);
    printf("\nTranspose of A:\n");
    mat4_print(&T);

    return 0;
}
