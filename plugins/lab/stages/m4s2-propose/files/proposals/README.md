# proposals/

Where the agent writes what it thinks should happen. **Nothing here has any effect.**

| File | What it is |
|---|---|
| `<id>.md` | the proposal a human reads before approving |
| `<id>.json` | the same decision, machine-readable: actions, evidence, confidence, risk, rollback |

Writing a proposal is unguarded, because proposing changes nothing. Applying one is guarded,
because it does.

## The three things an approver is actually deciding

**What will happen** — the `actions` list, and nothing outside it.

**How sure, and how bad if wrong** — `confidence` and `risk`, which vary independently. A
high-confidence, high-risk proposal still deserves a careful read.

**What is unknown** — `unresolved`. A gap the proposal declares is one the approver can
weigh. A gap it smooths over becomes theirs after they have signed.

## Approving one

```
python3 gate/approve.py <id> --show      read it
python3 gate/approve.py <id>             approve it
python3 tools/apply.py <id>              apply it
```

The approval records a hash of the proposal *and* its prose body. **Edit either after
approval and applying is refused** — the approval covers what was read, not whatever is
there now. That is the difference between an approval and a permission.
