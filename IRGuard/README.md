# IRGuard

**Counterexample-guided repair of unsafe LLVM floating-point optimizations on NVIDIA GPUs.**

IRGuard is an agentic compiler experiment that asks whether concrete numerical counterexamples help an LLM repair unsafe floating-point optimization policies.

The agent selects LLVM floating-point transformations, a custom C++ LLVM pass applies them, LLVM lowers the transformed program to NVPTX/PTX, the PTX executes on a real NVIDIA GPU, and an adversarial verifier checks the result.

When verification fails, the agent receives either:

- only `VERIFICATION FAILED`, or
- the concrete input/output counterexample that caused the failure.

The repaired policy is then recompiled and executed again.

---

## Pipeline

```text
CUDA kernel
    ↓
Clang
    ↓
LLVM IR
    ↓
LLM-selected FP policy
    ↓
Custom LLVM pass
    ↓
LLVM O2
    ↓
NVPTX / PTX
    ↓
NVIDIA GPU
    ↓
Numerical verifier
    ↓
PASS or counterexample
    ↓
LLM repair
```

IRGuard does not treat the model's proposed optimization as correct until the generated PTX executes successfully against the verifier.

---

## Optimization policies

The agent can select from:

| Policy | Meaning |
|---|---|
| `contract` | Permit multiply-add contraction |
| `reassoc` | Permit / perform reassociation |
| `nnan` | Assume NaNs do not occur |
| `ninf` | Assume infinities do not occur |
| `arcp` | Permit reciprocal-based transformations |

The project currently demonstrates three distinct compiler mechanisms.

### `contract`

IRGuard attaches LLVM contraction permission to floating-point multiply/add operations.

For `mul_add`, NVPTX changes separate arithmetic into:

```ptx
fma.rn.f32
```

This can violate a contract requiring separate FP32 multiply and add rounding.

### `nnan`

IRGuard attaches LLVM's no-NaN assumption.

For `nan_guard`, LLVM O2 can then eliminate the program's explicit NaN handling.

Example counterexample:

```text
input:    NaN
expected: 0.0
actual:   NaN
```

### `reassoc`

IRGuard also implements a real arithmetic-tree rewrite in the custom LLVM pass.

Conceptually:

```text
(a * b + c) + d
```

becomes:

```text
a * b + (c + d)
```

For:

```text
a = 1e8
b = 1
c = -1e8
d = 1
```

the original evaluation produces:

```text
1.0
```

while the reassociated version produces:

```text
0.0
```

The transformation survives LLVM optimization and appears directly in generated PTX:

```ptx
add.rn.f32
fma.rn.f32
```

---

## Selective repair

IRGuard is designed so that the agent cannot succeed merely by disabling every optimization.

For example:

```text
initial policy:
["contract", "nnan"]

verification:
FAIL on NaN handling

agent repair:
["contract"]

verification:
PASS
```

The model removes the invalid `nnan` assumption while preserving FMA contraction.

A harder case activates multiple unsafe policies:

```text
["contract", "reassoc", "nnan"]
```

With counterexample feedback, one observed trajectory was:

```text
["contract", "reassoc", "nnan"]
        ↓
cancellation counterexample
        ↓
["contract", "nnan"]
        ↓
NaN counterexample
        ↓
["contract"]
        ↓
PASS
```

The useful `contract` optimization survives both repairs.

---

## Experiment

Five compiler-repair tasks were evaluated under two feedback conditions:

1. **Bare feedback** — the agent sees only `VERIFICATION FAILED`.
2. **Counterexample feedback** — the agent additionally sees the concrete failing input and output.

Each task was repeated 10 times per feedback condition.

```text
5 tasks
× 2 feedback modes
× 10 repetitions
= 100 agent episodes
```

The experiments used the same model, compiler pipeline, verifier, GPU, and repair budget.

### Overall results

| Feedback | Verified final policy | Minimal repair | Mean repair turns |
|---|---:|---:|---:|
| Bare | 50/50 | 50/50 | 1.14 |
| Counterexample | 50/50 | 50/50 | 1.20 |

Both feedback modes ultimately repaired every experiment.

For the simpler tasks, the kernel contract and active policy already exposed enough information for the model to identify the unsafe relaxation. Concrete counterexamples therefore did not improve final success.

---

## Hidden sequential-failure result

The `guarded_reassoc` task contains two independent semantic failures:

```text
reassoc → cancellation failure
nnan    → NaN-handling failure
contract → valid and should remain enabled
```

The verifier exposes the cancellation failure first.

Across 10 runs:

| Metric | Bare | Counterexample |
|---|---:|---:|
| Verified final policy | 10/10 | 10/10 |
| Minimal final policy | 10/10 | 10/10 |
| Fixed currently exposed failure first | **3/10** | **10/10** |
| Mean repair turns | 1.7 | 2.0 |

This reveals an important tradeoff.

Bare feedback sometimes reaches the final policy faster by making a broader speculative repair.

Counterexample feedback instead produces more targeted, evidence-aligned repairs: it fixed the failure currently demonstrated by the verifier in 100% of runs versus 30% with generic failure feedback.

The result therefore does **not** show that counterexamples universally improve convergence speed.

It shows that, in the harder ambiguous case, they substantially improve **causal localization of the observed compiler-semantic failure**.

---

## GPU execution

Every candidate policy is compiled through the actual compiler stack:

```text
LLVM IR
→ LLVM optimization
→ NVPTX backend
→ PTX
→ NVIDIA GPU
```

The verifier checks the executed GPU result rather than reasoning only over source code or LLVM IR.

Experimental environment:

```text
GPU:         NVIDIA L4
Driver:      570.195.03
LLVM:        21.1.8
Python:      3.11.10
CuPy:        14.2.0
OpenAI SDK:  3.19.2
```

---

## Performance

A verified `guarded_mul_add` policy using FMA contraction was benchmarked against the strict implementation.

Configuration:

```text
N:                 1,048,576 elements
Warmup:            50 launches
Measured launches: 300
Repeated runs:     5
GPU:               NVIDIA L4
```

Observed median latency:

```text
strict   ≈ 0.01120 ms
contract ≈ 0.01120 ms
speedup  ≈ 1.00x
```

No meaningful performance difference was measurable for this small memory-bound kernel.

The experiment therefore treats FMA preservation as a compiler/code-generation result rather than claiming a performance improvement that was not measured.

---

## Repository structure

```text
IRGuard/
├── agent.py
├── harness.py
├── verifier.py
├── evaluate.py
├── experiment.py
├── benchmark.py
├── make_summary.py
│
├── llvm-pass/
│   ├── IRGuardMathPass.cpp
│   └── CMakeLists.txt
│
├── nan_guard.cu
├── mul_add.cu
├── guarded_mul_add.cu
├── reassoc_mix.cu
├── guarded_reassoc.cu
│
└── results/
    ├── experiment_100episodes.json
    ├── summary.json
    ├── benchmark-summary.txt
    ├── environment.txt
    ├── contract_counterexample.txt
    ├── nnan_counterexample.txt
    ├── contract_ptx.diff
    ├── nnan_ir.diff
    ├── llvm-evidence/
    └── ptx-evidence/
```

---

## Build the LLVM pass

IRGuard was tested with LLVM 21.

```bash
cd llvm-pass
mkdir -p build
cd build
```

```bash
cmake \
  -G Ninja \
  -DLLVM_DIR="$(llvm-config-21 --cmakedir)" \
  ..
```

```bash
ninja
```

This produces:

```text
llvm-pass/build/IRGuardMathPass.so
```

---

## Run a repair episode

Set the GPU architecture if needed:

```bash
export IRGUARD_ARCH=sm_89
```

Set your API key through the environment:

```bash
export OPENAI_API_KEY=...
```

Example:

```python
from agent import run_episode

run_episode(
    "guarded_reassoc",
    ["contract", "reassoc", "nnan"],
    feedback_mode="counterexample",
    max_turns=4,
)
```

---

## Run the experiment

```bash
IRGUARD_RUNS=10 python3 experiment.py
```

The complete experiment trajectories are written under:

```text
results/
```

The frozen 100-episode run used for the reported results is:

```text
results/experiment_100episodes.json
```

---

## Important scope

IRGuard is an adversarial numerical verification experiment, not a formal verifier.

A `PASS` means that a policy passed the implemented verification suite; it does not prove semantic equivalence for every possible floating-point input.

Similarly, the demonstrated failures are not LLVM bugs.

They are cases where an optimization policy selected by the agent violates the numerical contract declared for the kernel.

---

## Main finding

For simple compiler-policy failures, a capable coding model often identifies the unsafe optimization from the policy and semantic contract alone.

Concrete counterexamples become more useful when several plausible transformations are active and the failure cause is ambiguous.

In IRGuard's hidden sequential-failure task, counterexamples increased first-step causal localization from **30% to 100%**, while both feedback modes still reached verified minimal final policies in every run.
