# {{SYSTEM_NAME}}

@intent.md

TODO — three or four lines below the import. This file is loaded on **every turn**, so it is
the most expensive text you will write. Put here only what is true for every task:

- what this project is, in a sentence
- where the data lives, and that it is read-only evidence
- where output goes
- anything a newcomer would get wrong on their first attempt

Anything that is only true for *one* task belongs in a skill, not here. If you find yourself
writing a procedure, stop — that is the difference between this file and `skills/`.

The `@intent.md` line on the second line is an **import**: Claude Code expands it at launch,
so your intent is in context for every turn rather than sitting in a file nobody opens. That
is also why intent has to stay short.
