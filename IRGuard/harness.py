import os
import subprocess
from pathlib import Path

ROOT = Path("/workspace/irguard")
ARCH = os.environ.get("IRGUARD_ARCH", "sm_89")

PLUGIN = ROOT / "llvm-pass/build/IRGuardMathPass.so"

ALLOWED = {
    "contract",
    "reassoc",
    "arcp",
    "nnan",
    "ninf",
}

def run(cmd, env=None):
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stdout + "\n" + result.stderr
        )

    return result

def validate_policy(policy):
    policy = set(policy)

    unknown = policy - ALLOWED

    if unknown:
        raise ValueError(
            f"unknown policy flags: {sorted(unknown)}"
        )

    return sorted(policy)

def apply_policy(name, policy):
    policy = validate_policy(policy)

    src = ROOT / f"{name}.strict.ll"
    tag = "strict" if not policy else "-".join(policy)
    transformed = ROOT / f"{name}.agent.{tag}.ll"

    env = os.environ.copy()
    env["IRGUARD_POLICY"] = ",".join(policy)

    run([
        "opt-21",
        "-load-pass-plugin", str(PLUGIN),
        "-passes=function(irguard-math)",
        "-S",
        str(src),
        "-o", str(transformed),
    ], env=env)

    return transformed

def optimize_ir(name, transformed):
    optimized = transformed.with_name(transformed.stem + ".opt.ll")

    run([
        "opt-21",
        "-passes=default<O2>",
        "-S",
        str(transformed),
        "-o", str(optimized),
    ])

    return optimized

def lower_ptx(name, optimized):
    ptx = optimized.with_name(optimized.stem + ".ptx")

    run([
        "llc-21",
        "-march=nvptx64",
        f"-mcpu={ARCH}",
        "-O2",
        str(optimized),
        "-o", str(ptx),
    ])

    return ptx

def compile_policy(name, policy):
    transformed = apply_policy(name, policy)
    optimized = optimize_ir(name, transformed)
    ptx = lower_ptx(name, optimized)

    return {
        "policy": sorted(policy),
        "llvm_ir": str(optimized),
        "ptx": str(ptx),
    }
