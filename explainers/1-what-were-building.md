# 1 · What we're building (a walk-through you can read aloud)

> This is written to be **spoken**. Read it like you're talking to the room,
> pausing to point at the file on screen. Plain English, no jargon dumps.

---

## The story so far

Last time, we built a small AI agent and watched it run inside **LangGraph
Studio** — that visual tool where you see little boxes light up one after another
as the agent thinks. That was perfect for *building*. But Studio is like a
workshop. You don't hand a customer your workshop. So today we take that **exact
same agent** and do four things to it that turn a toy into something real:

1. **Ship it** — put it online so anything can talk to it.
2. **Watch it** — see what it's actually doing, live, when real people use it.
3. **Measure it** — score it honestly against a list of known-right answers.
4. **Fix it** — read where it went wrong, find the real reason, and improve it.

And here's the hook I want you to hang onto: **this agent is wrong about 4 times
out of 10 right now.** By the end of the hour, we'll have found out *exactly* why,
fixed it, and watched it jump to being right 9 times out of 10 — and I won't guess
even once. The agent itself will tell us what's broken.

---

## What the agent actually is

Let's open **`agent.py`** and I'll explain it like a person, not like code.

Picture a **front-desk receptionist**. A message comes in. The receptionist reads
it and decides: *is this a hello, a goodbye, a complaint, or a question?* Then they
hand it to the right person and a reply goes back out. That's the whole agent.

In the code, that flow looks like this:

```
START → classify → (pick a lane) → { greeting | farewell | complaint | question } → finalize → END
```

Four ideas, and that's genuinely all there is:

- **The message travels on a little form.** As it moves through the agent, each
  step fills in another box on the form — what kind of message it is, the mood,
  the reply. In the code that "form" is called the **state**. Point at
  `ChatState` near the top: it's just a list of blanks — message, intent,
  sentiment, response, final.

- **Each step is one tiny job.** These are the **nodes** — `classify_node`,
  `greeting_node`, `complaint_node`, and so on. Each one is a small function that
  takes the form, does one thing, and writes its answer back on the form. The
  `classify_node` is the receptionist reading the message and tagging it. The
  `finalize_node` at the end just staples everything together into one tidy reply.

- **There's a signpost in the middle.** After the message is tagged, something has
  to decide which lane it goes down. That's the **router** — `route_by_intent`. It
  reads the tag and sends the message to greeting, farewell, complaint, or
  question. One in, one of four out.

- **At the very bottom we press "compile".** `graph = workflow.compile()` takes all
  those steps and wires them into one finished thing we can run. From here on,
  that finished `graph` is just an object with a button on it called `.invoke()` —
  you press it with a message, you get an answer. **Remember that button. It's the
  secret to the whole next part.**

---

## The one detail that's going to matter a LOT

Here's the part to slow down on. **How does the receptionist actually decide what
kind of message it is?** Look at the keyword lists near the top of the file.

It just looks for specific words. If the message contains the letters "hi", call
it a greeting. If it contains "broken" or "refund", call it a complaint. That's
it — it's matching words from a little hand-written list.

That sounds reasonable. It is also going to be *gloriously* wrong, in ways that
are funny and very human, and we are going to catch every one of them with the
measuring step later. So plant this flag now and say it out loud:

> *"Hold on to one fact: the agent decides everything just by spotting words from a
> list. That tiny shortcut is the reason this thing is wrong 4 times out of 10 —
> and in about forty minutes we're going to prove it."*

That's the agent. Next: we put a doorbell on it so the world can ring it.
→ [2 · Ship it and watch it](2-ship-it-and-watch-it.md)
