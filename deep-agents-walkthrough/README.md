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
| 3. Read-aloud guide | `../explainers/4-deep-agents.md` | A spoken walk-through of the code for demos |

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

## Credits

The example and theory are adapted from
[ALucek/deep-agents-walkthrough](https://github.com/ALucek/deep-agents-walkthrough),
built on LangChain's [`deepagents`](https://github.com/langchain-ai/deepagents).
The agent code here has been updated for the current `deepagents` / LangChain 1.x
APIs and routes its model through OpenRouter.
