# Your workspace — L2 Support Triage

You are on the level-2 support team at **Northwind**, a SaaS platform. Tickets reach you from
Salesforce once level 1 has escalated them: a user says they cannot do something, and nobody
yet knows why.

Your job is the first diligence. Read the ticket, check how the account is configured, look
in the database at what the user actually tried and what the platform told them, and decide
which of these it is:

- **Configuration** — something in the account's setup is wrong. We can fix it.
- **User error** — the user is doing something their plan, role or permissions do not allow.
- **Product defect** — the platform did the wrong thing. This goes to the vendor.
- **Need more information** — you cannot responsibly say yet.

Two thirds of what arrives as "a bug" turns out to be one of the first two. Getting that
distinction right, with evidence, is the whole job.

## What is in here

```
data/
├── tickets/                  four escalated tickets from Salesforce
├── db/
│   ├── support.db            accounts, users, entitlements, audit log, case history, vendor cases
│   └── schema.md             what is in it, and the queries that matter
├── knowledge/
│   ├── triage-policy.md      the four classifications, and how to choose
│   ├── configuring-sso.md    how login routing actually works
│   ├── plan-entitlements.md  which plan includes what — and what changed in June
│   ├── bulk-export-guide.md  the feature, and the workaround
│   ├── known-issues.md       defects already open with the vendor
│   └── escalation-policy.md  what the vendor requires, and how to validate a fix
└── examples/
    ├── triage-note-example.md         the format your output must match
    └── vendor-escalation-example.md   what an escalation looks like
notes/                        yours
```

Start with `data/tickets/CASE-4471.md`. Everything you need to resolve it is in this folder —
the answer is not in the ticket, and that is the point.

## Where you are going

| Module | What your system will do |
|---|---|
| 1 | Turn a ticket into a triage note with a classification and its evidence — same shape every time |
| 2 | Retrieve from the knowledge base and known-issues register, so a triage cites the article behind it |
| 3 | Reason over a graph of accounts, features, defects and vendor cases — "who else is affected by this" |
| 4 | Propose the resolution — customer reply, config fix, or vendor escalation — behind a human approval gate |

## Starting

Run `/lab:next`.

Module 1 starts by having you triage a ticket with nothing but a plain prompt, deliberately
crudely, so that everything after it has a reason.
