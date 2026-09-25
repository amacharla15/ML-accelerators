extern "C" __global__
void mul_add(const float* a, const float* b,
             const float* c, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i < n)
        out[i] = a[i] * b[i] + c[i];
}
