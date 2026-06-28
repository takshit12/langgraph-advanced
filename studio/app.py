# app.py — wrap the compiled LangGraph `graph` in a REST API.
#
# THE WHOLE POINT: a compiled LangGraph graph is just a Python object with
# `.invoke()` and `.stream()`. "Deploying an agent" is nothing more exotic than
# putting that object behind an HTTP endpoint. You do NOT need LangGraph Platform
# / LangSmith Deployments to ship — any web framework will do. Here we use
# FastAPI, then containerise with the Dockerfile next to this file.
#
# Run locally (no Docker):
#   uvicorn app:app --reload --port 8000
# Then open http://127.0.0.1:8000/docs for an auto-generated Swagger UI.

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()  # pull LANGFUSE_* from .env so the deployed API can trace too

# Import the SAME graph students built last session. No changes to agent.py.
from agent import graph

app = FastAPI(
    title="LangGraph Agent API",
    description="A compiled LangGraph graph served over HTTP. No vendor runtime required.",
    version="1.0.0",
)


# ---  Langfuse tracing -----------------------------------------------
# Observability is still ADDITIVE here: if Langfuse keys are present we attach a
# callback handler so every API call becomes a trace; if not (or langfuse isn't
# installed, e.g. in the lean container), we run untraced. Lazy import keeps the
# slim requirements-api.txt image working without langfuse.
def _config(run_name: str) -> dict:
    cfg = {"run_name": run_name}
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        try:
            from langfuse.langchain import CallbackHandler

            cfg["callbacks"] = [CallbackHandler()]
        except Exception:
            pass  # langfuse not installed in this image — serve without tracing
    return cfg


# --- Request / response schemas (FastAPI validates these for you) -----------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: Optional[str] = None
    sentiment: Optional[str] = None
    response: Optional[str] = None
    final: Optional[str] = None


# --- Health check: the first thing any orchestrator (Docker/K8s) will hit ---
@app.get("/health")
def health():
    return {"status": "ok"}


# --- The core endpoint: run the graph once, return the final state ----------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # graph.invoke runs START -> classify -> (router) -> handler -> finalize -> END
    # and returns the fully-merged state dict.
    result = graph.invoke({"message": req.message}, config=_config("api:/chat"))
    return ChatResponse(
        intent=result.get("intent"),
        sentiment=result.get("sentiment"),
        response=result.get("response"),
        final=result.get("final"),
    )


# --- Bonus: stream the graph node-by-node over Server-Sent Events -----------
# graph.stream() yields one chunk per node as it finishes: {node_name: partial_state}.
# This is the same node-by-node execution you watched in Studio, but over the wire.
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    import json

    def event_generator():
        for chunk in graph.stream({"message": req.message}, config=_config("api:/chat/stream")):
            yield f"data: {json.dumps(chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    # Allows `python app.py` as an alternative to the uvicorn CLI.
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
