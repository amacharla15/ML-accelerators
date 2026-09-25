import json

rows = json.load(open(
    "results/experiment_100episodes.json"
))

out = {
    "overall": {},
    "guarded_reassoc": {},
}

for mode in ["bare", "counterexample"]:
    rs = [
        r for r in rows
        if r["mode"] == mode
    ]

    hard = [
        r for r in rs
        if r["case"] == "guarded_reassoc"
    ]

    turns = [
        r["repair_turns"]
        for r in rs
    ]

    out["overall"][mode] = {
        "episodes": len(rs),
        "verified": sum(r["passed"] for r in rs),
        "minimal_repairs":
            sum(r["minimal_repair"] for r in rs),
        "mean_repair_turns":
            sum(turns) / len(turns),
        "input_tokens":
            sum(r["input_tokens"] for r in rs),
        "output_tokens":
            sum(r["output_tokens"] for r in rs),
    }

    out["guarded_reassoc"][mode] = {
        "episodes": len(hard),
        "verified": sum(r["passed"] for r in hard),
        "minimal_repairs":
            sum(r["minimal_repair"] for r in hard),
        "first_failure_fixed":
            sum(r["first_failure_fixed"] for r in hard),
        "mean_repair_turns":
            sum(r["repair_turns"] for r in hard)
            / len(hard),
    }

with open("results/summary.json", "w") as f:
    json.dump(out, f, indent=2)

print(json.dumps(out, indent=2))
