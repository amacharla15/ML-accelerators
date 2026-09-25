import statistics
import cupy as cp

N = 1 << 20
WARMUP = 50
RUNS = 300

a = cp.random.uniform(0.5, 2.0, N).astype(cp.float32)
b = cp.random.uniform(0.5, 2.0, N).astype(cp.float32)
c = cp.random.uniform(-1.0, 1.0, N).astype(cp.float32)
out = cp.empty_like(a)
def load(path):
    mod = cp.RawModule(path=path)
    return mod.get_function("guarded_mul_add")

strict = load(
    "guarded_mul_add.agent.strict.opt.ptx"
)

contract = load(
    "guarded_mul_add.agent.contract.opt.ptx"
)
def bench(kernel):
    grid = ((N + 255) // 256,)
    block = (256,)

    for _ in range(WARMUP):
        kernel(
            grid, block,
            (a, b, c, out, cp.int32(N)),
        )

    cp.cuda.runtime.deviceSynchronize()
    times = []

    for _ in range(RUNS):
        start = cp.cuda.Event()
        end = cp.cuda.Event()

        start.record()
        kernel(
            grid, block,
            (a, b, c, out, cp.int32(N)),
        )

        end.record()
        end.synchronize()

        times.append(
            cp.cuda.get_elapsed_time(start, end)
        )

    return statistics.median(times)

s = bench(strict)
c = bench(contract)

print("strict median ms:", s)
print("contract median ms:", c)
print("speedup:", s / c)
