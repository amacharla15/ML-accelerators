import json
import os
from pathlib import Path

from agent import run_episode

ROOT = Path("/workspace/irguard")
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

RUNS = int(os.environ.get("IRGUARD_RUNS", "5"))

CASES = [
    {
        "name": "nan_guard",
        "initial": ["nnan"],
        "target": [],
    },
    {
        "name": "mul_add",
        "initial": ["contract"],
        "target": [],
    },
    {
        "name": "guarded_mul_add",
        "initial": ["contract", "nnan"],
        "target": ["contract"],
    },
    {
        "name": "reassoc_mix",
        "initial": ["contract", "reassoc"],
        "target": ["contract"],
    },
    {
        "name": "guarded_reassoc",
        "initial": ["contract", "reassoc", "nnan"],
        "target": ["contract"],
    },
]

def summarize(case, mode, run_id, trajectory):
    last = trajectory[-1]
    passed = last["result"]["status"] == "PASS"
    final_policy = last["policy"]

    repair_turns = (
        len(trajectory) - 1
        if passed else None
    )

    total_in = sum(
        x.get("usage", {}).get("input_tokens", 0)
        for x in trajectory
    )

    total_out = sum(
        x.get("usage", {}).get("output_tokens", 0)
        for x in trajectory
    )

    first_repair = None

    if len(trajectory) > 1:
        first_repair = trajectory[1]["policy"]

    first_failure_fixed = None

    if case["name"] == "guarded_reassoc" and first_repair is not None:
        first_failure_fixed = "reassoc" not in first_repair

    return {
        "case": case["name"],
        "mode": mode,
        "run": run_id,
        "passed": passed,
        "repair_turns": repair_turns,
        "final_policy": final_policy,
        "target_policy": case["target"],
        "minimal_repair":
            sorted(final_policy) ==
            sorted(case["target"]),
        "first_failure_fixed":
            first_failure_fixed,
        "input_tokens": total_in,
        "output_tokens": total_out,
        "trajectory": trajectory,
    }

rows = []

for case in CASES:
    for mode in [
        "bare",
        "counterexample",
    ]:
        for run_id in range(RUNS):
            print(
                "\n===",
                case["name"],
                mode,
                run_id,
                "===",
            )

            trajectory = run_episode(
                case["name"],
                case["initial"],
                feedback_mode=mode,
                max_turns=4,
            )

            rows.append(
                summarize(
                    case,
                    mode,
                    run_id,
                    trajectory,
                )
            )

with open(
    OUT / "experiment.json",
    "w",
) as f:
    json.dump(
        rows,
        f,
        indent=2,
    )

print("\nsaved:", OUT / "experiment.json")
