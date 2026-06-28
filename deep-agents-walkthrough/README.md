# Deep Agents Walkthrough

What turns a chatbot into an agent with the *stamina* to finish a long, multi-step
job? This walkthrough covers the four techniques behind modern "deep agents"
(Claude Code, Cursor, Manus, Deep Research) and then builds a working one.

The four pillars:

1. **A detailed system prompt** — a real job description, not a one-liner.
2. **A planning / to-do tool** — write the plan down and keep re-reading it.
3. **A file system** — offload work to "disk" instead of stuffing the context window.
4. **Sub-agents** — hire specialists and delegate.

## Learning path

| Step | Where | What |
|------|-------|------|
| 1. Theory | [`explainer.md`](./explainer.md) · [`deep_agents_overview.ipynb`](./deep_agents_overview.ipynb) | Why the four pillars work, with references and diagrams |
| 2. The build | [`competitive_analysis_agent/`](./competitive_analysis_agent) | A runnable deep agent that compares two companies |
| 3. The UI | [`setup-ui.sh`](./setup-ui.sh) | Spawn the visual [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) and watch the agent work live |

## Quickstart

```bash
cd competitive_analysis_agent
uv sync
cp ../.env.example ../.env      # then add your OpenRouter + Tavily keys
uv run langgraph dev
```

Full setup, environment variables, and how to interact with it (Studio or
deep-agents-ui) are in
[`competitive_analysis_agent/README.md`](./competitive_analysis_agent/README.md).

## Watch it work live (deep-agents-ui)

[deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) is LangChain's
visual front-end for deep agents: a chat window plus live panels showing the
agent's to-do list, the files it writes, and each sub-agent it spawns. It's the
best way to *see* the four pillars in motion.

It's a separate ~800 MB Node app, so we don't vendor it — `setup-ui.sh` clones,
configures, and launches it for you:

```bash
# Terminal 1 — the agent backend
cd competitive_analysis_agent && uv run langgraph dev

# Terminal 2 — the UI (clones + installs on first run, then starts it)
./setup-ui.sh
```

Then open <http://localhost:3000> and, in the UI's settings dialog, enter:

| Field | Value |
|-------|-------|
| Deployment URL | `http://127.0.0.1:2024` |
| Assistant ID | `competitive_analysis_agent` |
| LangSmith API Key | *optional* (auto-filled from your `.env` if set) |

These are saved in your browser, so you only enter them once. Requires **git** and
**Node 20+**. Use `./setup-ui.sh --setup-only` to install without starting.

## Credits

The example and theory are adapted from
[ALucek/deep-agents-walkthrough](https://github.com/ALucek/deep-agents-walkthrough),
built on LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents).
The agent code here has been updated for the current `deepagents` / LangChain 1.x
APIs and routes its model through OpenRouter.
