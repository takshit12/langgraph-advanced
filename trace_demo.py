# trace_demo.py — send your first traces to Langfuse.
#
# THE AHA: observability is *additive*. You do not rewrite the agent. You attach
# one CallbackHandler and pass it via config. LangGraph emits an event for every
# node it runs; the handler turns those into a nested trace in Langfuse.
#
# Run:  python trace_demo.py
# Then open your Langfuse project -> Tracing. You'll see one trace per message,
# each showing classify -> (router) -> handler -> finalize as nested spans, with
# the state at every step.

import os

from dotenv import load_dotenv

load_dotenv()  # pull LANGFUSE_* (and optional OPENROUTER_*) from .env

from langfuse import get_client
from langfuse.langchain import CallbackHandler

from agent import graph

MESSAGES = [
    "Hi there!",
    "My app is broken and I want a refund",
    "Which plan should I pick?",  # note: the buggy classifier mislabels this
]


def main() -> None:
    # Fail fast with a friendly message if keys are missing.
    missing = [k for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY") if not os.getenv(k)]
    if missing:
        raise SystemExit(
            f"Missing {missing} — copy .env.example to .env and paste your Langfuse keys."
        )

    client = get_client()
    try:
        # Optional connectivity check; guarded so a missing method never crashes the demo.
        if client.auth_check() is False:
            raise SystemExit("Langfuse auth failed — double-check keys and LANGFUSE_HOST region.")
    except AttributeError:
        pass

    # One handler can be reused across many invocations.
    handler = CallbackHandler()

    for msg in MESSAGES:
        result = graph.invoke(
            {"message": msg},
            # `callbacks` wires in Langfuse. `run_name` gives the trace a readable title.
            config={"callbacks": [handler], "run_name": f"demo: {msg[:30]}"},
        )
        print(f"{msg!r:45} -> {result['final']}")

    # Traces are sent in the background; flush before the script exits.
    client.flush()
    print("\n✅ Done. Open Langfuse -> Tracing to inspect the 3 traces node-by-node.")
    print("   (No LLM key? You'll still see the full graph trajectory — there's just")
    print("    no model 'generation' span on the question branch.)")


if __name__ == "__main__":
    main()
