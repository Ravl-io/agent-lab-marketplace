# Your workspace — Vendor QA

Your team owns a workstream delivered by **Halbrook Systems**. Milestone 3 has just been
submitted for acceptance. Someone has to establish whether what was promised is what shipped
— with evidence, because the findings go back to the supplier and they will push back.

Over the four modules you will build a system that does that review and produces a findings
pack a human signs off before it is issued.

## What is in here

```
data/
├── contract/
│   ├── MSA-excerpt.md          the master agreement — acceptance, standards, security, SLAs
│   └── SOW-milestone-3.md      what Milestone 3 promised, and its acceptance criteria
├── requirements-register.md    every requirement, and what verifies it
├── deliverables/               what Halbrook actually submitted — the thing under test
└── examples/
    └── findings-pack-example.md   the format findings are issued in
notes/                          yours
```

The contract has been **amended once**, and one clause is judged differently depending on the
date. That is deliberate, and it will matter in Module 3.

## Where you are going

| Module | What you will have built |
|---|---|
| 1 | A skill that reviews one deliverable against a checklist and emits findings in a fixed format |
| 2 | Retrieval over the contract, so every finding cites the exact clause it rests on |
| 3 | A requirement-to-deliverable-to-finding graph, so you can answer "which requirements has nobody verified" |
| 4 | A findings pack with severity and evidence, gated on human sign-off |

## The handbook

`handbook.html` in this folder is the reference for the whole course — the modules, the
commands, how to read a trace, and what to do when something breaks. Open it from the file
tree and leave it in a tab. It is a local file, so it needs no network.

## Starting

Run `/lab:next`. The tutor will tell you what to do first.

Module 1 starts by having you do this review the crude way, on purpose, so that everything
that follows has a reason.
