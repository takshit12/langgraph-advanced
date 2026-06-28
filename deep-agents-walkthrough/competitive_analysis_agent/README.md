# Competitive Analysis Agent

A **deep agent** that researches two companies from the open web and writes an
executive-ready comparison. It plans its work, delegates to research and critique
sub-agents, and saves its drafts to a virtual file system — all built on
[`deepagents`](https://github.com/langchain-ai/deepagents) +
[LangGraph](https://docs.langchain.com/langgraph-platform).

New to the concepts? Read the theory in [`../explainer.md`](../explainer.md) and
the notebook [`../deep_agents_overview.ipynb`](../deep_agents_overview.ipynb).

> Verified with `deepagents 0.6.12`, `langchain 1.3`, `langgraph 1.2`, Python 3.13.

---

## 1. Prerequisites

- **Python 3.13** (see `.python-version`)
- **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- API keys (all have free tiers):
  - **OpenRouter** — the model gateway → https://openrouter.ai/keys (needs a small credit balance)
  - **Tavily** — web search → https://app.tavily.com (1,000 free credits)
  - **LangSmith** *(optional, for tracing)* → https://smith.langchain.com

## 2. Install

From this directory:

```bash
cd deep-agents-walkthrough/competitive_analysis_agent
uv sync
```

That creates `.venv/` with the exact pinned versions from `uv.lock`.

## 3. Configure environment

`langgraph.json` loads its environment from **`../.env`** — i.e. the file lives at
`deep-agents-walkthrough/.env` (one level up), shared with the notebook. Copy the
template and fill it in:

```bash
cp ../.env.example ../.env   # then edit ../.env
```

```env
# Model gateway (required)
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4.1-mini   # any OpenRouter model id

# Web search (required for the agent to actually research)
TAVILY_API_KEY=tvly-...

# LangSmith tracing (optional but recommended)
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_PROJECT=deep_competitive_analysis
```

> **Model note:** the original walkthrough used GPT-5 directly. This version routes
> through OpenRouter so you can swap models with a single env var. `gpt-4.1-mini`
> is a cheap, fast default for demos; set `OPENROUTER_MODEL` to anything OpenRouter
> serves (e.g. `openai/gpt-5`, `anthropic/claude-sonnet-4-6`) for higher quality.

## 4. Run the server

```bash
uv run langgraph dev
```

Wait for it to print three URLs:

- **API** → `http://127.0.0.1:2024`
- **Studio UI** → `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`
- **API docs** → `http://127.0.0.1:2024/docs`

Quick health check in another terminal:

```bash
curl -s http://127.0.0.1:2024/ok          # -> {"ok":true}
```

## 5. Talk to it

**Option A — Studio (easiest, nothing to install).** Open the Studio URL, select
the `competitive_analysis_agent` graph, and send a request such as:

> *Create a comprehensive competitive analysis comparing Linear and Asana as
> project management solutions for product development teams.*

Watch the steps stream: `write_todos` (planning) → `task` → research sub-agents →
`internet_search` → `write_file` (drafts) → `task` → critique sub-agent → revise.

**Option B — deep-agents-ui (richer chat UI with live to-do / files / sub-agent
panels).** With `langgraph dev` running, in a separate terminal run the helper
(it clones, installs, and launches the UI — requires git + Node 20+):

```bash
cd ..            # into deep-agents-walkthrough/
./setup-ui.sh
```

Open <http://localhost:3000> and enter these in the UI's settings dialog (saved in
your browser after the first time):

| Field | Value |
|-------|-------|
| Deployment URL | `http://127.0.0.1:2024` |
| Assistant ID | `competitive_analysis_agent` |
| LangSmith API Key | *optional* (auto-filled from `../.env` if set) |

## 6. What to expect

The agent produces two documents — `company_profiles.md` and
`competitive_analysis.md` — written to its in-memory file system (visible in
Studio's state view). A saved reference run is in
[`example_output/`](./example_output).

This is a **heavy** workload by design. The reference GPT-5 run took ~35 minutes,
~200 model calls, 12 sub-agents, and ~287 web searches (≈ $9). On `gpt-4.1-mini`
it's far cheaper and faster, with slightly less polish — same machinery end to end.

> _Note: there is no persistent storage. All files and conversation state are
> cleared when the run/session ends._

---

## Files

| File | What it is |
|------|------------|
| `competitive_analysis_agent.py` | The whole agent — search tool, prompts, sub-agents, `create_deep_agent(...)` |
| `langgraph.json` | LangGraph platform config (graph entrypoint + `env: ../.env`) |
| `pyproject.toml` / `uv.lock` | Dependencies, pinned |
| `requirements.txt` | Same deps for non-uv installs (`pip install -r requirements.txt`) |
| `example_output/` | A saved reference run (Linear vs Asana) |

## Troubleshooting

- **`402 Insufficient credits`** — add a little balance to your OpenRouter account.
- **Search returns nothing / auth error** — `TAVILY_API_KEY` is missing or invalid in `../.env`.
- **Graph won't load / env not picked up** — confirm the file is `deep-agents-walkthrough/.env` (not inside this folder); `langgraph.json` points at `../.env`.
- **`uv sync` resolves old packages** — you're on an old lockfile; `uv lock` then `uv sync` to refresh.
