extern "C" __global__
void reassoc_mix(
    const float* a,
    const float* b,
    const float* c,
    const float* d,
    float* out,
    int n) {
    int i =
        blockIdx.x * blockDim.x +
        threadIdx.x;

    if (i >= n)
        return;

    float x = a[i] * b[i];
    float y = x + c[i];

    out[i] = y + d[i];
}
