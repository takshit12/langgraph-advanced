# evaluate.py — a tiny, dependency-free evaluation harness.
#
# This is the heart of the session and the heart of the two articles:
#   "The tool is not the point. Looking at your traces and writing pass/fail
#    checks from REAL failures is where the work lives."
#
# What it does:
#   1. Loads a golden dataset (input + expected_output) from JSONL.
#   2. Runs each input through your compiled graph.
#   3. Scores the output with deterministic, binary "code evaluators"
#      (exact-match on intent and sentiment) — no LLM, no API key, no Langfuse.
#   4. Prints a per-item table, aggregate accuracy, and a FAILURES section
#      so you can do error analysis (cluster failures by their cause).
#
# Run the baseline (the buggy classifier):
#   python evaluate.py
# Run the fixed classifier and compare:
#   python evaluate.py --agent agent_improved
#
# The evaluator functions below are imported by langfuse_experiment.py too, so the
# SAME logic powers both the local run and the Langfuse-backed run. That's the
# point: Langfuse stores and compares your evals; it does not invent them.

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple


# --- Code evaluators: plain functions returning True/False ------------------
# A "good eval" per Hamel/Lucek is binary and derived from a real failure mode.
def intent_correct(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    return (actual or {}).get("intent") == (expected or {}).get("intent")


def sentiment_correct(expected: Dict[str, Any], actual: Dict[str, Any]) -> bool:
    return (actual or {}).get("sentiment") == (expected or {}).get("sentiment")


EVALUATORS: Dict[str, Callable[[Dict, Dict], bool]] = {
    "intent": intent_correct,
    "sentiment": sentiment_correct,
}


# --- Dataset loading --------------------------------------------------------
def load_dataset(path: str) -> List[Dict[str, Any]]:
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            items.append(json.loads(line))
    return items


# --- Tiny formatting helpers (no pandas / rich needed) ----------------------
def _trunc(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def _mark(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def run(agent_module: str, dataset_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, int], int]:
    graph = importlib.import_module(agent_module).graph
    data = load_dataset(dataset_path)

    results: List[Dict[str, Any]] = []
    totals = {k: 0 for k in EVALUATORS}

    for item in data:
        out = graph.invoke(item["input"])
        exp = item["expected_output"]
        scores = {name: fn(exp, out) for name, fn in EVALUATORS.items()}
        for name, ok in scores.items():
            totals[name] += int(ok)
        results.append({"item": item, "out": out, "scores": scores})

    return results, totals, len(data)


def print_report(agent_module: str, results, totals, n) -> None:
    print(f"\n=== Evaluation: agent module = {agent_module!r} | {n} items ===\n")

    # Per-item table.
    header = f"{'id':<5} {'message':<42} {'intent (exp/got)':<26} {'sentiment (exp/got)':<28}"
    print(header)
    print("-" * len(header))
    for r in results:
        item, out, scores = r["item"], r["out"], r["scores"]
        meta = item.get("metadata", {})
        exp = item["expected_output"]
        msg = _trunc(item["input"]["message"], 41)
        intent_cell = f"{_mark(scores['intent'])} {exp['intent']}/{out.get('intent')}"
        sent_cell = f"{_mark(scores['sentiment'])} {exp['sentiment']}/{out.get('sentiment')}"
        print(f"{meta.get('id',''):<5} {msg:<42} {_trunc(intent_cell,25):<26} {_trunc(sent_cell,27):<28}")

    # Aggregate scores.
    print("\n--- Aggregate accuracy ---")
    for name in EVALUATORS:
        pct = 100.0 * totals[name] / n if n else 0.0
        print(f"  {name:<10}: {totals[name]}/{n}  ({pct:.1f}%)")

    # Failures, for error analysis.
    failures = [r for r in results if not all(r["scores"].values())]
    print(f"\n--- FAILURES ({len(failures)}) — cluster these by cause ---")
    if not failures:
        print("  none 🎉")
    for r in failures:
        item, out, scores = r["item"], r["out"], r["scores"]
        meta = item.get("metadata", {})
        exp = item["expected_output"]
        print(f"\n  [{meta.get('id','')}] {item['input']['message']!r}")
        if meta.get("note"):
            print(f"        note: {meta['note']}")
        if not scores["intent"]:
            print(f"        intent   : expected={exp['intent']!r:>12}  got={out.get('intent')!r}")
        if not scores["sentiment"]:
            print(f"        sentiment: expected={exp['sentiment']!r:>12}  got={out.get('sentiment')!r}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a LangGraph agent against a golden dataset.")
    parser.add_argument("--agent", default="agent", help="module exposing a compiled `graph` (e.g. 'agent' or 'agent_improved')")
    parser.add_argument("--dataset", default="golden_dataset.jsonl")
    args = parser.parse_args()

    results, totals, n = run(args.agent, args.dataset)
    print_report(args.agent, results, totals, n)


if __name__ == "__main__":
    main()
