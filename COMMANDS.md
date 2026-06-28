# Run everything from scratch

A top-to-bottom walkthrough to prove a **fresh clone works**. Run it yourself the
night before the session so nothing surprises you in the room.

> Need Python 3.11+, git, or Docker first? See the **Prerequisites** section in
> the [README](README.md) — it has the macOS and Windows install commands.

---

## Read this once — how the terminal works

This is the thing that trips everyone up, so let's make it boring and clear.

- **You always work from `studio/`, with the virtual environment active.** When the
  venv is on, your prompt shows `(.venv)` at the front. If you don't see it, the
  commands won't find your packages.
- **Most commands run, print something, and hand the prompt back to you.**
  `python agent.py`, `python evaluate.py`, the `docker build`, etc. — they finish
  and you're back at `(.venv) … studio %`.
- **One command is different: `uvicorn …` starts a web server.** A server's whole
  job is to *keep running and wait for requests*, so it **takes over that terminal
  and never returns to the prompt**. That's not stuck — that's working. You'll see
  it log every request. The same is true of `docker run`.

So whenever something "takes over" the terminal, you have two choices:

| | What you do | When to use it |
|---|-------------|----------------|
| **Stop it** | Press **`Ctrl-C`** in that terminal to kill the server and get your prompt back | You're done with the deploy demo and want to run the next thing |
| **Leave it, open another** | Open a **second terminal** for the next commands (re-activate the venv there — see below) | You want the server to keep answering while you do other things |

**The key fact that makes this simple:** only the **deploy** step (the `curl`
demo) needs the server running. `trace_demo.py`, `evaluate.py`, and
`langfuse_experiment.py` **do not use the server at all** — they import the agent
and run it directly, in-process. So the easy path is: do the deploy demo, press
`Ctrl-C` to stop the server, then run everything else in the same terminal.

### Every new terminal starts the same way

Whenever you open a fresh terminal (or a second one), run these two lines first:

```bash
cd ~/Desktop/Projects/langgraph-advanced/studio
source .venv/bin/activate
#   prompt should now show (.venv) and you're inside studio/
#   Windows (PowerShell):  cd ...\langgraph-advanced\studio ; .\.venv\Scripts\Activate.ps1
```

---

## Part 0 · One-time setup

```bash
# Clone and enter the kit (everything runs from studio/)
git clone https://github.com/takshit12/langgraph-advanced.git
cd langgraph-advanced/studio
```

```bash
# Virtual environment + dependencies — MUST be Python 3.11+
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
# Keys — only needed later, for the two Langfuse steps. You can do this now or
# right before Part 4. Create the file even if you'll add keys later (Docker reads it).
cp .env.example .env
#   Windows:  copy .env.example .env
#   → open .env and paste your pk-lf-… / sk-lf-… keys + the matching LANGFUSE_HOST
```

---

## Part 1 · The agent by itself  ·  _no server, no keys_

```bash
python agent.py
```
**Expect:** 3 lines, each like `<message> -> [intent=… | sentiment=…] …`. This
proves the agent works before we wrap or measure it. The prompt comes back when
it's done. ✅ (You've already seen this work.)

---

## Part 2 · DEPLOY — run it as a web service  ·  _this starts a server_

**Terminal 1 — start the server (it will take over this terminal):**

```bash
uvicorn app:app --reload --port 8000
```
**Expect:** `Uvicorn running on http://127.0.0.1:8000` and then it just sits there
logging. **This is correct — leave it running.** Do NOT type the next commands
here; this terminal belongs to the server now.

**Terminal 2 — open a new terminal, re-activate the venv, then call the server:**

```bash
cd ~/Desktop/Projects/langgraph-advanced/studio && source .venv/bin/activate

curl -s localhost:8000/health
#   EXPECT: {"status":"ok"}

curl -s -X POST localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"message":"My app is broken and I want a refund"}'
#   EXPECT: intent "complaint", sentiment "negative"
```

`curl` just talks to `http://localhost:8000`, so it works from **any** folder —
it doesn't care where you are. (The *server* had to be started from `studio/`; the
*curl* doesn't.) On Windows, run the multi-line curl in **Git Bash**, or skip curl
entirely and open **<http://127.0.0.1:8000/docs>** → "Try it out".

**When you're done:** go back to Terminal 1 and press **`Ctrl-C`** to stop the
server. Now Terminal 1 is free again for the rest of the steps.

---

## Part 3 · DOCKER — the same service in a container  ·  _optional_

This is what failed for you, and it was two separate things. Fix both:

**1. Docker Desktop must be running.** The error
`failed to connect to the docker API … is the daemon running?` means it isn't.
Open the **Docker Desktop app** (Spotlight → "Docker") and wait for the whale icon
in your menu bar to go steady. Then confirm from a terminal:

```bash
docker info        # should print server info, NOT an error
#   (or: docker ps  → an empty table is fine; an error means Desktop isn't up yet)
```

**2. Build from `studio/`, not the repo root.** The `Dockerfile` lives in
`studio/`. Your earlier `docker build .` ran from `…/langgraph-advanced` (one level
up), where there's no Dockerfile. So:

```bash
cd ~/Desktop/Projects/langgraph-advanced/studio    # ← must be here (the Dockerfile is here)
docker build -t langgraph-agent .                  # the "." means "use the Dockerfile in this folder"
```
**Expect:** build steps, ending in `naming to docker.io/library/langgraph-agent`.

```bash
# Run it. Like uvicorn, this TAKES OVER the terminal. Stop uvicorn first if it's
# still running (both want port 8000). --env-file needs the .env from Part 0 to exist.
docker run -p 8000:8000 --env-file .env langgraph-agent
```
Then test it exactly like Part 2 — from a **second terminal**, the same `curl`
commands (no venv needed for curl). **`Ctrl-C`** in the docker terminal to stop it.

> Docker is a "nice to have / show it once" step. If it fights you in the room,
> skip it — the `uvicorn` run in Part 2 already made the point. Don't let a Docker
> install swallow your clock.

---

## Part 4 · Where LANGFUSE comes in  ·  _observe the agent_

Up to now, nothing has touched Langfuse. Here's where it enters and what it's for.

**What it is:** a free website that collects "traces" — recordings of what your
agent did on each request (every step, inputs, outputs, timing). You run the agent
on your laptop as usual; a little recorder ships those recordings up to Langfuse's
cloud; then you open the **Langfuse website in your browser** to look at them.

**One-time, in your browser:**
1. Sign up at **cloud.langfuse.com** (EU) or **us.cloud.langfuse.com** (US). The
   region you pick **is** your `LANGFUSE_HOST`.
2. Create a project → **Settings → API Keys** → create a `pk-lf-…` / `sk-lf-…` pair.
3. Paste both keys + the matching `LANGFUSE_HOST` into `studio/.env` (Part 0).

**Then, in your terminal (no server needed — this runs the agent directly):**

```bash
python trace_demo.py
```
**Expect:** 3 result lines + `✅ Done`. This sends 3 traces up to Langfuse.

**Then back in your browser:** open your Langfuse project → **Tracing**. You'll see
your 3 traces. Click one → expand the tree (`classify → … → finalize`) → click a
step to read its input/output and latency. *That's* the payoff — looking inside
the agent's head.

> No keys yet? `trace_demo.py` will stop with a friendly "missing keys" message.
> The next two steps (Evaluate/Improve) need **no** keys, so you can do those first.

---

## Part 5 · EVALUATE — grade the buggy agent  ·  _no server, no keys_

```bash
python evaluate.py
```
**Expect:** `intent 6/14 (42.9%)`, `sentiment 11/14 (78.6%)`, 8 failures. Read the
**FAILURES** section — that list is the whole point. (This runs the agent directly;
Langfuse is not involved at all.)

---

## Part 6 · IMPROVE — grade the fixed agent  ·  _no server, no keys_

```bash
python evaluate.py --agent agent_improved
```
**Expect:** `intent 13/14 (92.9%)`, `sentiment 14/14 (100.0%)`, 1 failure (`g11`).
The jump from 43% → 93% is the moment the session is built around.

---

## Part 7 · Experiments — record the scores in Langfuse  ·  _needs keys_

```bash
python langfuse_experiment.py --agent agent
python langfuse_experiment.py --agent agent_improved
```
**Expect:** two runs in Langfuse you can open **side by side** (43% vs 93%). Same
agent-run-directly pattern as Part 4 — no server — it just records the scores to
the Langfuse cloud so you can compare versions over time.

---

## Cheat sheet — which step needs what

| Step | Run from | Server running? | Docker Desktop? | Langfuse keys? |
|------|----------|:---:|:---:|:---:|
| `python agent.py` | `studio/`, venv on | no | no | no |
| `uvicorn …` (deploy) | `studio/`, venv on | *it is the server* | no | no |
| `curl …` | any folder, **2nd terminal** | **yes** | no | no |
| `docker build` / `docker run` | `studio/`, venv on | no | **yes** | run needs `.env` to exist |
| `python trace_demo.py` | `studio/`, venv on | no | no | **yes** |
| `python evaluate.py` | `studio/`, venv on | no | no | no |
| `python langfuse_experiment.py` | `studio/`, venv on | no | no | **yes** |

**The one-paragraph answer to your questions:** run the Python scripts and
`docker build` from **`studio/`** with the venv active. The only thing that needs
the server *running* is the `curl` demo — for that, leave `uvicorn` going in one
terminal and curl from a second. For everything else (trace_demo, evaluate,
experiment), you don't need the server, so just `Ctrl-C` it first and reuse the
same terminal. Langfuse only matters for `trace_demo.py` and
`langfuse_experiment.py` — those send data to the Langfuse website, which you then
open in your browser to explore.

---

## Quick health check

If **Part 1, 5, and 6** print the numbers above, the kit is healthy — those need
**no keys and no server** and exercise the whole agent + evaluation path. Part 4
and 7 additionally confirm your Langfuse connection (keys + correct region host).
