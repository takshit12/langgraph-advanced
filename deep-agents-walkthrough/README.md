# Deep Agents Walkthrough

What turns a chatbot into an agent with the *stamina* to finish a long, multi-step
job? This walkthrough covers the four techniques behind modern "deep agents"
(Claude Code, Cursor, Manus, Deep Research) and then builds a working one.

The four pillars:

1. **A detailed system prompt** — a real job description, not a one-liner.
2. **A planning / to-do tool** — write the plan down and keep re-reading it.
3. **A file system** — offload work to "disk" instead of stuffing the context window.
4. **Sub-agents** — hire specialists and delegate.

The example agent is a **competitive-analysis deep agent**: name two companies and
it researches both from the open web and writes an executive-ready comparison.

## Learning path

| Step | Where | What |
|------|-------|------|
| 1. Theory | [`explainer.md`](./explainer.md) · [`deep_agents_overview.ipynb`](./deep_agents_overview.ipynb) | Why the four pillars work, with references and diagrams |
| 2. The build | [`competitive_analysis_agent/`](./competitive_analysis_agent) | A runnable deep agent that compares two companies |
| 3. The UI | [`setup-ui.sh`](./setup-ui.sh) | Spawn the visual [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) and watch the agent work live |

---

## Run it — step by step

> Verified with `deepagents 0.6.12`, `langchain 1.3`, `langgraph 1.2`, Python 3.13.

### 1. Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **git**, and **Node 20+** (only needed for the optional UI in step 5b)
- API keys (all have free tiers):
  - **OpenRouter** (model gateway) → https://openrouter.ai/keys — needs a small credit balance
  - **Tavily** (web search) → https://app.tavily.com — 1,000 free credits
  - **LangSmith** (tracing, *optional*) → https://smith.langchain.com

### 2. Install

```bash
cd competitive_analysis_agent
uv sync                     # creates .venv from uv.lock
```

### 3. Add your keys

The agent loads its environment from `deep-agents-walkthrough/.env` (one level up —
`langgraph.json` points at `../.env`). Copy the template and fill it in:

```bash
cp ../.env.example ../.env  # then edit ../.env
```

```env
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=openai/gpt-4.1-mini   # swap for openai/gpt-5, anthropic/claude-sonnet-4-6, ...
TAVILY_API_KEY=tvly-...
# optional tracing:
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_TRACING=true
```

### 4. Start the agent server

```bash
uv run langgraph dev
```

It prints three URLs — the **API** (`http://127.0.0.1:2024`), the **Studio UI**,
and the **API docs**. Leave this running. Sanity check in another terminal:

```bash
curl -s http://127.0.0.1:2024/ok        # -> {"ok":true}
```

### 5. Talk to it — pick one

**5a. Studio (fastest, nothing to install).** Open the Studio URL it printed,
select the `competitive_analysis_agent` graph, and send the demo prompt in step 6.

**5b. deep-agents-ui (richer — live to-do / files / sub-agent panels).** In a
second terminal, from this folder (`deep-agents-walkthrough/`):

```bash
./setup-ui.sh               # clones + installs the UI on first run, then starts it
```

Open <http://localhost:3000> and enter these in the settings dialog (saved in your
browser, so just once):

| Field | Value |
|-------|-------|
| Deployment URL | `http://127.0.0.1:2024` |
| Assistant ID | `competitive_analysis_agent` |
| LangSmith API Key | *optional* (auto-filled from `.env` if you set one) |

> `./setup-ui.sh --setup-only` installs without launching. The UI is a separate
> ~800 MB Node app, fetched on demand — it is **not** committed to this repo.

### 6. Run a request and watch the pillars fire

Send:

> *Create a comprehensive competitive analysis comparing Linear and Asana as
> project management solutions for product development teams.*

Watch the steps stream: `write_todos` (planning) → `task` → research sub-agents →
`internet_search` → `write_file` for `company_profiles.md` and
`competitive_analysis.md` → `task` → critique sub-agent → revise. The finished
files appear in the UI's / Studio's state view; a saved reference run is in
[`competitive_analysis_agent/example_output/`](./competitive_analysis_agent/example_output).

> **Cost & time:** this is a heavy job. The reference GPT-5 run took ~35 min,
> ~200 model calls, 12 sub-agents, ~287 searches (≈ $9). On `gpt-4.1-mini` it's far
> cheaper and faster with slightly less polish — set `OPENROUTER_MODEL` to trade
> cost for quality. There's no persistent storage: state clears when the run ends.

Full reference (every env var, troubleshooting) lives in
[`competitive_analysis_agent/README.md`](./competitive_analysis_agent/README.md).

---

## Credits

The example and theory are adapted from
[ALucek/deep-agents-walkthrough](https://github.com/ALucek/deep-agents-walkthrough),
built on LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents).
The agent code here has been updated for the current `deepagents` / LangChain 1.x
APIs and routes its model through OpenRouter.
