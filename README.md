# LangGraph Advanced — Deploy → Observe → Evaluate → Improve

A hands-on kit that takes **one** small LangGraph agent through the rest of its
lifecycle: ship it as a real service, watch it in production, measure it against
examples you trust, and fix it with error analysis instead of guesswork.

It's the sequel to a "basics" session where the same agent ran locally and in
**LangGraph Studio** via `langgraph dev`. A dev server is great for building — it
is not how anything ships. This repo is the next four steps.

```
   DEPLOY            OBSERVE            EVALUATE           IMPROVE
  FastAPI +    →    Langfuse      →   golden set +   →   error analysis
   Docker          tracing          code evaluators      → fix → re-run
```

### The payoff

The classifier in `agent.py` is **deliberately buggy**. The evaluation step finds
the bugs *for you*. By doing error analysis on real failures — not by guessing —
you watch the scores jump:

| Agent                | Intent accuracy | Sentiment accuracy | Failures |
|----------------------|-----------------|--------------------|----------|
| `agent.py`           | 6/14 (**42.9%**) | 11/14 (**78.6%**)  | 8        |
| `agent_improved.py`  | 13/14 (**92.9%**) | 14/14 (**100%**)   | 1        |

That **43% → 93%** jump, arrived at without a single guess, is the whole point.
The one residual failure (`g11`, *"I do not hate it"*) is left broken on
purpose — negation is the wall keyword matching can't climb, and the reason you'd
reach for an LLM classifier next.

> **The meta-lesson:** the tool is not the point. Langfuse and LangSmith are just
> places to store traces and scores. The work — looking at your own outputs and
> writing pass/fail checks from real failures — is where the quality comes from.

---

## The agent

A four-way keyword classifier graph — no LLM in the hot path, so it runs offline
with zero API keys:

```
START → classify → (router) → { greeting | farewell | complaint | question } → finalize → END
```

- **State** — a `TypedDict` that flows through the graph, merged at each node.
- **Nodes** — plain `state -> partial-state` functions.
- **Conditional edge** — a router that picks the branch by the classified intent.
- **Compile** — `graph = workflow.compile()`, a runnable object with `.invoke()`
  and `.stream()`. That object is the only thing the rest of this repo needs.

---

## Prerequisites

You need **Python 3.11+** (langfuse v3 requires it) and **git**. **Docker** is
optional — only the container step uses it. `pip`, `venv`, and `curl` already ship
with Python or your OS.

### Step 1 — check what you already have

If Python prints **3.11 or higher** and git prints a version, skip straight to
[Quickstart](#quickstart) — you're set.

**macOS / Linux** (Terminal):

```bash
python3 --version     # need 3.11 or higher
git --version
docker --version      # optional — only for the container step
```

**Windows** (PowerShell):

```powershell
python --version      # need 3.11 or higher
git --version
docker --version      # optional
```

### Step 2 — install whatever is missing

**macOS** — easiest via [Homebrew](https://brew.sh) (install it once with the
one-liner on that page), then:

```bash
brew install python@3.12 git
brew install --cask docker      # optional — then launch Docker Desktop once
```

**Windows** — use `winget` (built into Windows 10/11):

```powershell
winget install Python.Python.3.12
winget install Git.Git
winget install Docker.DockerDesktop     # optional — then launch Docker Desktop once
```

Prefer clicking installers? Grab [Python](https://www.python.org/downloads/)
(**tick "Add python.exe to PATH"** in the installer),
[Git](https://git-scm.com/download/win), and
[Docker Desktop](https://www.docker.com/products/docker-desktop/).

> After installing, **close and reopen your terminal** so the new tools land on
> your PATH, then re-run the Step 1 checks. On macOS, `python3`/`pip3`; on
> Windows, `python`/`pip`.

---

## Quickstart

All the code lives in **`studio/`** (it holds `agent.py` and every kit file) —
run every command below from there.

```bash
git clone https://github.com/takshit12/langgraph-advanced.git
cd langgraph-advanced/studio
```

Create and activate a virtual environment:

Use a **Python 3.11+** interpreter — the macOS system `python3` is often 3.9,
which can't install langgraph 1.x. Check with `python3 --version` first.

**macOS / Linux:**

```bash
python3.11 -m venv .venv && source .venv/bin/activate   # or any python3.11+
python --version                                        # confirm 3.11+
```

**Windows (PowerShell):**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If PowerShell blocks the activate script, run
> `Set-ExecutionPolicy -Scope Process RemoteSigned` first (affects only the
> current window), or use Command Prompt: `.venv\Scripts\activate.bat`.

Then install the dependencies and create your `.env`:

```bash
pip install -r requirements.txt
cp .env.example .env          # Windows: copy .env.example .env
```

Your `.env` needs a Langfuse public/secret pair and the **region-matched** host
(see `.env.example`). OpenRouter is optional — without it, the `question` branch
returns a deterministic offline answer so every demo still works.

---

## 1 · Deploy — run the agent as an HTTP service

A compiled graph is just a Python object, so "deploying" is wrapping it in a web
server — no LangGraph Platform or LangSmith runtime required. `app.py` imports the
**unchanged** `agent.py` and exposes it over FastAPI.

```bash
uvicorn app:app --reload --port 8000        # then open http://127.0.0.1:8000/docs
```

> **Windows:** the multi-line `curl` snippets below use bash line-continuations
> (`\`). Run them in **Git Bash**, or skip them and use the interactive Swagger UI
> at <http://127.0.0.1:8000/docs> → **Try it out**.

```bash
curl -s localhost:8000/health

curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message": "My app is broken and I want a refund"}'

# node-by-node over Server-Sent Events (same as watching it run in Studio):
curl -N -X POST localhost:8000/chat/stream \
  -H 'content-type: application/json' \
  -d '{"message": "Hi, my app is broken and unusable"}'
```

Containerize it (ships anywhere a container runs — VPS, ECS, Cloud Run, K8s):

```bash
docker build -t langgraph-agent .
docker run -p 8000:8000 --env-file .env langgraph-agent
```

**Endpoints:** `GET /health` · `POST /chat` · `POST /chat/stream`.
Port busy? Use `--port 8001` (uvicorn) or `-p 8001:8000` (docker).

---

## 2 · Observe — send traces to Langfuse

Observability is *additive*: you bolt it on without touching the agent's logic.
The entire integration is one callback handler passed via `config`:

```python
from langfuse.langchain import CallbackHandler   # v3 import path
from langfuse import get_client

handler = CallbackHandler()                       # reads keys from .env
graph.invoke({"message": msg}, config={"callbacks": [handler], "run_name": "demo"})
get_client().flush()                              # push before the script exits
```

```bash
python trace_demo.py     # then open Langfuse → Tracing and click into a trace
```

You'll see `classify → handler → finalize` as nested spans, with inputs, outputs,
and latency per node.

> **One honest seam:** the `question` node calls OpenRouter through the raw OpenAI
> SDK, so the callback handler traces the *node* but not the LLM *generation*
> inside it. To capture the model call too, swap the import inside `question_node`
> to `from langfuse.openai import OpenAI` — that wrapper is auto-instrumented.

---

## 3 · Evaluate — score against a golden dataset

`golden_dataset.jsonl` is 14 hand-written examples, each with an `input` and the
`expected_output` (intent + sentiment). `evaluate.py` is intentionally
**dependency-free** (no Langfuse, no API key) so the concept is naked: load the
dataset, run each input through the graph, compare with exact-match **code
evaluators**, print a table + aggregate + a failures section.

```bash
python evaluate.py
# → intent 6/14 (42.9%), sentiment 11/14 (78.6%), 8 failures
```

Read the **FAILURES** section and cluster them by *cause*, not symptom.

---

## 4 · Improve — fix the clusters, re-run, compare

The 8 failures cluster into three named bugs. `agent_improved.py` is the **same
graph wiring** with three surgical fixes:

| Fix | Cluster it kills |
|-----|------------------|
| Word-boundary matching (`\bword\b`) | `"hi"` matching inside "t**hi**s", "s**hi**p", "w**hi**ch" |
| Intent priority (check **complaint** before greeting) | "Hi, my app is broken" filed as a greeting |
| Expanded keywords (`furious`, `worst`, `unusable`, …) | real complaints using unseen words |

```bash
python evaluate.py --agent agent_improved
# → intent 13/14 (92.9%), sentiment 14/14 (100%), 1 failure
```

The 1 remaining failure (`g11` *"I do not hate it, it works fine now"*) is
**negation** — you cannot keyword your way out of language. That's the honest
bridge to an LLM classifier, which you'd then evaluate against this *same* dataset
to prove it actually helps.

---

## 5 · (Optional) Langfuse experiments — track scores over time

Same dataset, same evaluators as `evaluate.py` — but pushed to Langfuse as an
experiment, so runs are recorded, versioned, and comparable run-over-run:

```bash
python langfuse_experiment.py --agent agent
python langfuse_experiment.py --agent agent_improved
```

Open Langfuse to see the two runs side by side.

---

## Project structure

Everything lives in `studio/` — `cd` there to run any command:

```
langgraph-advanced/
├── README.md          ← repo overview (this file)
└── studio/            ← the kit; the langgraph.json app root
    ├── agent.py       ← run all commands from here
    └── …
```

| File (in `studio/`) | What it is |
|------|------------|
| `agent.py` | the buggy 4-way classifier (the eval subject) |
| `agent_improved.py` | the fixed version — same graph, three surgical fixes |
| `app.py` | FastAPI wrapper: `/health`, `/chat`, `/chat/stream` |
| `Dockerfile` / `.dockerignore` | lean container build |
| `requirements.txt` / `requirements-api.txt` | full local deps / lean runtime deps |
| `langgraph.json` | lets `langgraph dev` open the agent in Studio |
| `.env.example` | env template (copy to `.env`) |
| `trace_demo.py` | minimal Langfuse tracing demo |
| `golden_dataset.jsonl` | 14 labeled examples |
| `evaluate.py` | dependency-free eval harness |
| `langfuse_experiment.py` | same eval, pushed to Langfuse |

---

## Where to go next — deployment portability

FastAPI-around-the-graph (this repo) is the most portable and most DIY option. If
you want managed niceties (durable run queue, built-in human-in-the-loop endpoints,
stream reconnection) *without* vendor lock-in, two open-source paths:

- **Standalone LangGraph server** you run yourself via Docker / Compose / K8s
  (their docs warn against running it serverless / scale-to-zero).
- **[Aegra](https://github.com/ibbybuilds/aegra)** — a FastAPI + Postgres drop-in
  for LangGraph Platform that speaks the open Agent Protocol, so your client code
  doesn't change.

The decision is just: how much of that managed machinery do you actually need,
versus rebuild only the pieces you use.

---

## Troubleshooting

- **Langfuse shows no traces** → 9 times out of 10 it's the **region host**.
  `LANGFUSE_HOST` must match where you created the account (EU / US / JP). Then
  check the keys (`pk-lf-…` / `sk-lf-…`), `langfuse>=3`, and Python 3.11+.
- **Eval numbers don't match the table** → someone edited `agent.py` or the
  dataset. The 43→93 story depends on them being byte-for-byte as shipped.
- **`ModuleNotFoundError: agent`** → run commands from inside `studio/`, next to
  `agent.py`.
- **Port already in use** → `--port 8001` (uvicorn) / `-p 8001:8000` (docker).

---

*Built for a live, hands-on LangGraph session. The deploy is the easy 20%. The
loop on the right — golden set, code evaluators, read the failures, fix the
cluster, measure again — is the actual craft.*
