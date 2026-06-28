# 2 · Ship it and watch it (read aloud)

> Spoken-style walk-through. Open the files as you go and point at them.

---

## Part A — Shipping it (`app.py`, `Dockerfile`)

Remember that button I told you to hold onto? The finished agent is just an object
with a button called `.invoke()` — press it with a message, get an answer back.

So here's the big secret of "deploying an AI agent," and it's almost
disappointingly simple: **deploying it just means putting a doorbell on that
button that the internet can ring.** There's no special AI hosting, no magic
platform you have to pay for. If you can put any function online, you can put this
online.

Let's open **`app.py`**. The very first thing it does — point at this line — is
`from agent import graph`. That's important: **we did not change the agent at
all.** We're importing the exact same thing from last session and just wrapping a
web server around it. Shipping is a *wrapper*, not a rewrite.

Now look at the three "doors" this file opens. In web terms these are called
endpoints, but think of them as three doorbells:

- **`/health`** — ring this and it just says "yep, I'm alive." That's the first
  thing any hosting system checks to make sure your app is up. It's the heartbeat.

- **`/chat`** — this is the real one. You ring it with a message, it presses the
  agent's button once, and hands back the answer — the type of message, the mood,
  and the reply.

- **`/chat/stream`** — same thing, but it shows its work. Instead of waiting for
  the final answer, it sends each step out the moment it finishes — classify, then
  the chosen lane, then finalize. This is literally the same "boxes lighting up
  one by one" you saw in Studio, except now it's streaming over the internet so a
  real app could show a typing indicator or live progress.

We'll start it on our own laptop with one line — `uvicorn app:app` — and then ring
the doorbells with little `curl` commands. When the answer comes back as plain
data, that's the moment to say:

> *"That's our agent, as a service. A website or a phone app could call this right
> now and never even know LangGraph exists behind it."*

**Then the lunchbox.** Open the **`Dockerfile`**. A "container" is just a lunchbox:
it packs the app together with everything it needs to run, so it works the exact
same way on your laptop, on a server, or in the cloud — no "but it worked on my
machine." Notice we ship a *lean* lunchbox on purpose (`requirements-api.txt`) — it
only packs what's needed to answer messages, not all our building-and-testing
tools. A production thing should carry the bare minimum.

The point to land: *"This now runs anywhere. Your laptop, a five-dollar server,
big company cloud — it doesn't care. And nothing in here is locked to any one
vendor."*

---

## Part B — Watching it (`trace_demo.py` + Langfuse)

Okay. Our agent is live and answering people. But right now it's a **black box**:
a message goes in, an answer comes out, and we have no idea what happened in
between. When it gets something wrong — and we're about to find out it gets lots
of things wrong — we want to look *inside its head* and see how it decided.

That recording of what happened inside is called a **trace**. Think of it like a
**flight recorder** (a black-box recorder) on a plane: every step the agent took,
in order, with what went in and what came out, and how long each step took.

We'll use a free tool called **Langfuse** to collect those recordings. Open
**`trace_demo.py`** and here's the lovely part — point at it:

> *"We are not going to change the agent to do this. Not one line. We just clip a
> little recorder onto it."*

That's genuinely it. There's one extra line where we hand the agent a "recorder"
(it's called a callback handler) when we press its button. The agent runs exactly
as before; the recorder quietly writes down every step and ships it to Langfuse.
Observability — watching your thing in the wild — is something you *clip on*, not
something you have to build into the agent.

Then we'll **switch to the Langfuse website** and open the recording. You'll see
the same shape from Studio — classify, then the lane it picked, then finalize —
but now it's real, live data. We can click any step and read exactly what the
agent saw and what it decided. *That's* how you debug something once it's out in
the world.

**One honest thing I'll show you, not hide:** the "question" lane is the one spot
where our agent calls out to a real outside AI. Our recorder catches that the step
*happened*, but it doesn't automatically capture what the outside AI said inside
it — because that call goes around the part Langfuse hooks into. I'm leaving it
that way on purpose so you can *see the seam*: the recorder tracks the agent's own
steps; recording an outside AI's call is a second little hook you add separately.
It's a one-line change, and naming it honestly is more useful than pretending
everything's automatic.

Next: now that we can watch it, let's actually *grade* it — and find the bugs.
→ [3 · Measure it and fix it](3-measure-it-and-fix-it.md)
