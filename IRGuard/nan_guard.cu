extern "C" __global__
void nan_guard(const float* x, float* out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;

    if (i >= n)
        return;

    float v = x[i];

    if (v != v)
        out[i] = 0.0f;
    else
        out[i] = v + 1.0f;
}
