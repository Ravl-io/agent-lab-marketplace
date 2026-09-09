# Lab task cards — pick ONE (Module 1, 25 minutes, in pairs)

The goal is NOT to finish. The goal is to notice how the harness behaves.

Before any card: read `intent.md` and `CLAUDE.md` → run `/context` → check `/model` and
`/effort` once → enter plan mode. Point at files with `@`. Done = `python scripts/check_style.py`
prints `STYLE CHECK: PASS` and `summaries/index.md` is updated. `/clear` before a second card.

## Card A — The weekly summary (recommended first run)
> Plan first. Do what intent.md asks: produce the weekly ops summary for Aug 10–23 from
> @reports/, following the house style in CLAUDE.md, and update summaries/index.md.
> Done means check_style.py passes — paste its output. Ask me anything unclear before you start.

Watch for: CLAUDE.md read? `summarize-ops` fired without being named? The SEV2/SEV3
ambiguity in the webhook report — flagged or guessed? Style checker run unprompted?

## Card B — The skeptical review
> Plan first. Review @summaries/2026-08-10-weekly-summary.md against @reports/ and the house
> style. List every claim that doesn't trace to a report, every style violation, and anything
> that would mislead an executive. Do not edit anything yet — report first.

Watch for: does it respect "don't edit yet"? What evidence does it cite? Then ask it to fix
ONE finding — and watch which permission prompts appear.

## Card C — Change the rules (stretch)
> Plan first. Our incident severity scale is changing: add SEV4 (no impact, near-miss).
> Update the project so that FUTURE summaries handle SEV4 correctly. Tell me which files you
> intend to touch and why before you touch them.

Watch what it decides to touch: CLAUDE.md? the skill? the checker? all three?
Finish with: "Capture what we just did as a reusable skill: when the severity scale changes,
what has to be updated and checked." Read the SKILL.md it writes — is the description a good
signal? Is there a check for done?

## Lenses
- Builder: inspect diffs, the skill file, `.claude/settings.json`, and what `/context` showed.
- Practitioner: judge the plan, the questions it asks, the output quality.
- Both: note every permission prompt — would YOUR policy allow it? Draft one day-one rule.
