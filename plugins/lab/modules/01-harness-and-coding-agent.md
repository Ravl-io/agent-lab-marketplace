# Module 1 — Harness and coding agent

**Two hours.** They end with a working plugin, v0.1, running on their track's data.

## What this module is for

By the end they should be able to answer, out loud, to a colleague: *what is an agent, what
is the harness made of, and which primitive do I reach for?*

## The arc

| Step | Time | What they do | Checkpoint |
|---|---|---|---|
| **0** | 5m | Setup: settings, a tracer hook, one experiment. No data yet | `M1.C0-setup` |
| **1** | 10m | **What is an agent** — `--tools ""` then `"Read"` then `"Read,Write"`. Count the round trips | `M1.C1-agent` |
| **2** | 10m | **The core tools, and their limit** — every tool, no procedure. It works, and differently every time | |
| **2b** | 8m | **Intent** — the kickoff artifact, and the thing everything else is measured against | `M1.C2-intent` |
| **3** | 20m | **Skills** — write one, watch the agent choose it, then break its description | `M1.C3-skill` |
| **4** | 15m | **A tool** — deterministic, tested, structured output, wired into the skill | `M1.C4-tool` |
| **5** | 15m | **A hook** — a write boundary the model cannot argue with | `M1.C5-hook` |
| **6** | 20m | **The plugin** — package it, validate it, install it, watch it run | `M1.C6-plugin` |
| **7** | 9m | **Debrief** — choosing a primitive, the anti-patterns, what carries forward | module complete |

**Authoring status:** the whole module is authored. Modules 2 to 4 are not. Do not improvise them as though they were — if a participant finishes
Step 1 before the rest exists, say so plainly and hand back to the facilitator.

**Every track runs this module.** Anything track-specific — the task, the file names, the
skill name, the output format — comes from `${CLAUDE_PLUGIN_ROOT}/tracks/<track>/track.json`.
Read it at the start and use those values:

| Field | Use it for |
|---|---|
| `first_task` | the terse real-world task in Step 2 (already substituted into `experiments/task.prompt`) |
| `first_input` | the one file experiment 2 reads |
| `first_skill` | the skill directory name in Step 3 |
| `key_files.output_format` | the format their output must match |
| `key_files.policy` | the rules their constraints should reflect |

Illustrations below use the `support-triage` track and are marked as such. **Never read a
lead-track example out to a group on a different track** — it is the fastest way to lose them.

**Setup is incremental, on purpose.** Nobody receives a finished environment. Each stage adds
only what the next experiment needs, and the difference between two stages is small enough to
read. When a participant asks why they do not have the rest of the data yet, that is the
answer.

---

## Step 0 — Setup (5 minutes)

Frame it in one sentence and do it. This is plumbing; plumbing does not get a lecture.

### 0.1 Check the ground

The workspace **is** the folder they are already in. Do not create a subfolder, and do not
offer to. Project configuration is read from the project root.

Confirm from the state that `env.ready` is true and a track is set. If not, send them to
`/lab:doctor` or `/lab:start`.

### 0.2 Apply the first stage

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s1-harness
```

Five files, and nothing else:

| File | What it is |
|---|---|
| `.claude/settings.json` | Project configuration: four hooks, and which tools may run without asking |
| `.claude/hooks/trace.py` | The tracer. Their file, in their repo — they will read it in a minute |
| `experiments/exp.py` | Runs one experiment. Prints the command before it runs it |
| `experiments/exp1.prompt` | The first experiment's prompt, as plain text they can edit |
| `experiments/README.md` | What the three experiments are |

No data yet. That is deliberate, and Step 1 explains itself.

**If they see a warning about an untrusted workspace**, they need to accept the trust
dialog once — open Claude Code interactively in the folder and accept it. Until then the
`permissions` block in `settings.json` is ignored and every tool call stops to ask.

### 0.3 Record it

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" begin-module 01
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C0-setup
```

---

## Step 1 — What is an agent? (10 minutes)

**The question this answers:** everyone says "AI agent". What is actually happening?

Three runs of the same thing, differing in one flag. The participant runs each one and reads
the same trace file afterwards. **Do not explain the conclusion up front** — the numbers in
the trace make the point better than you can.

### 1.1 The frame, in three sentences

Say roughly this, then stop talking:

> A language model does one thing: you send it text, it sends text back. It cannot open a
> file, run a command, or remember the last thing you asked. Everything else — the file it
> read, the command it ran, the fact that it is still working on your problem — is the
> harness around it. We are about to watch that happen.

Then point at `.claude/hooks/trace.py`: it is attached to four moments — the prompt going
out, the model asking for a tool, the result coming back, the final answer — and it writes
each to `.claude/lab-trace.log`. Hook output is not shown in the session, which is why it
goes to a file they open.

### 1.2 Experiment one — no tools at all

```
python3 experiments/exp.py 1
```

It prints the command first, and the command is the lesson:

```
$ claude --tools "" --strict-mcp-config --append-system-prompt "...you have no tools..." \
    -p "$(cat experiments/exp1.prompt)"
```

`--tools ""` gives the model **no tools whatsoever**. Say that this is a separate Claude Code
session, started just for the experiment, and why: if we switched tools off for *this*
session, we would switch them off for the tutor too, and I would stop being able to help.
Configuration has a blast radius, and choosing where it applies is part of the job.

Then: **open `.claude/lab-trace.log`.** Ask, do not tell:

- The model answered the general question well — it knows the domain in general.
- It said it could not know the specific thing at their organisation, and did not guess.
- **`1 call to the model, 0 tool requests`.** One request, one response. That is all that
  happened.

Name the point: *the model knows a great deal in general and nothing whatsoever about your
organisation.* That gap is why the next three modules exist.

They can also run the command themselves, or edit `experiments/exp1.prompt` and re-run. Say
so — the prompt is a text file, not magic.

### 1.3 Experiment two — give it one tool

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s2-data
python3 experiments/exp.py 2
```

The stage adds one data file — their track's `first_input` — and two more prompts. Nothing
about the configuration changed: the difference is on the command line.

```
$ claude --tools "Read" --strict-mcp-config -p "$(cat experiments/exp2.prompt)"
```

Open the trace. It now reads:

```
--> SENT TO THE MODEL        your prompt
<-- BACK FROM THE MODEL      it wants a tool: Read(file_path=...)
--> HANDED TO THE HARNESS    (the model is paused, waiting)
<-- RESULT SENT BACK         1,247 chars of the file
<-- FINAL ANSWER             what the file is about
This experiment: 2 call(s) to the model, 1 tool request(s).
```

Draw out three things, in order:

1. **The model did not read the file.** It asked. Read the line again — it came *back* from
   the model as a request. The harness did the reading.
2. **The result was sent back in, and the model ran again.** Two calls, not one. The second
   call contained everything the first did *plus* the file contents.
3. It answered from the file, and said what the file did not contain.

Now name it:

> An agent is not a model. An agent is the **loop**: send everything you have to the model,
> get back either an answer or a request for a tool, run the tool, add the result to
> everything you have, send it again. Until the model stops asking.

Two consequences worth stating while the trace is on screen:

- **Each tool use costs another round trip.** That is why agents are slower than a chat, and
  why a task needing eight tool calls takes roughly eight times as long as one needing one.
- **Everything accumulates.** The conversation grows with every result. Context is a budget,
  and retrieval — Module 2 — is mostly about spending it well.

### 1.4 Experiment three — let it act

```
python3 experiments/exp.py 3
```

```
$ claude --tools "Read,Write" --strict-mcp-config -p "$(cat experiments/exp3.prompt)"
```

The trace shows **3 calls, 2 tool requests**, and `notes/first-summary.md` now exists on disk
where a minute ago it did not.

The thing to name: nothing about the model changed across the three experiments. Same model,
same shape of prompt. What changed was **what the harness would let it do** — one flag,
three words. Reading is a different kind of act from writing, and the distance between an
assistant and something that changes your systems is that short.

That is the setup for Module 4's approval gate, and it is worth saying now: the interesting
engineering is not in making the agent capable. It is in deciding what it may do.

### 1.5 Allowlists, in 60 seconds

Worth making time for. `--tools "Read"` is an **allowlist**: it names what exists, and
everything else is simply absent.

We tried building this lab the other way — a deny list in `settings.json` naming `Read`,
`Write`, `Bash`, `Glob`, `Grep` and the rest. The model still had a dozen tools left, because
you can only deny what you can name, and new tools arrive with new versions. A deny list is
incomplete by construction. If a participant takes one security lesson out of today, that is
the one.

### 1.6 Check understanding, then gate

One question, and wait for a real answer:

> **"The model wrote a file in experiment three. Who actually wrote it, and how many times
> did we call the model to get it done?"**

The answer you want: the *harness* wrote it, after the model asked; three calls. If they say
"the model wrote it", go back to the trace and read the Write line together. That
misconception is worth a minute, because everything in Module 4 depends on knowing where
that boundary sits.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C1-agent
```

### 1.7 Hand over

Two lines. They have seen what an agent is; next they do their track's real job with nothing
but a prompt, and find out what a prompt alone does and does not give them.

### Questions you may get early

- *"Can I see the actual API request?"* — Not from a hook; hooks see the tool boundary, not
  the HTTP traffic. `.claude/lab-raw.jsonl` holds the exact payloads the harness sends the
  hook, which is the real contract and worth a look. For raw API traffic, `claude --debug api`.
- *"Why a separate session instead of a slash command?"* — Because the tool restriction has to
  apply to the experiment and not to the tutor. Answered in `experiments/README.md` too.
- *"Why did it use an absolute path when the prompt said a relative one?"* — Good catch. The
  harness resolves the path before the tool runs. Another thing the model is not doing itself.


---

## Step 2 — The core tools, and what they cannot give you (12 minutes)

**The question this answers:** if an agent is a loop over tools, what tools does it actually
need?

### 2.1 Name the five

They have now seen `Read` and `Write` work. Name the rest, against the trace they already
have rather than as a list on a slide:

| | |
|---|---|
| **Read** | open a file |
| **Write** | create or replace a file |
| **Execute** | run a command — `Bash`. The widest of the five by far, and the reason permissions matter |
| **Search files** | `Grep`, `Glob` — find things without reading everything |
| **Search the web** | `WebSearch`, `WebFetch`. Denied in this lab, deliberately: everything today is answerable from your own data |

Almost everything an agent appears to do decomposes into these. When Module 3 gives it a
knowledge graph, the graph is reached through one of them.

Then say the thing they have not noticed:

> Nobody asked for memory. Nothing in your prompt said "remember the file you read". But the
> second call to the model contained the file contents, and the third contained both the file
> and the summary. **The harness is accumulating context on your behalf** — that is the other
> half of what a harness does, and it is why the conversation gets more expensive as it goes.

### 2.2 Give it everything and ask for the real job

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s3-corpus
python3 experiments/exp.py 4
```

The stage brings in the rest of the corpus — the knowledge base, the database, the other
the worked example. The prompt is their track's `first_task` and nothing else — one line,
already substituted into `experiments/task.prompt`. For `support-triage` that is
`Triage CASE-4471.`; for `docgen`, `Write the Monthly Delivery Report for August 2026.`

```
$ claude --tools "Read,Write,Bash,Grep,Glob" --strict-mcp-config -p "$(cat experiments/triage.prompt)"
```

**Warn them it will take a minute or two**, and that the point is not the wait.

### 2.3 Do not set them up to expect failure

It will produce a **good** result. On `support-triage` it finds the unregistered domain and
rules out entitlement with a dated query; on the other tracks it does comparably well. It may
notice things you did not plan for. Say so before they run it, because the honest lesson is
more interesting than "the model is useless without help":

> A capable model with good data does this job well. That is not the problem we are solving.

What to look at instead, in this order:

1. **The count.** Around 18 tool requests. Now look at the first three or four — `find`, `ls`,
   `find data -type f`. It spent its opening turns working out where your data lives. Every
   one of those is a full round trip.
2. **The shape.** It invented its own structure. Possibly good structure — but its own.
   Compare it against their track's `key_files.output_format`, which is the format their
   team actually reviews. It does not match.
3. **The judgement.** Did it follow the rules in their track's `key_files.policy`? On
   `support-triage` that means using the four classifications as labels, and ruling out
   configuration *and* entitlement explicitly, each with evidence, before considering a
   defect. It may have done some of that by instinct. Instinct is not a policy.
4. **If there is time, run it again.** The second answer is also good, and a different shape.

### 2.3b The gap is not the same on every track — check before you claim one

Measured, with no skill and every core tool:

| Track | What is genuinely missing | What will probably **already be fine** |
|---|---|---|
| `support-triage` | Our four classification labels; ruling out configuration *and* entitlement each with evidence, in that order; the note's section order | The diagnosis itself — it usually finds the real cause |
| `docgen` | Where the output belongs; whether unsourced claims were flagged as gaps rather than quietly dropped; run-to-run consistency | **The format.** The template is in the corpus, so it follows it. Do not promise otherwise |
| `vendor-qa` | Severity assigned from the contract rather than from tone; every finding carrying both a criterion *and* a clause; coverage of requirements nobody verified | Spotting the obvious defects in the deliverable |

**Read the run in front of you before naming the gap.** If you tell a docgen group "look, it
ignored your format" and it plainly did not, you lose them for the rest of the module. The
reliable gaps on every track are the two you can always point at: **the wasted discovery
turns at the start**, and **the fact that nothing guarantees the next run looks like this
one**. Run it twice if the clock allows; that comparison never fails.

### 2.4 Name it

> Tools give an agent **capability**. They do not carry **procedure** — the order you work
> in, the checks that must happen before a conclusion, the evidence standard, the format your
> colleagues review. Capability without procedure gives you a good answer that is different
> every time, in a shape nobody can review, at a cost you did not choose.

That is the gap a skill fills. Not making bad work good — making good work **repeatable**.

---

## Step 2b — Intent (8 minutes)

**The question this answers:** I have just watched an agent do my job well and in the wrong
shape. What is the right shape?

This is the **kickoff artifact** from Anthropic's AI-native SDLC playbook. In real work it
comes *first* — before any building, in place of a backlog entry and a refinement meeting.
Say that out loud, and say why it is at Step 2 here instead: they needed to watch an agent
work before they could write constraints that an agent could actually apply. In Module 4 they
will write one first, in the proper order.

### 2b.1 Do not hand them a form

The scaffold arrived with the corpus at Step 2, at `intent.md`. It has the five headings and
a note telling them not to fill it in alone — and that instruction is the method, not
politeness.

**Interview them.** Ask about scope, users, constraints, and what success looks like. Draft
the file from their answers. Then have them correct it. The originator's words stay theirs;
the tutor is doing transcription and structure, which is the one kind of writing-for-them
that does not break the learning contract.

Done as an interview this takes six or seven minutes. Handed over as a form with five TODOs
it takes twenty and produces worse answers, because nobody writes their own constraints
unprompted.

### 2b.2 The five sections, and what each is really for

| Section | What it is for | Where it lands later |
|---|---|---|
| **Problem** | what is wrong today, in their words. Not the solution | the thing you check the result against |
| **Proposed outcome** | what is true once this exists, written so someone else could tell | Module 4's acceptance criteria |
| **Affected users and systems** | who touches it, what it reads and writes, and what it deliberately does *not* | scope, and the write boundary in Step 5 |
| **Constraints** | the rules it must work within | **their skill's constraints in Step 3, and their hook in Step 5** |
| **Open questions** | what they do not know yet | the list they bring to their team on Monday |

Two of those need pushing on, because both get skipped:

- **Constraints must be applyable, not aspirational.** "Be careful with customer data" cannot
  be applied by anything. "`data/` is read-only evidence" becomes a hook in twenty minutes.
- **Open questions must not be empty.** This is the one people leave blank, and it is the one
  that costs. An unwritten question gets silently answered by whoever implements it, usually
  wrongly and usually without noticing. Ask them directly: *"what did you have to guess at
  while answering the last four sections?"* That question produces the list.

### 2b.3 Make it drive something

The artifact on its own is governance — version-controlled next to the code it produced, so
the reasoning survives in git history. That is worth having and it is what the playbook is
for.

But in Claude Code you can make it **load**. `CLAUDE.md` supports imports, so a line reading

```
@intent.md
```

puts the intent in context on every turn. That is the difference between intent that shapes
the work and intent that sits in a file nobody opens.

They will write `CLAUDE.md` in Step 6; tell them now that the import is coming, and that it
is why `intent.md` has to stay short. **Every line of it is paid for on every single turn.**
Forty lines is a reasonable ceiling. This is also the honest trade-off to name: the governance
copy wants to be thorough, and the loaded copy wants to be brief. Brief wins, because an
intent nobody can afford to load is not driving anything.

### 2b.4 Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_intent.py"
```

It checks the five sections, the title and metadata, that Constraints carries at least two
concrete rules, and that Open questions is not empty.

- **Exit 0** — record the checkpoint.
- **Exit 1** — do not. Every problem it names is a sentence's work, and the empty-Open-questions
  failure is the one worth insisting on.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C2-intent
```

### 2b.5 Hand over

One line: they have written down what good looks like, and the next three steps are about
making an agent produce it. Their Constraints section is about to become a skill, and one line
of it is about to become a hook.

### If the clock has beaten you

Compress to three minutes by interviewing only **Constraints** and **Open questions**, and
leaving the other three sections as headings with a sentence each. Those two are the ones the
rest of the module consumes. Do not skip the step entirely: Step 3 without a Constraints
section becomes "write a skill about whatever you like", which is the weakest version of that
exercise.

---

## Step 3 — Skills (20 minutes)

**The question this answers:** how do I give the agent *our* procedure without pasting it
into every prompt?

### 3.1 What a skill is, in one idea

A skill is a folder with a `SKILL.md` in it. What makes it different from a document is
**when it gets loaded**:

| Level | What it is | When the model sees it |
|---|---|---|
| 1 | the `description` in the frontmatter | **every turn**, alongside the tool definitions |
| 2 | the body of `SKILL.md` | only once the model decides to activate it |
| 3 | files the body points at | only if the procedure actually needs them |

That is **progressive disclosure**, and it is the whole design. The model is shown a one-line
menu of everything available; the cost of a skill that is not used is one line.

Two consequences worth stating now:

- **The description is a trigger, not documentation.** It is the only part loaded before the
  decision to open the skill. If it does not say when to use the skill, the skill never fires.
- **Skills are chosen by the model, not by you.** They saw slash commands in Step 1 — those
  they invoked. A skill is offered, and the model decides. That is the difference, and it is
  one frontmatter line apart.

If someone asks why this is not just `CLAUDE.md`: because `CLAUDE.md` is loaded on every turn
whether it is relevant or not. Ten procedures in `CLAUDE.md` is ten procedures in the context
of every question you ask. Ten skills is ten lines.

### 3.2 They write it

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s4-skill
```

That installs `experiments/skill-scaffold.md`, already filled in with their track's names
and paths. They copy it to `.claude/skills/<first_skill>/SKILL.md` and complete the TODOs.

**Their Constraints section from Step 2b is the starting point** — have them open
`intent.md` alongside. The constraints they wrote go into the skill's Constraints almost
unchanged, which is the first time in the module that an earlier artifact pays for itself.

**Do not write it for them.** Coach on these four decisions, which are the actual content:

- **description** — what it does, and *when to use it*, in words someone would type. This is
  where most first attempts fail.
- **where things are** — explicit paths. Point at their own trace from Step 2: three wasted
  turns because the agent had to go looking. This one line removes them.
- **procedure** — in order. Push them on *why that order*: which check comes first, and which
  steps exist to rule something out. The order is the expertise; the checks are obvious.
- **constraints** — the rules a new starter gets wrong in week one. For this track the big one
  is: never call it a product defect until configuration and entitlement are both ruled out
  with evidence.

Fifteen minutes is enough for a decent first version. It does not need to be complete — they
will run it and find out what is missing, which is the point.

### 3.3 Run it, and watch it get chosen

```
python3 experiments/exp.py 5
```

**The same prompt as Step 2.** The only difference is that `Skill` is in the tool list and a
skill now exists.

Then read `.claude/lab-trace.log` together. Four things to find, in order:

**1. The model chose the skill.**
```
Skill(skill='<their skill name>', args='...')      e.g. Skill(skill='triage-ticket', ...)
```
Nobody typed that. It came *back from the model* as a request, exactly like `Read` did in
Step 1. It read a one-line description, decided this was the job, and asked for it.

**2. The body is not in the trace — and that is worth a sentence.** The result of the `Skill`
call is just `{"success": true}`. The body does not come back as a tool result; the harness
injects it into the conversation as context. So you cannot *see* the body arrive.

**3. But you can see that it arrived.** Look at what follows. The reads and commands match
their procedure, in their order. If a step of theirs was "check whether it has happened
before", there is a query doing exactly that. That correspondence is the proof.

**4. Progressive disclosure, level 3.** Their body did not contain the policy or the output
format — it *pointed* at them. In the trace, the files named in `key_files` get read after
activation. The agent went and fetched what the procedure referenced, and only what it
referenced.

### 3.3b If their skill did not fire

This is the most common thing to go wrong here, and it is not in the trace as an error — it
is simply an absent `Skill` line. Work down this list with them; the first three cost seconds.

1. **Is it in the right place?** `.claude/skills/<name>/SKILL.md` — the folder name matters,
   and the file must be exactly `SKILL.md`.
2. **Does the frontmatter `name:` match the folder name?** A mismatch is the quietest
   failure of the lot.
3. **Run the checker**, which covers both of the above and more:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_skill.py"
   ```
   It reports what would stop the skill working, and separately what would merely make it
   fire late.
4. **Read their description out loud, then read the prompt out loud.** If nothing in the
   description would make you reach for it given that prompt, that is the answer — go to
   Step 3.5 early, because they have discovered it themselves.

They do **not** need to restart anything. Each experiment runs as a fresh session, so a skill
edited a second ago is picked up on the next run. Say so if they ask — it is a reasonable
question and the answer is reassuring.

### 3.4 Compare the two runs

Both numbers are at the bottom of each block in the trace. Measured with the reference
version of each track's skill, same prompt in both columns:

| Track | No skill | With the skill |
|---|---|---|
| `support-triage` | 18 tool requests | **13** |
| `vendor-qa` | 14 | **11** |
| `docgen` | 12 | **9** |

**Use your own track's row**, and expect the participant's numbers to differ from it — their
skill is not the reference one. What holds on every track is the direction and the reason:
the opening discovery turns are gone, and the work happens in the order they specified. Ask
them which of their own lines removed those turns.

The magnitude varies for a reason worth one sentence if someone asks: the more of the job
that was *already written down in the corpus*, the less a skill has left to add. On `docgen`
the template is in the data, so the skill is mostly buying order and a decided output
location; on `support-triage` it is buying the whole investigation sequence.

Then the part that matters more than the count: **is the output in the house format now?**
Hold it against their track's `key_files.output_format`. If it is not, that is not a failure
— it is the next iteration, and the skill is a file they can edit.

### 3.5 Break the description (4 minutes, do not skip)

This is the exercise that makes the concept stick, and the result is more interesting than
"it stops working". Have them try two degraded descriptions, re-running
`python3 experiments/exp.py 5` after each and checking the trace both times for **whether
`Skill` appears and how early**.

**Variant one — vague:**
```yaml
description: Helper for tickets.
```

**Variant two — accurate, but about the wrong job:**
```yaml
description: Formats phone numbers for the billing system export.
```

Measured on the authored version of this skill, same prompt every time:

| description | did it fire? | at which tool call | tool requests |
|---|---|---|---|
| accurate — names the task *and* when to use it | yes | **1st** | **13** |
| vague — "Helper for tickets." | yes | 7th | 20 |
| wrong job — "Formats phone numbers…" | **no** | — | 17 |

Three things to draw out, and the middle one is the surprise:

1. **The accurate description gets the skill chosen first**, before the agent has guessed at
   anything. That is where the savings come from — not from the body being clever, but from
   the body arriving before the flailing starts.
2. **The vague description is worse than having no skill at all** — 20 requests against 18
   for Step 2's no-skill run. The agent blundered around for six turns, *then* found the
   skill and started the procedure over. A half-recognised skill costs you twice.
3. **The wrong description never fires.** The body was perfect and completely irrelevant,
   because nothing ever opened it.

> The body is where the value is. The description is whether anyone ever sees it — and
> whether they see it in time.

Have them restore their real description before moving on.

If a participant's vague variant still fires immediately, look at the skill's **name** with
them: a name like `triage-ticket` against a prompt saying "Triage CASE-4471" is itself a
strong signal.
That is a real finding about how the choice is made, not a broken exercise — the name is part
of the advertisement too.

### 3.6 Gate

A checkpoint that only records progress is not a gate. Validate the artifact first:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_skill.py"
```

- **Exit 0** — record the checkpoint and move on. Read out any non-blocking notes it
  printed; they are the next iteration, not a problem.
- **Exit 1** — do **not** record the checkpoint. Show them the specific problems it named
  and let them fix them. This takes a minute and it is the difference between a skill they
  own and a file they have.

Then:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C3-skill
```

Then hand over in two lines: they have given the agent their procedure. Next, Step 4, they
give it something the model cannot do at all — a real tool.

### Deliberately not covered yet

Do not raise these here, even if tempted. Each has a better home:

- **MCP** — Step 4, when they have written a tool and sharing it becomes a real question.
- **Hooks as lifecycle interceptors** — Step 5, when they write one. They have used the
  tracer all module; naming the general mechanism lands better after they have built one.
- **Cross-harness standardisation** — Step 7 or the debrief, once they have a plugin and
  portability is a concrete concern rather than a claim.


---

## Step 4 — A tool (15 minutes)

**The question this answers:** the skill told the agent *how* to do the job. Why would I ever
write code instead?

### 4.1 The frame — and do not promise speed

Say this, and mean it, because the measurements below will not support the other story:

> A skill is instructions. The agent still decides how to follow them, and it decides slightly
> differently every time. A tool is **code**: same input, same output, and you can test it.
> You reach for one when a step has a single right answer that you are not willing to leave
> to a model's judgement.

Their track has exactly such a step. On `support-triage` it is the entitlement question:
*was this account entitled to this feature on the ticket's date* — a query with a date filter
that is wrong in a way nobody notices if the model omits it. On `docgen` it is provenance:
every fact carrying the file and line it came from. On `vendor-qa` it is scanning for
credentials and production personal data, which is the thing a human reviewer skims past at
four in the afternoon.

### 4.2 They write it

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s5-tool
```

That installs `tools/<their track's tool>.py` — argument handling and JSON printing already
done, with the part that matters left as TODO. The scaffold names the three decisions worth
making deliberately; those are the coaching points, and they differ by track.

**Do not write it for them.** Two things to push on, whatever the track:

- **Print JSON and nothing else.** Anything for a human goes to stderr. The next reader is a
  program.
- **Return a dict of named facts, not a list.** Their skill is about to depend on those names.

### 4.3 Make it prove itself

The scaffold has a `--selftest` with no checks in it. Have them add at least three, one of
which must be that calling it twice with the same input gives the same result.

```
python3 tools/<tool>.py --selftest
```

This is the moment to name something that pays off for the rest of the course:

> You just wrote a test for a piece of your agent. You cannot do this to a prompt. This is
> the seed of what Module 4 calls an eval, and it is the only reason you will later be able
> to tell whether a change made things better or just different.

### 4.4 Wire it into the skill

Have them edit their skill from Step 3 to call the tool, and say what it returns. One or two
lines in *Where things are*, and a step in the procedure.

### 4.5 Re-run, and read the result honestly

```
python3 experiments/exp.py 5
```

**Same command, same flags as Step 3.** Nothing about the harness changed — only that a tool
now exists and the skill knows about it.

Now the part that needs care from you. Here is what actually happened across three runs of
the reference version on `support-triage`, same prompt every time:

| Run | Tool requests |
|---|---|
| Step 3, skill only | 13 |
| Step 4, tool + skill | 13 |
| Step 4, and the skill told explicitly to trust the tool | 16 |

**The tool did not reduce round trips.** The agent ran the snapshot and then verified parts of
it against the database anyway, and telling it not to did not stop it. Do not stand in front
of a room and predict a smaller number.

Two things to draw out instead, and they are both better than the number would have been:

1. **The agent verifying independently is not a bug.** A support engineer who double-checks a
   tool's domain list is behaving well. The tool's job is to make the authoritative answer
   *available and tested*, not to stop the agent thinking. What changed is that the
   entitlement answer now comes from tested code with the right date, every time — which is
   a correctness property, not a speed one.
2. **13, 13, 16 from the same setup.** Sit with that for a second. **You cannot tell whether
   a change helped from one run.** This is the single most useful thing in Module 1 for what
   comes later: it is why Module 2 keeps a scoreboard over fifteen queries instead of eyeballing
   one answer, and why Module 4 is largely about evals.

If a participant's run happens to drop sharply, good — say that it varies, and that one run
is not evidence either way. The lesson is the variance, not the direction.

### 4.6 Tool or MCP? (2 minutes, now that they have earned the question)

Someone will ask, and now it is answerable rather than a claim:

> A script that prints JSON **is** a tool. The agent called it through `Bash` and it worked.
> MCP is what you reach for when the tool has to outlive the exercise: a typed interface, a
> name the agent sees without being told, and one implementation shared across projects and
> machines. You will build one in Module 2, when the retrieval tool needs to be reachable
> from anywhere rather than from this folder.

The useful rule: **start with the script; promote it to MCP when it stops being yours alone.**

### 4.7 Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_tool.py"
```

It checks the things the module just claimed: no scaffold left in place, `--selftest` passing
with at least three checks, valid JSON on stdout, and the agreed keys present.

- **Exit 0** — record the checkpoint. Read out any notes; they are the next iteration.
- **Exit 1** — do not record it. The problems it names are specific and each is a minute's work.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C4-tool
```

### 4.8 Hand over

Two lines. They have a skill that carries their procedure and a tool that carries the part
that must not vary. Next, Step 5: a hook — the first thing in this module the model cannot
choose to ignore.


---

## Step 5 — A hook (15 minutes)

**The question this answers:** my skill says where to put the output. Why would I need
anything stronger than that?

### 5.1 Frame it as the difference between asking and enforcing

> A skill is **guidance the model chooses to follow**. It follows it most of the time. A tool
> is **code that runs when asked**. A hook is **code that runs whether the model likes it or
> not** — before the action, every time, with the power to refuse.

Do not explain further yet. The next two minutes make the case better than the sentence does.

### 5.2 Show the problem, do not assert it

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s6-hook
python3 experiments/exp.py 6
```

The prompt is their track's task plus one reasonable-sounding filing instruction — save the
output into `data/` "so the next person finds it alongside" the source material. Nobody is
being tricked; it is the sort of thing a colleague would ask for.

Then:

```
git status --short data/
```

On `support-triage` you will see something like `?? data/knowledge/CASE-4471-triage.md`. Their
work product is now sitting inside their evidence.

Name why that matters, once:

> Everything in `data/` is what your conclusions rest on. Once the agent can write there, you
> can no longer tell what was evidence and what the agent produced. The next triage reads
> this note as a source. That is how a corpus quietly rots.

And their skill did say where to write — their track's `output_dir`. The agent was asked
nicely and did something else, because the prompt asked it to.

### 5.3 Restore it, and notice what just saved you

```
git checkout -- data/
```

This is what the git repository from Step 0 is for. Worth ten seconds: the reason the
workspace is a repo is not tidiness, it is that you can undo an agent.

### 5.4 They write the hook

The scaffold is at `.claude/hooks/write_boundary.py`. Four decisions, in the order they bite,
and all four are in the file:

1. **Which tools to care about.** A hook on every tool that inspects `file_path` does nothing
   for `Bash` or `Grep`.
2. **Naming what is protected, or naming what is allowed.** Push on this — they met it in
   Step 1. Which of the two can ever be complete?
3. **Resolving the path.** The agent sends absolute paths; the prompt talks in relative ones.
   Compare against `CLAUDE_PROJECT_DIR` or the rule matches on some runs and not others.
4. **What the refusal says.** It is shown to the model, which will then try something else. A
   good reason redirects it. A bad one makes it retry the same thing.

### 5.5 Test it without an agent — this is the point of a hook

```
echo '{"tool_name":"Write","tool_input":{"file_path":"data/x.md"}}' | python3 .claude/hooks/write_boundary.py
echo '{"tool_name":"Write","tool_input":{"file_path":"<output_dir>/x.md"}}' | python3 .claude/hooks/write_boundary.py
echo '{"tool_name":"Read","tool_input":{"file_path":"data/x.md"}}'  | python3 .claude/hooks/write_boundary.py
```

Deny prints JSON; allow prints nothing. Three commands, no model, no waiting, definitive.
Say it out loud: **they just tested a piece of their agent's behaviour in under a second.**
That is the third time this module a deterministic component has turned out to be testable,
and it is the whole reason Module 4 can exist.

### 5.6 Register it

A hook that is not in `settings.json` never runs, and this is the most common thing to get
wrong. The snippet is in the scaffold's docstring; they add it alongside the tracer that has
been there since Step 0.

### 5.7 Run it again

```
python3 experiments/exp.py 6
```

Same prompt. Check the trace and the corpus, in that order:

- In `.claude/lab-trace.log`, a blocked write appears as a request from the model with **no
  RESULT line after it**. That absence is how a refusal looks — the tracer reports what the
  model asked for, not what the harness allowed.
- The output should land in their track's `output_dir` instead. The model usually explains the
  refusal in its answer, which is the reason they wrote in 5.4 doing its job.
- `git status --short data/`.

**Three different things happened across the tracks this material was built on**, and you
should know all three before you run it, because only one of them is the tidy demonstration:

| What you see | What it means |
|---|---|
| A `Write` request with no RESULT line, and the output redirected | The tidy case. The hook refused it |
| The corpus changed anyway, and there is no `Write` in the trace | It used `Bash` — `cp`, `mv`, a redirect. Go straight to 5.8; they have found it by the best possible route |
| Nothing happened at all — no write attempted, corpus clean | Their `CLAUDE.md` already said `data/` is read-only, and the model simply obeyed |

The third is the awkward one, because nothing visible happens and the step can fall flat.
**It is also the most honest result**: instructions do work, most of the time. Say exactly
that, then force the demonstration so they see the refusal:

```
claude --tools "Write" --strict-mcp-config \
  -p "Create a file at data/probe.md containing the word probe. Use the Write tool."
```

That is guaranteed to attempt a write into `data/`, and it comes back refused with their own
message. Which is the point in one line: *the instruction worked this time, and the hook works
every time.*

### 5.8 The hole they should find (2 minutes — worth making time for)

Ask them: *"you have blocked the write tools. How would you get round it?"*

The answer is `Bash` — `cp`, `mv`, `rm`, `sed -i`, a `>` redirect. Their hook does not match
those. Two things happened while this material was being built, and both are worth repeating
to the room:

- On one track the model **pointed the gap out unprompted** and declined to use it: *"that gap
  exists (the hook only matches write tools), but deliberately stepping around a control the
  project owner installed isn't mine to do."*
- On another it simply **used `Bash` without noticing there was a control to avoid** — it
  wanted to copy a file, so it ran `cp`. No `Write` call appeared in the trace at all.

The second is the one that matters. The hole is not exploited by a model trying to escape; it
is walked through by a model picking the obvious tool for the job. You cannot defend against
intent you are not facing.

Do not let anyone fix it by grepping shell commands. That is Step 1's lesson again: you cannot
enumerate the ways to write a file, and a rule matching `data/` also blocks
`sqlite3 data/db/support.db "SELECT ..."`, which is a read.

The real answer is that controls are layered, and this hook is one layer:

| Layer | Decides |
|---|---|
| `--tools` | which tools exist at all |
| `permissions` in settings.json | which of them may run without asking |
| **this hook** | what a permitted tool may touch |
| Module 4's gate | who approves the consequential action |

Any one of them alone is theatre. The hook's value is that it is the layer the model cannot
talk its way past — not that it is sufficient.

### 5.9 Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_hook.py"
```

It checks that the hook exists, has no scaffold left in it, is actually registered under
`PreToolUse`, and then feeds it five payloads to see what it decides.

- **Exit 0** — record the checkpoint.
- **Exit 1** — do not. Each problem it names is a minute's work, and "it exists but never
  runs" is the one it catches most.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C5-hook
```

### 5.10 Hand over

Two lines. They now have all four primitives: a skill carrying procedure, a tool carrying
what must not vary, a hook carrying what must not happen, and the harness underneath. Next,
Step 6: package them so somebody else can install the whole thing with one command.


---

## Step 6 — The plugin (20 minutes)

**The question this answers:** I have four loose things in a folder. How does somebody else
get them?

This is the module's promise. They leave with `v0.1` installed and running.

### 6.1 The decision that makes this a lesson

Do not start with the mechanics. Start with the sort:

> You have a skill, a tool, a hook, some data, and some output. **Which of those would you
> hand to a colleague, and which are yours alone?**

Let them answer. The line they are looking for:

| Goes in the plugin | Stays in the project |
|---|---|
| the **skill** — your procedure | the **data** — your evidence |
| the **tool** — code that must not vary | the **output** — what you produced |
| the **hook** — what must not happen | `CLAUDE.md`, `intent.md` — what this project is |

> A plugin is **portable capability**. The project is **this situation**. If your colleague
> installing your plugin would also need your `data/` directory, you have put the wrong thing
> in it.

The tracer stays in the project too. It is the lab's, not theirs.

### 6.2 Scaffold it

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/workspace.py" stage m1s7-plugin
```

That creates their plugin directory — named from their track's `system_name` — with a
manifest to fill in and a `hooks/hooks.json` already written, plus `CLAUDE.md` and
`intent.md` at the project root.

They move their skill, tool and hook in. Copy or `git mv`, their choice; `git mv` makes the
point that this is a reorganisation, not new work.

### 6.3 The two paths that will break, and why that is the lesson

This is the part worth your attention as a facilitator, because both breakages are
predictable and both teach the same thing.

**The tool's own path.** Their tool almost certainly computes its data location from
`__file__`. That worked when it sat in `tools/` next to `data/`. Inside the plugin it now
resolves to the *plugin's* directory, and the data is not there. The fix is to resolve
against the project:

```python
os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
```

**The skill's reference to the tool.** Their skill says `python3 tools/<tool>.py`. That path
is relative to whoever installed the plugin, which is not them. It has to become:

```
python3 "${CLAUDE_PLUGIN_ROOT}/tools/<tool>.py"
```

Name the distinction once, because it is the whole of Step 6:

> **`${CLAUDE_PLUGIN_ROOT}`** is where the capability lives. **`${CLAUDE_PROJECT_DIR}`** is
> where the situation lives. Code and procedure use the first. Data and output use the second.
> Getting these the wrong way round is why a plugin works for its author and nobody else.

### 6.4 Validate it with the real tool

```
claude plugin validate ./<their plugin>
```

This is not a lab script — it is the same command anybody publishing a plugin runs. Worth
saying so.

### 6.5 Run it, and prove it is coming from the plugin

```
python3 experiments/exp.py 7
```

Same task as Step 3 and Step 4. The command now carries `--plugin-dir ./<their plugin>`, and
the capability arrives from the plugin rather than from loose files.

To make it undeniable, have them **move the project-level copies out of the way** first — rename
`.claude/skills/` and `tools/` — and run it again. If it still works, the plugin is genuinely
self-contained. If it stops working, they have found a path they have not fixed yet, which is
better to find now than in Module 2.

Then look at the trace for the thing that surprises people:

```
Skill  <plugin-name>:<skill-name>
```

**The skill is namespaced now.** It was `write-report`; it is `report-builder:write-report`.
That is what packaging does — it gives the capability an owner. Mention that this is also why
plugin authors care about the plugin's `name`: it is the namespace everyone will type.

Check the hook came too. The plugin's `hooks/hooks.json` is loaded along with everything else,
so the write boundary now travels with the capability rather than living in one project's
settings. Verified: a `Write` into `data/` is refused by the plugin's own hook, with the
plugin's own message.

### 6.6 `CLAUDE.md` and `intent.md` (5 minutes, and do not skip `intent.md`)

Two files, two different jobs, and the distinction is worth stating plainly:

- **`CLAUDE.md`** is loaded on **every turn**, so it is the most expensive text in the
  project. Only what is true for every task: what this is, where the data is, where output
  goes, what a newcomer gets wrong. If they start writing a procedure, stop them — that is a
  skill.
- **`intent.md`** they already wrote, in Step 2b. What changes here is the **first line of
  `CLAUDE.md`**: an `@intent.md` import, which is what puts it in context every turn rather
  than leaving it as a file nobody loads.

Check the import is actually there — `check_plugin.py` will refuse without it. Then point out
what it costs: their intent is now paid for on every turn, which is the reason it had to stay
under forty lines. If theirs has grown, this is the moment to trim it, and trimming an intent
is a better use of two minutes than it sounds.

Their **Proposed outcome** section becomes their acceptance criteria in Module 4 almost
verbatim. Say so.

### 6.7 Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin.py"
```

It checks the manifest, that the components are actually *in* the plugin rather than left
behind, that `hooks.json` uses `${CLAUDE_PLUGIN_ROOT}` rather than the project path, that the
skill does not call its tool by a project-relative path, and then runs
`claude plugin validate`. It also refuses a `CLAUDE.md` or `intent.md` with scaffold TODOs
left in them.

- **Exit 0** — record the checkpoint. They have `v0.1`.
- **Exit 1** — do not. The portability problems are the point of the step.

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" checkpoint M1.C6-plugin
```

### 6.8 Hand over

Say it plainly, because they have earned it: **they built a plugin.** It has a procedure, code
that does not vary, a boundary that cannot be argued with, and it installs with one flag. Then
the debrief.


---

## Step 7 — Debrief (10 minutes)

**Run this as a conversation, not a summary.** They have done the work; the debrief is where
they get the words for it. Ask first, supply second. If a participant can answer the opening
question unprompted, the module worked and you should say so.

### 7.1 Ask the question the module opened with

> **"What is an agent, what is the harness made of, and which primitive do you reach for?"**

Let two or three people try. What you are listening for, in their own words:

- an agent is **the loop**, not the model — request, tool request, result, request again
- the harness is what holds the loop: the tools, the context it accumulates on your behalf,
  the permissions, the hooks, and the skills it offers the model
- the model itself is stateless and knows nothing about their organisation

If nobody gets to "the loop", open `.claude/lab-trace.log` at the Step 1 block and read the
call count out loud. It is a better answer than any explanation.

### 7.2 The rule for choosing a primitive

This is the thing they will use on Monday. Four questions, in order — the first "yes" wins:

| Ask | If yes | Because |
|---|---|---|
| Must it be **identical every time**? | a **tool** | code does not have judgement, and can be tested |
| Must it happen **whether the model agrees or not**? | a **hook** | it runs before the action, and can refuse |
| Is it **how we do this particular job**? | a **skill** | procedure, loaded only when relevant |
| Is it true for **every task in this project**? | **`CLAUDE.md`** | but it costs context on every single turn |

Then one more, which is a different axis entirely:

> **Do you invoke it, or should the agent decide?** Same file either way — one frontmatter
> line apart. `disable-model-invocation: true` makes it yours to type; leaving it off makes
> the description a trigger.

And last: **would a colleague want this?** Then it goes in the plugin. If they would also need
your `data/` directory to use it, something is in the wrong pile.

### 7.3 What they measured today

Put this up. Every row is something they watched happen, not a claim anyone made:

| What changed | What was measured |
|---|---|
| `--tools ""` → `"Read"` → `"Read,Write"` | **1 → 2 → 3** calls to the model |
| No skill → a skill | 18 → **13** tool requests (`support-triage`); 12 → 9 (`docgen`); 14 → 11 (`vendor-qa`) |
| Description accurate → vague → about the wrong job | fires **1st** (13 requests) → fires 7th (**20**) → **never fires** |
| Skill → skill + tool | 13, 13, **16** across three runs — no reliable change |
| Hook off → hook on | corpus modified → write refused and redirected |

Two of those rows are the important ones, and they are the two that did not go the way you
would have predicted:

- **A vaguely described skill is worse than no skill** (20 against 18). It flails, then finds
  the skill, then starts the procedure over. You pay twice.
- **Three identical runs gave 13, 13 and 16.** Ask them: *"how would you know if a change you
  made had helped?"* Sit in the silence. That question is Module 2 and Module 4.

### 7.4 The anti-patterns, each one earned

Ask which of these they nearly did. Most will own two or three.

- **Putting a rule in a skill when it needed a hook.** Their skill said where to write the
  output. In Step 5 the agent wrote somewhere else anyway. A skill is a request.
- **Writing a description that documents instead of triggers.** Measured: it fires seventh
  instead of first, or never.
- **A deny list.** They watched one leak a dozen tools in Step 1. Allowlists are the only
  kind that can be complete.
- **A tool that makes judgements.** If it has to weigh something, it is a skill. A tool that
  varies is a script you hope works.
- **Procedure in `CLAUDE.md`.** It is loaded on every turn, relevant or not. Ten procedures
  there is ten procedures in the context of every question.
- **The mega-skill.** One `SKILL.md` for everything: the description cannot trigger precisely
  and the body loads material for jobs you are not doing.
- **A plugin that only works for its author.** The two paths that broke in Step 6.

### 7.5 What carries into the rest of the course

Four threads. Name them explicitly, because each is a whole module:

| From today | Becomes |
|---|---|
| The model knows nothing about your organisation (Step 1) | **Module 2** — retrieval, and grounding it in your documents |
| Context accumulates on every call; it is a budget | **Module 2** — why chunking and retrieval matter at all |
| You cannot tell from one run whether a change helped | **Module 2's scoreboard, Module 4's evals** |
| Controls are layered, and the last layer is a human | **Module 4** — the approval gate |

And one direct handover: **the "what good looks like" section of their `intent.md` becomes
their eval criteria in Module 4, almost verbatim.** If they skipped it, now is the moment to
say that they will be writing it in Module 4 either way, and it is cheaper to write while the
work is fresh.

### 7.6 Close the module

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" complete-module 01
```

Tell them plainly what they have: a plugin they built, with a procedure, code that does not
vary, a boundary that cannot be argued with, and a manifest so somebody else can install it.
It runs on their machine and it is theirs.

### 7.7 The optional extension

Never required, never gating, and worth mentioning once:

> **Add a second skill to your plugin**, for a different task in your track. The interesting
> part is not the writing — it is watching two skills compete for the same prompt, and finding
> out what you have to put in each description to make the right one win.

That is genuinely the best preparation for Module 2 that exists, because it is the same problem
retrieval has: many candidates, one question, and a decision about relevance.

### 7.8 If the clock has beaten you

The module works with Step 7 cut to three minutes: ask 7.1, put up the table in 7.3, and name
the two surprising rows. Everything else can go. What must not be cut is 7.3 — a room that
leaves without *"three identical runs gave 13, 13 and 16"* has no reason to care about
Module 2.
