import json
import os

from openai import OpenAI
from evaluate import evaluate

client = OpenAI()

MODEL = os.environ.get(
    "IRGUARD_MODEL",
    "gpt-5.6-luna",
)

ALLOWED = [
    "contract",
    "reassoc",
    "arcp",
    "nnan",
    "ninf",
]

KERNELS = {
    "nan_guard": {
        "description":
            "Return 0 for NaN; otherwise return x + 1.",
        "contract":
            "NaN inputs must produce exactly 0.0.",
    },

    "mul_add": {
        "description":
            "Compute a*b+c using FP32.",
        "contract":
            "Separate FP32 multiply and add rounding is required.",
    },
}

SCHEMA = {
    "type": "object",
    "properties": {
        "policy": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ALLOWED,
            },
        },
        "hypothesis": {
            "type": "string",
        },
    },
    "required": [
        "policy",
        "hypothesis",
    ],
    "additionalProperties": False,
}

def propose(kernel, policy, feedback):
    info = KERNELS[kernel]

    prompt = f"""
You control LLVM floating-point optimization policy.

Kernel: {kernel}
Description: {info["description"]}
Required semantics: {info["contract"]}

Allowed LLVM flags:
{ALLOWED}

Current policy:
{policy}
"""

    prompt += f"""

Verifier feedback:
{json.dumps(feedback, indent=2)}

Return the next policy.

Preserve useful optimizations when they are compatible
with the required semantics. Remove only assumptions
that you believe caused the verification failure.
"""

    r = client.responses.create(
        model=MODEL,
        input=prompt,
        max_output_tokens=1000,
        text={
            "format": {
                "type": "json_schema",
                "name": "irguard_policy",
                "strict": True,
                "schema": SCHEMA,
            }
        },
    )

    raw = r.output_text.strip()

    if not raw:
        raise RuntimeError(
            "Empty model output"
            f" status={getattr(r, 'status', None)}"
            f" incomplete={getattr(r, 'incomplete_details', None)}"
            f" usage={getattr(r, 'usage', None)}"
            f" output={getattr(r, 'output', None)}"
        )

    try:
        proposal = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Invalid structured model output"
            f" status={getattr(r, 'status', None)}"
            f" incomplete={getattr(r, 'incomplete_details', None)}"
            f" raw={raw!r}"
        ) from e

    usage = {
        "input_tokens":
            getattr(r.usage, "input_tokens", 0),
        "output_tokens":
            getattr(r.usage, "output_tokens", 0),
    }

    return proposal, usage

def run_episode(
    kernel,
    initial_policy,
    feedback_mode="counterexample",
    max_turns=4,
):
    policy = list(initial_policy)
    trajectory = []

    for turn in range(max_turns):
        result = evaluate(
            kernel,
            policy,
        )

        step = {
            "turn": turn,
            "policy": list(policy),
            "result": result,
        }

        print(
            f"turn={turn} "
            f"policy={policy} "
            f"status={result['status']}"
        )

        if result["status"] == "PASS":
            trajectory.append(step)
            return trajectory

        if feedback_mode == "bare":
            feedback = {
                "status":
                    "VERIFICATION FAILED",
            }

        elif feedback_mode == "counterexample":
            feedback = {
                "status":
                    "VERIFICATION FAILED",
                "counterexample":
                    result["counterexample"],
            }

        else:
            raise ValueError(
                f"bad feedback mode: {feedback_mode}"
            )

        proposal, usage = propose(
            kernel,
            policy,
            feedback,
        )

        step["feedback"] = feedback
        step["proposal"] = proposal
        step["usage"] = usage

        trajectory.append(step)

        print("agent:", proposal)

        policy = proposal["policy"]

    return trajectory

KERNELS["guarded_mul_add"] = {
    "description":
        "Return 0 for NaN a; otherwise compute a*b+c.",

    "contract":
        "NaN a must produce 0.0. FMA contraction is allowed "
        "for finite inputs with absolute error <= 1e-6.",
}

KERNELS["reassoc_mix"] = {
    "description":
        "Compute a finite FP32 arithmetic expression using "
        "a, b, c, and d.",

    "contract":
        "Outputs must satisfy the verifier's numerical accuracy "
        "requirements. FMA contraction is permitted.",
}

KERNELS["guarded_reassoc"] = {
    "description":
        "Compute a guarded FP32 arithmetic expression over "
        "a, b, c, and d.",

    "contract":
        "Outputs must satisfy the hidden numerical verification "
        "suite. FMA contraction is permitted.",
}
