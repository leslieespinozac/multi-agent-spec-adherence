"""
run_eval.py
-----------
Main entry point. Loads the agent specifications and scenarios, asks each agent
to respond to each scenario (via the mock or real model), scores whether agents
stayed in their roles, and writes a results summary.

Usage:
    python run_eval.py            # runs with the mock model (no API key needed)
    python run_eval.py --real     # runs against a real model (requires setup; see README)

Output:
    Prints a readable summary to the screen and writes results/results.json.
"""

import json
import os
import sys

from model import MockModel, RealModel
from scorer import score_scenario


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_agents():
    """Load every agent specification in the agents/ folder."""
    agents = {}
    for filename in os.listdir("agents"):
        if filename.endswith(".json"):
            spec = load_json(os.path.join("agents", filename))
            agents[spec["name"]] = spec
    return agents


def run(use_real_model=False):
    agents = load_agents()
    scenarios = load_json("scenarios/scenarios.json")["scenarios"]
    model = RealModel() if use_real_model else MockModel()

    results = []
    print("\n=== Specification-Adherence Eval ===")
    print(f"Model backend: {'REAL' if use_real_model else 'MOCK (illustrative only)'}\n")

    for scenario in scenarios:
        # Ask every agent to respond to this scenario.
        responses = {}
        for name, spec in agents.items():
            responses[name] = model.get_response(
                name, spec["system_prompt"], scenario["user_message"]
            )

        result = score_scenario(scenario, responses)
        result["responses"] = responses
        results.append(result)

        # Print a readable line per scenario.
        status = "PASS" if result["passed"] else "FAIL"
        detail = "" if result["passed"] else f"  ->  {', '.join(result['failures'])}"
        print(f"[{result['stakes'].upper():6}] {result['scenario_id']:28} {status}{detail}")

    # Summary statistics.
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    high_stakes = [r for r in results if r["stakes"] == "high"]
    high_passed = sum(1 for r in high_stakes if r["passed"])

    print(f"\nPassed {passed}/{total} scenarios.")
    if high_stakes:
        print(f"High-stakes scenarios passed: {high_passed}/{len(high_stakes)}")
    print("Full results written to results/results.json\n")

    os.makedirs("results", exist_ok=True)
    with open("results/results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    use_real = "--real" in sys.argv
    run(use_real_model=use_real)
