# chat.py — TALK to the agent interactively and watch traces show up in Langfuse.
#
# Why this exists: running trace_demo.py / evaluate.py feels disconnected — you run
# a script, then go look. This is a live loop: you type a message, the agent
# answers, and (if your Langfuse keys are in .env) that single turn is pushed to
# Langfuse immediately. Keep the Langfuse "Tracing" tab open on a second screen and
# watch a new trace pop up after every message you send.
#
# Run:  python chat.py
# Quit: type 'quit' / 'exit', or press Ctrl-C / Ctrl-D.

import os

from dotenv import load_dotenv

load_dotenv()  # pull LANGFUSE_* (+ optional OPENROUTER_*) from .env

from agent import graph


def _tracing():
    """Return (handler, client) if Langfuse keys are set, else (None, None)."""
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        print("⚠️  No Langfuse keys in .env — running WITHOUT tracing.")
        print("   Add LANGFUSE_PUBLIC_KEY / SECRET_KEY / HOST to .env to see traces.\n")
        return None, None
    from langfuse import get_client
    from langfuse.langchain import CallbackHandler

    # The SDK reads LANGFUSE_HOST, but falls back to LANGFUSE_BASE_URL (the var the
    # Langfuse UI snippet / CLI use). Show whichever is set so the region is honest.
    host = os.getenv("LANGFUSE_HOST") or os.getenv("LANGFUSE_BASE_URL") or "https://cloud.langfuse.com"
    print(f"✅ Tracing ON → {host}")
    print("   Open Langfuse → Tracing and watch a trace appear after each message.\n")
    return CallbackHandler(), get_client()


def main() -> None:
    handler, client = _tracing()
    print("Talk to the agent. Type a message and press Enter.  (quit = exit)\n")

    try:
        while True:
            msg = input("you > ").strip()
            if msg.lower() in {"quit", "exit"}:
                break
            if not msg:
                continue

            # run_name is the title you'll see in Langfuse; callbacks wire in tracing.
            config = {"run_name": f"chat: {msg[:40]}"}
            if handler:
                config["callbacks"] = [handler]

            result = graph.invoke({"message": msg}, config=config)
            print(f"bot > {result['final']}\n")

            if client:
                client.flush()  # push THIS turn now, so it appears in Langfuse within seconds
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        if client:
            client.flush()

    print("bye 👋")


if __name__ == "__main__":
    main()
