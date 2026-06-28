# Run everything from scratch

A single top-to-bottom command list to prove a **fresh clone works**. Run it
yourself the night before the session so nothing surprises you in the room.

> Need Python 3.11+, git, or Docker first? See the **Prerequisites** section in
> the [README](README.md) — it has the macOS and Windows install commands.

Each block says what to **expect** so you can tell instantly if a step is healthy.

---

```bash
# 1 · Clone and enter the kit (everything runs from studio/)
git clone https://github.com/takshit12/langgraph-advanced.git
cd langgraph-advanced/studio
```

```bash
# 2 · Virtual environment + dependencies — MUST be Python 3.11+
python3 --version                 # if this is < 3.11, use python3.11 (or python3.12) below
python3.11 -m venv .venv && source .venv/bin/activate
#   Windows (PowerShell):  py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1
python --version                  # confirm the venv is 3.11+
python -m pip install --upgrade pip
pip install -r requirements.txt
#   Why 3.11? langgraph 1.x and langfuse only ship for 3.11+. On the macOS system
#   python3 (often 3.9) pip can't find langgraph 1.0 and the install fails.
```

```bash
# 3 · Keys (only needed for the Langfuse steps, 6 and 9)
cp .env.example .env
#   Windows:  copy .env.example .env
#   → open .env and paste your pk-lf-… / sk-lf-… keys + the matching LANGFUSE_HOST
```

```bash
# 4 · Smoke-test the agent itself — no server, no keys needed
python agent.py
#   EXPECT: 3 lines, each like  "<message> -> [intent=… | sentiment=…] …"
```

```bash
# 5 · DEPLOY — run the API and ring its doorbells
uvicorn app:app --reload --port 8000
#   Leave this running. Open a SECOND terminal, then:  cd …/studio && source .venv/bin/activate

curl -s localhost:8000/health
#   EXPECT: {"status":"ok"}

curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"My app is broken and I want a refund"}'
#   EXPECT: intent "complaint", sentiment "negative"

#   (multi-line curl is bash; on Windows use Git Bash, or just open
#    http://127.0.0.1:8000/docs → "Try it out". Ctrl-C the server when done.)
```

```bash
# 5b · (optional) the same service, in a container
docker build -t langgraph-agent .
docker run -p 8000:8000 --env-file .env langgraph-agent
```

```bash
# 6 · OBSERVE — push traces to Langfuse (needs keys from step 3)
python trace_demo.py
#   EXPECT: 3 result lines + "✅ Done", then traces appear in Langfuse → Tracing
```

```bash
# 7 · EVALUATE — grade the buggy agent
python evaluate.py
#   EXPECT: intent 6/14 (42.9%), sentiment 11/14 (78.6%), 8 failures
```

```bash
# 8 · IMPROVE — grade the fixed agent and watch the jump
python evaluate.py --agent agent_improved
#   EXPECT: intent 13/14 (92.9%), sentiment 14/14 (100.0%), 1 failure (g11)
```

```bash
# 9 · (optional) push both runs to Langfuse to compare side by side
python langfuse_experiment.py --agent agent
python langfuse_experiment.py --agent agent_improved
#   EXPECT: two runs in Langfuse, 43% vs 93%, comparable over time
```

---

## Quick health check

If **steps 4, 7, and 8** print the numbers above, the kit is healthy — those need
**no keys** and exercise the whole agent + evaluation path. Steps **6 and 9**
additionally confirm your Langfuse connection (keys + correct region host).
