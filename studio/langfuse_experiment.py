# langfuse_experiment.py — run the SAME eval, but push it to Langfuse.
#
# evaluate.py proves you own the eval logic. This file shows what the platform
# buys you on top: every item becomes a trace, every check becomes a score, and
# two runs (baseline vs improved) sit side-by-side in the Langfuse UI so you can
# see the regression/improvement at a glance and drill into any failing trace.
#
# It reuses intent_correct / sentiment_correct from evaluate.py — no duplicated
# logic. Langfuse's run_experiment() handles the looping, tracing, and scoring.
#
# Run the baseline, then the fix, then compare in the UI:
#   python langfuse_experiment.py --agent agent
#   python langfuse_experiment.py --agent agent_improved
#
# Requires LANGFUSE_* keys in .env (see .env.example). Needs Python 3.11+.

import argparse
import importlib

from dotenv import load_dotenv

load_dotenv()

from langfuse import Evaluation, get_client
from langfuse.langchain import CallbackHandler

from evaluate import intent_correct, load_dataset, sentiment_correct


def build_task(agent_module: str):
    """Return a task(item) that runs the chosen graph and returns its final state."""
    graph = importlib.import_module(agent_module).graph

    def task(*, item, **kwargs):
        # item is a plain dict for local data: item["input"] == {"message": ...}
        # Attaching the handler nests the node-level spans under this item's trace,
        # so each experiment trace shows classify -> route -> handler -> finalize.
        handler = CallbackHandler()
        return graph.invoke(item["input"], config={"callbacks": [handler]})

    return task


# --- Evaluators: wrap the plain True/False checks as Langfuse Evaluations -----
# Booleans are sent as 1.0 / 0.0 so Langfuse can average them into an accuracy.
def intent_evaluator(*, input, output, expected_output, metadata=None, **kwargs):
    ok = intent_correct(expected_output, output)
    return Evaluation(
        name="intent_correct",
        value=1.0 if ok else 0.0,
        comment=f"expected={expected_output.get('intent')} got={(output or {}).get('intent')}",
    )


def sentiment_evaluator(*, input, output, expected_output, metadata=None, **kwargs):
    ok = sentiment_correct(expected_output, output)
    return Evaluation(
        name="sentiment_correct",
        value=1.0 if ok else 0.0,
        comment=f"expected={expected_output.get('sentiment')} got={(output or {}).get('sentiment')}",
    )


# --- Run-level evaluator: aggregate accuracy across the whole run ------------
def overall_accuracy(*, item_results, **kwargs):
    checks = [
        e.value
        for r in item_results
        for e in r.evaluations
        if e.name in ("intent_correct", "sentiment_correct") and e.value is not None
    ]
    if not checks:
        return Evaluation(name="overall_accuracy", value=None)
    avg = sum(checks) / len(checks)
    return Evaluation(name="overall_accuracy", value=avg, comment=f"{avg:.1%} of all checks passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default="agent", help="'agent' or 'agent_improved'")
    parser.add_argument("--dataset", default="golden_dataset.jsonl")
    args = parser.parse_args()

    data = load_dataset(args.dataset)
    langfuse = get_client()

    result = langfuse.run_experiment(
        name="intent-classifier-eval",
        run_name=args.agent,  # shows up as the run label in Langfuse
        description="Keyword intent/sentiment classifier vs the golden dataset",
        data=data,
        task=build_task(args.agent),
        evaluators=[intent_evaluator, sentiment_evaluator],
        run_evaluators=[overall_accuracy],
        metadata={"agent_module": args.agent},
    )

    # Human-readable summary in the terminal...
    print(result.format())
    # ...and make sure everything is delivered to Langfuse before we exit.
    langfuse.flush()
    print("\n✅ Open Langfuse -> Tracing (filter by the scores) to inspect each item,")
    print("   or run this again with --agent agent_improved and compare the two runs.")


if __name__ == "__main__":
    main()
