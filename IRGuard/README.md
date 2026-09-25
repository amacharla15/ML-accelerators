# IRGuard

Counterexample-guided repair of unsafe LLVM floating-point optimizations.

IRGuard lets an LLM choose LLVM floating-point optimization policies,
compiles them through LLVM/NVPTX, executes the resulting PTX on a real
NVIDIA GPU, and feeds numerical verification failures back to the model.

## Pipeline

CUDA kernel
 LLVM IR
 LLM-selected policy
 custom C++ LLVM pass
 LLVM O2
 NVPTX/PTX
 NVIDIA GPU
 numerical verifier
 repair loop

## Supported policies

- `contract` — permits multiply-add contraction
- `reassoc` — permits / performs reassociation
- `nnan` — assumes NaNs do not occur
- `ninf` — assumes infinities do not occur
- `arcp` — permits reciprocal-based transforms
