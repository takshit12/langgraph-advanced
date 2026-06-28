# agent_improved.py — the SAME graph as agent.py, with a fixed classifier.
#
# Only the two helper functions (classify_intent / classify_sentiment) and the
# keyword lists changed. The graph wiring, nodes, and state are byte-for-byte the
# same as agent.py — which is the lesson: evals point at the bug, you fix the
# small thing that's actually wrong, and you re-run the SAME dataset to confirm.
#
# Three fixes, each killing one cluster of failures the baseline produced:
#
#   FIX 1 — Word-boundary matching (kills substring false-positives).
#     Baseline used `keyword in text`, so "hi" matched inside "tHIs", "wHIch",
#     "sHIp"; "good" matched inside "GOODbye". We now match whole words only.
#
#   FIX 2 — Intent priority (kills the "Hi, my app is broken" ordering bug).
#     Baseline checked greeting BEFORE complaint, so any complaint that opened
#     with "Hi" was filed as a greeting. We now check complaint > farewell >
#     greeting, so the most actionable label wins.
#
#   FIX 3 — Expanded keyword lists (kills false-negatives like "furious"/"worst").
#     Real complaints rarely use your exact seed words. We add a few. NOTE this
#     is whack-a-mole — see the negation case ("I do not hate it") that STILL
#     fails. That residual is the honest motivation for an LLM classifier, which
#     you would then evaluate with this exact same harness.
import os
import re
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, START, END


class ChatState(TypedDict):
    message: Optional[str]
    intent: Optional[str]
    sentiment: Optional[str]
    response: Optional[str]
    final: Optional[str]


# --- FIX 3: a few more real-world keywords -----------------------------------
# Order of INTENT_KEYWORDS now encodes PRIORITY (FIX 2): complaint first.
INTENT_KEYWORDS = {
    "complaint": [
        "broken", "bug", "angry", "refund", "terrible", "not working", "hate",
        "furious", "worst", "unusable", "never arrived",  # added
    ],
    "farewell": ["bye", "goodbye", "see you", "cya", "later"],
    "greeting": ["hello", "hi", "hey", "hiya", "good morning", "good evening"],
}

POSITIVE = ["great", "love", "thanks", "thank you", "awesome", "good", "nice", "fine", "perfect"]
NEGATIVE = ["broken", "bug", "angry", "terrible", "hate", "bad", "refund", "furious", "worst", "unusable"]


# --- FIX 1: match whole words/phrases, not raw substrings ---------------------
def _has(text: str, phrase: str) -> bool:
    """True if `phrase` appears in `text` on word boundaries (case-insensitive)."""
    return re.search(r"\b" + re.escape(phrase.lower()) + r"\b", text.lower()) is not None


def classify_intent(text: str) -> str:
    # Dict preserves insertion order, so this honours the priority in INTENT_KEYWORDS.
    for intent, words in INTENT_KEYWORDS.items():
        if any(_has(text, w) for w in words):
            return intent
    return "question"


def classify_sentiment(text: str) -> str:
    pos = any(_has(text, w) for w in POSITIVE)
    neg = any(_has(text, w) for w in NEGATIVE)
    if neg and not pos:
        return "negative"
    if pos and not neg:
        return "positive"
    return "neutral"


# --- Nodes (unchanged from agent.py) -----------------------------------------
def classify_node(state: ChatState) -> dict:
    message = (state.get("message") or "").strip()
    return {"intent": classify_intent(message), "sentiment": classify_sentiment(message)}


def greeting_node(state: ChatState) -> dict:
    return {"response": "Hello! 👋 What can I help you with today?"}


def farewell_node(state: ChatState) -> dict:
    return {"response": "Thanks for stopping by — goodbye! 👋"}


def complaint_node(state: ChatState) -> dict:
    return {
        "response": (
            "I'm sorry you're having trouble. I've logged this as a complaint "
            "and a human will follow up. Could you share more detail?"
        )
    }


def question_node(state: ChatState) -> dict:
    message = (state.get("message") or "").strip()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        try:
            # Prefer Langfuse's drop-in so the model call is traced as a
            # GENERATION (what LLM-as-a-judge evaluators score); fall back to the
            # plain SDK in the lean container where langfuse isn't installed.
            try:
                from langfuse.openai import OpenAI
            except ImportError:
                from openai import OpenAI

            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
            completion = client.chat.completions.create(
                model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
                messages=[{"role": "user", "content": message}],
            )
            return {"response": completion.choices[0].message.content}
        except Exception as exc:
            return {"response": f"(LLM unavailable: {exc}) You asked: '{message}'"}
    return {"response": f"Here's what I found for: '{message}' (offline demo answer)."}


def finalize_node(state: ChatState) -> dict:
    intent = state.get("intent")
    sentiment = state.get("sentiment")
    response = state.get("response") or ""
    return {"final": f"[intent={intent} | sentiment={sentiment}] {response}"}


def route_by_intent(state: ChatState) -> str:
    return state.get("intent") or "question"


# --- Build the graph (identical wiring to agent.py) --------------------------
workflow = StateGraph(ChatState)
workflow.add_node("classify", classify_node)
workflow.add_node("greeting", greeting_node)
workflow.add_node("farewell", farewell_node)
workflow.add_node("complaint", complaint_node)
workflow.add_node("question", question_node)
workflow.add_node("finalize", finalize_node)

workflow.add_edge(START, "classify")
workflow.add_conditional_edges(
    "classify",
    route_by_intent,
    {"greeting": "greeting", "farewell": "farewell", "complaint": "complaint", "question": "question"},
)
workflow.add_edge("greeting", "finalize")
workflow.add_edge("farewell", "finalize")
workflow.add_edge("complaint", "finalize")
workflow.add_edge("question", "finalize")
workflow.add_edge("finalize", END)

graph = workflow.compile()


if __name__ == "__main__":
    for msg in ["Hi there!", "Hi, my app is broken", "Which plan should I pick?"]:
        print(msg, "->", graph.invoke({"message": msg})["final"])
