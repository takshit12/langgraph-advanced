# 3 · Measure it and fix it (read aloud)

> This is the heart of the session. Spoken-style. Slow down here.

---

## Part A — Measuring it (`golden_dataset.jsonl`, `evaluate.py`)

Here's the question nobody likes to answer honestly: **how do you know if your
agent is actually any good?** Most people answer with vibes — "yeah, it seems
fine." We're going to do better than vibes.

The trick is simple and it's the same trick a teacher uses: **make an answer
key.** Open **`golden_dataset.jsonl`**. This is just 14 example messages, and for
each one, *we* — the humans who know the right answer — have written down what the
agent *should* say. What kind of message it is, and the mood. That's our answer
key. People call it a "golden dataset," but it's just a list of questions with the
correct answers filled in.

Read a couple out loud and let people feel the trap being set:

- "What is this, exactly?" → that's a **question**, obviously.
- "Can you ship my order faster?" → also a **question**.

> *"Keep an eye on those two. Nothing about them looks like a 'hello' to you or me.
> Let's see what our word-spotting agent thinks."*

Now open **`evaluate.py`**. This is just an automatic grader. It does three
boring, beautiful things: it takes each of the 14 messages, runs it through the
agent, and checks the agent's answer against our answer key — right or wrong, no
half-marks. No AI judging here, no fancy framework. It's a plain checker that asks
"did it match? yes or no." That's what most real evaluation actually is.

Run it. The score comes back:

> **Right about the message type: 6 out of 14. That's 43%.**

Let that land. *"This agent is wrong more often than it's right."* And then — this
is the important bit — scroll down to the **list of failures**. The grader just
handed us every single message it got wrong, with the right answer and the agent's
wrong answer sitting side by side. **That list is the most valuable thing on the
screen.** It's not a vague score; it's a to-do list.

Hand-on for the room: read the failures, and don't fix anything yet. Just write
down, in your own words, *why* you think each one went wrong.

---

## Part B — Fixing it (`agent_improved.py`)

Now the magic move, and it's the whole skill: **eight failures look like eight
problems, but they're not.** Group them by *why* they happened, and they collapse
into just **three real bugs** — plus one we'll leave alone on purpose.

**Bug 1 — it's matching letters hidden inside other words.** This is the big one.
"What is **thi**s?" got called a greeting. Why? Because the letters "h-i" are
sitting right inside the word "t-**hi**-s." The agent was looking for "hi" and
found it hiding inside "this," "ship," "which." Four of our eight failures are this
one silly thing.

**Bug 2 — it checks things in the wrong order.** "Hi, my app is broken" got filed
as a friendly hello. But that person is clearly upset! The problem: the agent
checks "is this a greeting?" *before* it checks "is this a complaint?", and it
stops at the first match. The word "Hi" came first, so it never even looked
further. When a message is two things at once, the order you check decides the
answer.

**Bug 3 — it just doesn't know enough words.** "I'm absolutely furious," "the
worst experience ever" — these are obviously angry complaints, but the words
"furious" and "worst" weren't on our little hand-written list, so the agent
shrugged and called them questions. Real upset customers don't limit themselves to
the words you happened to think of.

Now open **`agent_improved.py`** and show that it's the **same agent** — same
shape, same steps — with three small, surgical fixes that each kill one bug:

- We make it match **whole words only**, so "hi" matches the *word* "hi" and never
  hides inside "this." (Kills bug 1 — all four of them.)
- We make it check **complaints before greetings**, so an upset "Hi, my app is
  broken" is treated as the complaint it is. (Kills bug 2.)
- We **teach it more words** — furious, worst, unusable, and so on. (Kills bug 3.)

Run the grader again on the fixed version:

> **From 43% up to 93% on the message type. And the mood score from 79% to a
> perfect 100%.**

The line to deliver slowly:

> *"Forty-three to ninety-three. And we did not guess once. Every single fix came
> straight off that list of failures the agent handed us. That's the whole job."*

---

## The one we left broken (the most important slide)

There's still one failure, and we left it broken **on purpose**: *"I do not hate
it, it works fine now."* The agent sees the word "hate" and flags a complaint —
but read it: that person is *happy*. The word "hate" is there, but the meaning is
the opposite.

And you cannot fix that by looking at words. No word-list in the world
understands that "do **not** hate" is the opposite of "hate." This is the exact
wall where word-spotting ends and you finally, genuinely need a real AI brain that
understands *meaning*.

> *"This is the moment you reach for a smarter model — not because it's trendy, but
> because you hit a wall that word-matching truly cannot climb. And here's the
> beautiful part: when you build that smarter version, you test it against these
> very same 14 questions to prove it actually helped. The answer key never
> changes. Only the agent does."*

Last file — **`langfuse_experiment.py`** — is just our same grader, but instead of
printing the score to the screen and forgetting it, it saves the scores into
Langfuse. So next week's smarter version becomes a *third bar* you compare against
today's 43% and 93%. That's how the loop becomes permanent: ship, watch, measure,
fix, measure again — forever.
