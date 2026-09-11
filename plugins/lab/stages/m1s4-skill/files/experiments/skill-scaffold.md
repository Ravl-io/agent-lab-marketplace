# Scaffold — your first skill

Copy this to `.claude/skills/{{SKILL_NAME}}/SKILL.md` and fill in the TODOs. The shape is
given; the decisions are yours, and they are the part that matters.

```markdown
---
name: {{SKILL_NAME}}
description: TODO
---

# TODO — a title for the job

TODO — one or two sentences: what job is this, and what does "done" look like?

## Where things are

TODO — list the paths this job needs. Be explicit. If you leave this out, the agent spends
its first few turns running `find` and `ls` to work out where your data lives. You saw that
happen in the last experiment; look at the trace again if you want to count them.

## Procedure

TODO — numbered steps, in the order you want them done.

Think about what you actually do at work, in order. Which check comes first, and why that
one? Include the exact commands or queries you would run, where there are any. If a step
exists in order to *rule something out*, say so — the order of the checks is the expertise
here, not the checks themselves.

## Output

TODO — point at `{{OUTPUT_FORMAT_FILE}}`, which is the format your team actually reviews.

Do not paste that format in here. Reference the file and tell the agent to read it. That is
the difference between a skill and a wall of text, and you will see it in the trace: the
agent goes and fetches what the procedure references, and only what it references.

## Constraints

TODO — what must it never do?

The useful ones are the rules a new starter would get wrong in their first week. Your
track's policy is in `{{POLICY_FILE}}` if you want a reminder of what those are.
```

## What goes in the description, and why it matters more than it looks

The `description` is **the only part of this file the agent sees** before deciding whether to
open it. It is loaded on every single turn, alongside the tool definitions. The body is not
loaded until the agent chooses to activate the skill.

So the description is not documentation. It is a **trigger**. Write it to answer two
questions:

1. What can this do?
2. When should it be used — in the words someone would actually type?

A vague description like `Helper for stuff` gets picked up late, after the agent has already
started guessing, which costs more than having no skill at all. A description about the wrong
job never fires and your body is never read. You are going to test exactly this, so write
your first attempt and expect to change it.
