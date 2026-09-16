# Step 6 — Last known good (6 minutes)

**What this step teaches:** the question that separates a good first look from a fast one —
*did this ever work with the same settings?* If it did, the settings are not what changed.

## Frame — under 4 lines

The customer said it worked yesterday evening. We can check that, not take their word for it.
If the same export, with the same 30-second setting, succeeded yesterday, then the setting
cannot be the thing that broke it today.

## Ask

> **Did this same export succeed before today with the same settings? Check yesterday's API
> log and the exports table, and tell me when it last worked, how long it took, and which
> engine version ran it.**

## Judge — when they say "next"

- Last success: **2026-09-15T18:40:07Z**, status 200, **84,210 ms**, engine
  **openreport-3.1** (`logs/api-2026-09-15.log`; also row 80 in the `exports` table).
- The `exports` table shows **eight more successes in September**, all on engine 3.1, all
  around 84 seconds — and every attempt today failed at 30,004 ms on engine 3.2.

Ask them: *"Same report, same 30-second setting, worked yesterday. So is the setting the
cause?"* The answer they should reach: the setting was already below what the docs recommend,
but it did not change. The engine did. So the timeout is at most **part** of the story —
"partial", not "verified".

If someone asks how an 84-second export succeeded with a 30-second timeout, do not guess.
Say the next step answers it (the vendor's notes explain what the timeout actually measures).

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S6
```
