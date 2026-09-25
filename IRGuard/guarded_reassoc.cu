extern "C" __global__
void guarded_reassoc(
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

    float av = a[i];

    if (av != av) {
        out[i] = 0.0f;
        return;
    }

    float x = av * b[i];
    float y = x + c[i];
    out[i] = y + d[i];
}
