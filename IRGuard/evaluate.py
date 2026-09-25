from harness import compile_policy
from verifier import (
    verify_nan_guard,
    verify_mul_add, verify_guarded_mul_add, verify_reassoc_mix, verify_guarded_reassoc,
)

def evaluate(kernel, policy):
    build = compile_policy(
        kernel,
        policy,
    )

    if kernel == "nan_guard":
        result = verify_nan_guard(
            build["ptx"]
        )

    elif kernel == "mul_add":
        result = verify_mul_add(
            build["ptx"]
        )

    elif kernel == "guarded_mul_add":
        result = verify_guarded_mul_add(
            build["ptx"]
        )

    elif kernel == "reassoc_mix":
        result = verify_reassoc_mix(
            build["ptx"]
        )

    elif kernel == "guarded_reassoc":
        result = verify_guarded_reassoc(
            build["ptx"]
        )

    else:
        raise ValueError(
            f"unknown kernel: {kernel}"
        )

    result["policy"] = build["policy"]
    result["llvm_ir"] = build["llvm_ir"]
    result["ptx"] = build["ptx"]

    return result
