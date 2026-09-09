#!/usr/bin/env python3
"""Test suite for scripts/check_style.py — the weekly ops summary house-style checker.

Run it with either of:
    python scripts/test_check_style.py
    python -m unittest discover -s scripts -p 'test_*.py'

No third-party dependencies. Every test builds a small summary in a temporary
directory; nothing under reports/ or summaries/ is written to.

Two groups matter most:
  * RegressionTests  — cases that the checker once passed silently. They are the
    reason the severity and owner checks were rewritten; if one of these ever
    passes again, an enforcement hole has reopened.
  * GoldenFileTests  — every real summary in summaries/ must keep passing, so a
    future tightening of the rules cannot quietly invalidate published work.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKER = REPO / "scripts" / "check_style.py"
SUMMARIES = REPO / "summaries"

sys.dont_write_bytecode = True  # keep scripts/ free of a __pycache__ directory

_spec = importlib.util.spec_from_file_location("check_style", CHECKER)
check_style = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_style)


TITLE = "# Weekly Ops Summary — Aug 10 to Aug 23, 2026"
TLDR = "**TL;DR** — One incident, resolved the same morning."
ROW = "| Payments slowdown | 30m | Checkout slow, not down | SEV2 |"
CHANGE = "- Move reporting queries onto a read replica — Dana R."


def build(title=TITLE, tldr=TLDR, rows=(ROW,), changes=(CHANGE,), watch=(), filler=0):
    """Assemble a summary document from parts. Each part is overridable per test."""
    parts = [title, "", tldr, "", "## Impact", "",
             "| Incident | Duration | Customer impact | Severity |",
             "|---|---|---|---|"]
    parts += list(rows)
    parts += ["", "## What we're changing", ""]
    parts += list(changes)
    if watch:
        parts += ["", "## Watch items", ""]
        parts += list(watch)
    if filler:
        parts += ["", " ".join(["word"] * filler)]
    return "\n".join(parts) + "\n"


class StyleTestCase(unittest.TestCase):
    """Base class giving each test a temporary file and two assertions."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def issues(self, doc: str) -> list[str]:
        path = self.dir / "summary.md"
        path.write_text(doc, encoding="utf-8")
        return check_style.check(path)

    def assertClean(self, doc: str):
        found = self.issues(doc)
        self.assertEqual(found, [], f"expected no issues, got: {found}")

    def assertFlags(self, doc: str, contains: str):
        found = self.issues(doc)
        self.assertTrue(found, f"expected an issue mentioning {contains!r}, got a clean pass")
        self.assertTrue(
            any(contains.lower() in i.lower() for i in found),
            f"expected an issue mentioning {contains!r}, got: {found}",
        )


class TitleTests(StyleTestCase):
    def test_correct_title_passes(self):
        self.assertClean(build())

    def test_wrong_heading_is_flagged(self):
        self.assertFlags(build(title="# Ops Notes for August"), "Title")

    def test_title_must_be_the_first_line(self):
        self.assertFlags(build(title="Some preamble.\n\n" + TITLE), "Title")


class LengthTests(StyleTestCase):
    def test_short_summary_passes(self):
        self.assertClean(build())

    def test_over_the_word_cap_is_flagged(self):
        self.assertFlags(build(filler=check_style.MAX_WORDS + 50), "Length")


class TldrTests(StyleTestCase):
    def test_three_sentences_pass(self):
        self.assertClean(build(tldr="**TL;DR** — One. Two. Three."))

    def test_four_sentences_are_flagged(self):
        self.assertFlags(build(tldr="**TL;DR** — One. Two. Three. Four."), "TL;DR")

    def test_missing_tldr_is_flagged(self):
        self.assertFlags(build(tldr="Just an ordinary opening paragraph."), "TL;DR")


class StructureTests(StyleTestCase):
    def test_missing_impact_section_is_flagged(self):
        doc = f"{TITLE}\n\n{TLDR}\n\n## What we're changing\n\n{CHANGE}\n"
        self.assertFlags(doc, "Structure")

    def test_missing_changes_section_is_flagged(self):
        doc = f"{TITLE}\n\n{TLDR}\n\n## Impact\n\n| A | B | C | SEV1 |\n"
        self.assertFlags(doc, "Structure")

    def test_sections_out_of_order_are_flagged(self):
        doc = (f"{TITLE}\n\n{TLDR}\n\n## What we're changing\n\n{CHANGE}\n\n"
               "## Impact\n\n| Incident | Duration | Customer impact | Severity |\n"
               "|---|---|---|---|\n" + ROW + "\n")
        self.assertFlags(doc, "Structure")


class SeverityTests(StyleTestCase):
    def test_each_valid_code_passes(self):
        for sev in sorted(check_style.SEVERITIES):
            with self.subTest(sev=sev):
                self.assertClean(build(rows=(f"| Thing | 35m | Some impact | {sev} |",)))

    def test_code_with_a_parenthetical_note_passes(self):
        self.assertClean(build(rows=("| Thing | 35m | Some | SEV2 (unsettled, see Watch items) |",)))

    def test_invalid_code_is_flagged(self):
        self.assertFlags(build(rows=("| Thing | 35m | Some | SEV9 |",)), "Severity")

    def test_note_without_parentheses_is_flagged(self):
        self.assertFlags(build(rows=("| Thing | 35m | Some | SEV2 unsettled |",)), "Severity")

    def test_prose_instead_of_a_code_is_flagged(self):
        self.assertFlags(build(rows=("| Thing | 35m | Some | high |",)), "Severity")

    def test_missing_sev_prefix_is_flagged(self):
        self.assertFlags(build(rows=("| Thing | 35m | Some | 2 (degradation) |",)), "Severity")

    def test_empty_severity_cell_is_flagged(self):
        self.assertFlags(build(rows=("| Thing | 35m | Some |  |",)), "Severity")

    def test_one_bad_row_among_good_rows_is_flagged(self):
        rows = ("| A | 35m | Some | SEV1 |",
                "| B | 30m | Some | SEV9 |",
                "| C | 66h | Some | SEV3 |")
        self.assertFlags(build(rows=rows), "SEV9")

    def test_parentheses_elsewhere_in_the_row_do_not_confuse_the_check(self):
        self.assertClean(build(rows=("| Thing | 3h 10m | None (internal dashboards stale) | SEV3 |",)))


class OwnerTests(StyleTestCase):
    def _doc(self, bullet):
        return build(changes=(bullet,))

    def test_accepted_owner_formats(self):
        for tail in ("Dana R.", "Priya", "Dana R. and Priya S.", "Dana R., Marcus T.",
                     "Dana R. & Priya S.", "Ana Ruiz-Marin", "Jean Luc Picard"):
            with self.subTest(owner=tail):
                self.assertClean(self._doc(f"- Do the thing — {tail}"))

    def test_owner_after_a_mid_sentence_dash_passes(self):
        self.assertClean(self._doc("- Move reporting queries — the nightly ones — off the pool — Marcus T."))

    def test_bullet_with_no_dash_is_flagged(self):
        self.assertFlags(self._doc("- Do the thing right away"), "owner")

    def test_dash_followed_by_a_sentence_is_flagged(self):
        self.assertFlags(self._doc("- Do the thing — we will decide the owner later"), "owner")

    def test_dash_with_nothing_after_it_is_flagged(self):
        self.assertFlags(self._doc("- Do the thing —"), "owner")


class BulletCapTests(StyleTestCase):
    def test_change_bullets_at_the_cap_pass(self):
        bullets = [f"- Change number {i} — Dana R." for i in range(check_style.MAX_CHANGE_BULLETS)]
        self.assertClean(build(changes=bullets))

    def test_too_many_change_bullets_are_flagged(self):
        bullets = [f"- Change number {i} — Dana R." for i in range(check_style.MAX_CHANGE_BULLETS + 1)]
        self.assertFlags(build(changes=bullets), "Changes")

    def test_watch_items_at_the_cap_pass(self):
        watch = [f"- Watch item {i}." for i in range(check_style.MAX_WATCH_ITEMS)]
        self.assertClean(build(watch=watch))

    def test_too_many_watch_items_are_flagged(self):
        watch = [f"- Watch item {i}." for i in range(check_style.MAX_WATCH_ITEMS + 1)]
        self.assertFlags(build(watch=watch), "Watch items")

    def test_watch_items_do_not_need_an_owner(self):
        self.assertClean(build(watch=("- Cart abandonment is not yet quantified.",)))


class RegressionTests(StyleTestCase):
    """Cases the checker once passed silently. Each must stay flagged."""

    def test_bad_severity_hidden_behind_a_note(self):
        # Was invisible: the old check only matched a cell containing the code alone.
        self.assertFlags(build(rows=("| Thing | 35m | Some | SEV9 (pending) |",)), "SEV9")

    def test_change_bullet_with_a_dash_but_no_name(self):
        # Was invisible: the old check asked only whether a dash appeared anywhere.
        self.assertFlags(build(changes=("- Do the thing — this one is urgent.",)), "owner")

    def test_empty_severity_cell_not_read_as_a_separator_row(self):
        # Was invisible while separator detection accepted the empty string.
        self.assertFlags(build(rows=("| Thing | 35m | Some |  |",)), "Severity")


class GoldenFileTests(unittest.TestCase):
    """Every published summary must pass the checker as it stands."""

    def test_published_summaries_pass(self):
        files = sorted(SUMMARIES.glob("*-weekly-summary.md"))
        self.assertTrue(files, f"no summaries found in {SUMMARIES}")
        for path in files:
            with self.subTest(summary=path.name):
                self.assertEqual(check_style.check(path), [],
                                 f"{path.name} no longer passes the checker")


class CommandLineTests(StyleTestCase):
    """The workflow in CLAUDE.md depends on the exit code and the PASS line."""

    def _run(self, doc):
        path = self.dir / "summary.md"
        path.write_text(doc, encoding="utf-8")
        return subprocess.run([sys.executable, str(CHECKER), str(path)],
                              capture_output=True, text=True)

    def test_clean_summary_exits_zero_and_prints_pass(self):
        result = self._run(build())
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("STYLE CHECK: PASS", result.stdout)

    def test_failing_summary_exits_one_and_lists_issues(self):
        result = self._run(build(rows=("| Thing | 35m | Some | SEV9 |",)))
        self.assertEqual(result.returncode, 1)
        self.assertIn("STYLE CHECK:", result.stdout)
        self.assertNotIn("PASS", result.stdout)

    def test_missing_file_exits_one(self):
        result = subprocess.run([sys.executable, str(CHECKER), str(self.dir / "nope.md")],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
