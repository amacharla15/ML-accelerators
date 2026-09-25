extern "C" __global__
void guarded_mul_add(
    const float* a,
    const float* b,
    const float* c,
    float* out,
    int n) {
    int i =
        blockIdx.x * blockDim.x +
        threadIdx.x;

    if (i >= n)
        return;

    float av = a[i];

    if (av != av)
        out[i] = 0.0f;
    else
        out[i] = av * b[i] + c[i];
}
