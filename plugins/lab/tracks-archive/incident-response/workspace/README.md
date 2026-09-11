# Your workspace — Incident Response

You are on the platform team at **Northwind Payments**. Alerts fire, and whoever is on call
has about three minutes to work out what is happening, whether it has happened before, what
else it affects, and what to do about it.

Over the four modules you will build a system that does that work and proposes a fix — one
that a human approves before anything is applied.

## What is in here

```
data/
├── service-catalogue.md      every service, its team, its tier, what it depends on
├── runbooks/                 how to handle each service when it misbehaves
├── postmortems/              what went wrong before, and why
├── alerts/                   three real alerts, waiting to be triaged
└── examples/
    └── triage-note-example.md   the format an on-call engineer expects
notes/                        yours — the tutor will ask you to write things down here
```

This is your data to work with, not to protect. Read it, grep it, break it apart. You will be
chunking and re-chunking these documents in Module 2 and extracting a graph from them in
Module 3.

## Where you are going

| Module | What you will have built |
|---|---|
| 1 | A skill that turns an alert into a triage note — the same shape every time |
| 2 | Retrieval over the runbooks and postmortems, so triage cites the prior incident it resembles |
| 3 | A service dependency graph, so it can answer "what else is affected by this" |
| 4 | A remediation proposal with evidence and rollback, blocked behind a human approval gate |

## Starting

Run `/lab:next`. The tutor will tell you what to do first.

Do not read ahead and do not try to build the finished thing now. Module 1 starts by having
you do this task the crude way, on purpose, so that everything that follows has a reason.
