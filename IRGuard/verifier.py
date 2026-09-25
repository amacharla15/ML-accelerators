import cupy as cp
import numpy as np

def _json_float(x):
    x = float(x)

    if np.isnan(x):
        return "NaN"

    if np.isposinf(x):
        return "+Inf"

    if np.isneginf(x):
        return "-Inf"

    return x

def verify_nan_guard(ptx_path):
    x_np = np.array(
        [np.nan, 1.0, -2.0],
        dtype=np.float32,
    )

    x = cp.asarray(x_np)
    out = cp.empty(3, dtype=cp.float32)

    mod = cp.RawModule(path=str(ptx_path))
    kernel = mod.get_function("nan_guard")

    kernel(
        (1,),
        (32,),
        (
            x,
            out,
            cp.int32(3),
        ),
    )

    cp.cuda.runtime.deviceSynchronize()

    result = cp.asnumpy(out)

    expected = np.array(
        [0.0, 2.0, -1.0],
        dtype=np.float32,
    )

    ok = (
        np.isfinite(result[0])
        and result[0] == expected[0]
        and result[1] == expected[1]
        and result[2] == expected[2]
    )

    if ok:
        return {
            "status": "PASS",
            "kernel": "nan_guard",
        }

    return {
        "status": "FAIL",
        "kernel": "nan_guard",
        "counterexample": {
            "input": "NaN",
            "expected": 0.0,
            "actual": _json_float(result[0]),
        },
    }

def verify_mul_add(ptx_path):
    rng = np.random.default_rng(7)
    n = 4096

    a_np = rng.uniform(
        0.5, 2.0, n
    ).astype(np.float32)

    b_np = rng.uniform(
        0.5, 2.0, n
    ).astype(np.float32)

    product = (
        a_np * b_np
    ).astype(np.float32)

    c_np = -product

    a = cp.asarray(a_np)
    b = cp.asarray(b_np)
    c = cp.asarray(c_np)

    out = cp.empty(n, dtype=cp.float32)

    mod = cp.RawModule(
        path=str(ptx_path)
    )

    kernel = mod.get_function("mul_add")

    threads = 256
    blocks = (n + threads - 1) // threads

    kernel(
        (blocks,),
        (threads,),
        (a, b, c, out, cp.int32(n)),
    )

    cp.cuda.runtime.deviceSynchronize()

    result = cp.asnumpy(out)

    # Contract requires separate FP32 multiply
    # followed by separate FP32 addition.
    expected = np.zeros(
        n,
        dtype=np.float32,
    )

    bad = np.flatnonzero(
        result != expected
    )

    if len(bad) == 0:
        return {
            "status": "PASS",
            "kernel": "mul_add",
        }

    i = int(bad[0])

    return {
        "status": "FAIL",
        "kernel": "mul_add",
        "counterexample": {
            "a": float(a_np[i]),
            "b": float(b_np[i]),
            "c": float(c_np[i]),
            "expected": 0.0,
            "actual": _json_float(result[i]),
        },
    }

def verify_guarded_mul_add(ptx_path):
    a_np = np.array(
        [np.nan, 1.4376432],
        dtype=np.float32,
    )

    b_np = np.array(
        [1.0, 0.5253973],
        dtype=np.float32,
    )

    c_np = np.array(
        [0.0, -0.75533384],
        dtype=np.float32,
    )

    a = cp.asarray(a_np)
    b = cp.asarray(b_np)
    c = cp.asarray(c_np)

    out = cp.empty(2, dtype=cp.float32)

    mod = cp.RawModule(
        path=str(ptx_path)
    )

    kernel = mod.get_function(
        "guarded_mul_add"
    )

    kernel(
        (1,),
        (32,),
        (a, b, c, out, cp.int32(2)),
    )

    cp.cuda.runtime.deviceSynchronize()
    result = cp.asnumpy(out)

    if not np.isfinite(result[0]):
        return {
            "status": "FAIL",
            "kernel": "guarded_mul_add",
            "counterexample": {
                "input": "a=NaN",
                "expected": 0.0,
                "actual": _json_float(result[0]),
            },
        }

    if abs(float(result[1])) > 1e-6:
        return {
            "status": "FAIL",
            "kernel": "guarded_mul_add",
            "counterexample": {
                "input": "finite",
                "expected_tolerance": 1e-6,
                "actual": _json_float(result[1]),
            },
        }

    return {
        "status": "PASS",
        "kernel": "guarded_mul_add",
    }

def verify_reassoc_mix(ptx_path):
    a = cp.asarray(
        np.array([1.0e8], dtype=np.float32)
    )
    b = cp.asarray(
        np.array([1.0], dtype=np.float32)
    )

    c = cp.asarray(
        np.array([-1.0e8], dtype=np.float32)
    )
    d = cp.asarray(
        np.array([1.0], dtype=np.float32)
    )

    out = cp.empty(1, dtype=cp.float32)

    mod = cp.RawModule(
        path=str(ptx_path)
    )

    kernel = mod.get_function(
        "reassoc_mix"
    )

    kernel(
        (1,),
        (32,),
        (a, b, c, d, out, cp.int32(1)),
    )

    cp.cuda.runtime.deviceSynchronize()

    actual = float(
        cp.asnumpy(out)[0]
    )

    expected = 1.0

    if abs(actual - expected) > 1e-6:
        return {
            "status": "FAIL",
            "kernel": "reassoc_mix",
            "counterexample": {
                "a": 1.0e8,
                "b": 1.0,
                "c": -1.0e8,
                "d": 1.0,
                "expected": expected,
                "actual": actual,
            },
        }

    return {
        "status": "PASS",
        "kernel": "reassoc_mix",
    }

def verify_guarded_reassoc(ptx_path):
    mod = cp.RawModule(path=str(ptx_path))
    kernel = mod.get_function("guarded_reassoc")

    # Case 1: cancellation exposes reassociation.
    a = cp.asarray(np.array([1.0e8], dtype=np.float32))
    b = cp.asarray(np.array([1.0], dtype=np.float32))
    c = cp.asarray(np.array([-1.0e8], dtype=np.float32))
    d = cp.asarray(np.array([1.0], dtype=np.float32))
    out = cp.empty(1, dtype=cp.float32)

    kernel(
        (1,), (32,),
        (a, b, c, d, out, cp.int32(1)),
    )

    cp.cuda.runtime.deviceSynchronize()
    actual = float(cp.asnumpy(out)[0])

    if abs(actual - 1.0) > 1e-6:
        return {
            "status": "FAIL",
            "kernel": "guarded_reassoc",
            "counterexample": {
                "kind": "cancellation",
                "a": 1.0e8,
                "b": 1.0,
                "c": -1.0e8,
                "d": 1.0,
                "expected": 1.0,
                "actual": actual,
            },
        }

    # Case 2: NaN handling exposes nnan.
    a = cp.asarray(np.array([np.nan], dtype=np.float32))
    b = cp.asarray(np.array([1.0], dtype=np.float32))
    c = cp.asarray(np.array([0.0], dtype=np.float32))
    d = cp.asarray(np.array([0.0], dtype=np.float32))
    out = cp.empty(1, dtype=cp.float32)

    kernel(
        (1,), (32,),
        (a, b, c, d, out, cp.int32(1)),
    )

    cp.cuda.runtime.deviceSynchronize()
    actual = float(cp.asnumpy(out)[0])

    if not np.isfinite(actual) or actual != 0.0:
        return {
            "status": "FAIL",
            "kernel": "guarded_reassoc",
            "counterexample": {
                "kind": "nan",
                "a": "NaN",
                "expected": 0.0,
                "actual": _json_float(actual),
            },
        }

    return {
        "status": "PASS",
        "kernel": "guarded_reassoc",
    }
