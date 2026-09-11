# Your workspace — Document Transformation & Reporting

Every month someone spends a day turning meeting notes, status updates and metric extracts
into the Monthly Delivery Report. It is slow, it reads differently depending on who wrote it,
and half the claims in it cannot be traced back to anything.

Over the four modules you will build a system that produces that report — cited, in house
style, published only after a human approves it.

## What is in here

```
data/
├── sources/                     this month's raw material: sync notes, status updates, metrics
├── template/
│   └── monthly-report-template.md   the structure the report must follow
├── house-style.md               the rules the writing must obey
└── examples/
    └── report-2026-07.md        last month's published report — your target quality
notes/                           yours
```

Your job this month is **August 2026**. Last month's report is in `examples/` so you can see
what good looks like — and so that in Module 3 you can answer what actually changed between
the two.

## Where you are going

| Module | What you will have built |
|---|---|
| 1 | A skill that writes one report section in house style from the template — consistently |
| 2 | Retrieval over the sources, so every claim carries a citation instead of a guess |
| 3 | An entity graph of projects, owners, milestones and risks, so the report can aggregate and cross-reference |
| 4 | Full report generation with gaps flagged, gated on a human approving publication |

## The handbook

`handbook.html` in this folder is the reference for the whole course — the modules, the
commands, how to read a trace, and what to do when something breaks. Open it from the file
tree and leave it in a tab. It is a local file, so it needs no network.

## Starting

Run `/lab:next`. The tutor will tell you what to do first.

Module 1 starts by having you write a section the crude way, on purpose, so that everything
that follows has a reason.
