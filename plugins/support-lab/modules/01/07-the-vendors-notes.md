# Step 7 — The vendor's own notes (4 minutes)

**What this step teaches:** when a component was upgraded, read that component's release
notes. Vendors usually document the thing that just bit you.

## Frame — under 3 lines

The export engine is a third-party component, OpenReport, and it went from 3.1 to 3.2 this
morning. There is no web access here, but the vendor's release notes are saved in the docs.

## Ask

> **Read the vendor release notes for OpenReport 3.2 under docs/vendor and tell me whether
> anything there, including any known issue, matches what we are seeing.**

## Judge — when they say "next"

From `docs/vendor/openreport-3.2-release-notes.md`:

- Paginated export now **flushes every 500,000 rows**; each page is committed before the
  next, so **the wall-clock time to the first byte increases**, and *"callers with
  request-level timeouts must raise them accordingly."* That is the answer to yesterday's
  puzzle: the timeout counts until the engine starts sending. On 3.1 that was immediate; on
  3.2 it is not.
- **Known issue #412**: exports over 1M rows that completed in 60–90 s on 3.1 may exceed
  120 s on 3.2 when the source query is unsorted. Workaround: raise the caller timeout, or
  set `paginate_threshold` above the report size. Fix planned for 3.2.2.

Bonus, if Claude Code found it or they ask: the product's own release page
`docs/releases/2.4.1.md` says *"No configuration changes required."* That is a documentation
gap and belongs in the findings.

Wrap in two lines: they now have a cause with a timestamp, a vendor note that names it, and a
setting that made the customer vulnerable to it. Time to write it down.

## Gate

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state.py" clear S7
```
