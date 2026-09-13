#!/usr/bin/env python3
"""Static self-test for the Agent Lab plugin.

Checks the things that break silently and only show up in front of a room: a stage payload
that leaks one track's task to every group, a placeholder nobody resolves, a file the module
tells participants to open that does not exist on their track.

    python3 lab/scripts/selftest.py            run everything
    python3 lab/scripts/selftest.py --verbose  list every check

Exits non-zero if any check fails. No model calls, no network.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACKS = os.path.join(PLUGIN_ROOT, "tracks")
STAGES = os.path.join(PLUGIN_ROOT, "stages")
SCRIPTS = os.path.join(PLUGIN_ROOT, "scripts")

TEXT_EXT = (".md", ".json", ".txt", ".prompt", ".yaml", ".yml", ".py", ".sh")

REQUIRED_TRACK_FIELDS = [
    "id", "name", "order", "tagline", "system_name", "example_brief", "scenario",
    "best_for", "difficulty", "data_you_get", "you_will_build", "final_deliverable",
    "graph_payoff", "temporal_payoff", "first_input", "first_task", "first_skill",
    "general_question", "unknown_item", "key_files",
]

failures: list[str] = []
warnings: list[str] = []
passed = 0


def check(ok: bool, label: str, detail: str = "", verbose: bool = False) -> None:
    global passed
    if ok:
        passed += 1
        if verbose:
            print(f"  pass  {label}")
    else:
        failures.append(f"{label}" + (f" — {detail}" if detail else ""))


def warn(label: str) -> None:
    warnings.append(label)


def track_ids() -> list[str]:
    return sorted(d for d in os.listdir(TRACKS)
                  if os.path.exists(os.path.join(TRACKS, d, "track.json")))


def stage_ids() -> list[str]:
    return sorted(d for d in os.listdir(STAGES)
                  if os.path.exists(os.path.join(STAGES, d, "stage.json")))


def load(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


# --------------------------------------------------------------------------

def check_tracks(verbose: bool) -> None:
    print("tracks")
    for tid in track_ids():
        meta = load(os.path.join(TRACKS, tid, "track.json"))
        payload = os.path.join(TRACKS, tid, "workspace")

        for field in REQUIRED_TRACK_FIELDS:
            check(field in meta and meta[field] not in (None, "", {}, []),
                  f"{tid}: track.json has '{field}'", verbose=verbose)

        check(meta.get("id") == tid, f"{tid}: track.json id matches directory",
              f"id={meta.get('id')!r}", verbose=verbose)

        modules = meta.get("you_will_build") or {}
        for num in ("01", "02", "03", "04"):
            check(num in modules, f"{tid}: you_will_build has module {num}", verbose=verbose)

        check(os.path.isdir(payload), f"{tid}: has a workspace payload", verbose=verbose)
        check(os.path.exists(os.path.join(payload, "README.md")),
              f"{tid}: payload has README.md", verbose=verbose)

        # every path the lab promises must actually be in the corpus
        referenced = {"first_input": meta.get("first_input")}
        for key, value in (meta.get("key_files") or {}).items():
            referenced[f"key_files.{key}"] = value
        for label, rel in referenced.items():
            if not rel:
                continue
            check(os.path.exists(os.path.join(payload, rel)),
                  f"{tid}: {label} exists in the corpus", rel, verbose=verbose)

        # the task must not be another track's task
        for other in track_ids():
            if other == tid:
                continue
            other_task = load(os.path.join(TRACKS, other, "track.json")).get("first_task")
            check(meta.get("first_task") != other_task,
                  f"{tid}: first_task is not {other}'s", verbose=verbose)


def check_stages(verbose: bool) -> None:
    print("stages")
    for sid in stage_ids():
        sdir = os.path.join(STAGES, sid)
        meta = load(os.path.join(sdir, "stage.json"))
        for field in ("id", "stage", "title", "commit"):
            check(field in meta, f"{sid}: stage.json has '{field}'", verbose=verbose)
        check(meta.get("id") == sid, f"{sid}: stage.json id matches directory",
              f"id={meta.get('id')!r}", verbose=verbose)
        if meta.get("settings"):
            path = os.path.join(sdir, meta["settings"])
            check(os.path.exists(path), f"{sid}: settings file exists", meta["settings"],
                  verbose=verbose)
            if os.path.exists(path):
                try:
                    load(path)
                    check(True, f"{sid}: settings is valid JSON", verbose=verbose)
                except ValueError as exc:
                    check(False, f"{sid}: settings is valid JSON", str(exc))
        for rel in meta.get("from_track", []):
            if rel == "{{ALL}}":
                continue
            for tid in track_ids():
                resolved = rel.replace("{{FIRST_INPUT}}",
                                       load(os.path.join(TRACKS, tid, "track.json"))
                                       .get("first_input", ""))
                check(os.path.exists(os.path.join(TRACKS, tid, "workspace", resolved)),
                      f"{sid}: from_track '{rel}' resolves for {tid}", resolved,
                      verbose=verbose)


def check_substitution(verbose: bool) -> None:
    """Apply every stage for every track and assert nothing is left unresolved."""
    print("substitution (applying every stage for every track)")
    for tid in track_ids():
        root = tempfile.mkdtemp(prefix=f"labtest-{tid}-")
        try:
            subprocess.run([sys.executable, os.path.join(SCRIPTS, "state.py"),
                            "--root", root, "init"],
                           capture_output=True, check=True)
            subprocess.run([sys.executable, os.path.join(SCRIPTS, "state.py"),
                            "--root", root, "set-track", tid],
                           capture_output=True, check=True)
            for sid in stage_ids():
                result = subprocess.run(
                    [sys.executable, os.path.join(SCRIPTS, "workspace.py"),
                     "--root", root, "stage", sid],
                    capture_output=True, text=True)
                check(result.returncode == 0, f"{tid}: stage {sid} applies",
                      result.stderr.strip()[:160], verbose=verbose)

            leaked = []
            for dirpath, dirs, names in os.walk(root):
                dirs[:] = [d for d in dirs if d != ".git"]
                for name in names:
                    if not name.endswith(TEXT_EXT):
                        continue
                    full = os.path.join(dirpath, name)
                    try:
                        text = open(full, encoding="utf-8").read()
                    except (OSError, UnicodeDecodeError):
                        continue
                    for token in set(re.findall(r"\{\{[A-Z_]+\}\}", text)):
                        leaked.append(f"{os.path.relpath(full, root)}:{token}")
            check(not leaked, f"{tid}: no unresolved placeholders in the workspace",
                  ", ".join(sorted(set(leaked))[:6]), verbose=verbose)

            # the handbook has to reach the participant's own folder: the client network
            # blocks external sites, so a link is not a delivery mechanism
            handbook = os.path.join(root, "handbook.html")
            check(os.path.exists(handbook), f"{tid}: handbook.html lands at the workspace root",
                  verbose=verbose)
            if os.path.exists(handbook):
                body = open(handbook, encoding="utf-8").read()
                check(body.lstrip().startswith("<!doctype html>"),
                      f"{tid}: the workspace handbook is a standalone document",
                      verbose=verbose)
                check("fonts.googleapis.com" in body
                      and body.count("http") == body.count("fonts.googleapis.com"),
                      f"{tid}: the handbook fetches nothing but the web font",
                      verbose=verbose)

            # the prompts each experiment needs must exist once its stage is applied
            exp_py = os.path.join(root, "experiments", "exp.py")
            check(os.path.exists(exp_py), f"{tid}: experiments/exp.py installed",
                  verbose=verbose)
            if os.path.exists(exp_py):
                wanted = set(re.findall(r'"prompt":\s*"([^"]+)"', open(exp_py).read()))
                for prompt in sorted(wanted):
                    path = os.path.join(root, "experiments", prompt)
                    check(os.path.exists(path),
                          f"{tid}: experiments/{prompt} exists after all stages",
                          verbose=verbose)
                    if os.path.exists(path):
                        check(open(path).read().strip() != "",
                              f"{tid}: experiments/{prompt} is not empty", verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_reference_skills(verbose: bool) -> None:
    print("reference skills (facilitator answer keys)")
    for tid in track_ids():
        meta = load(os.path.join(TRACKS, tid, "track.json"))
        name = meta.get("first_skill")
        path = os.path.join(TRACKS, tid, "reference", "skills", name, "SKILL.md")
        if not os.path.exists(path):
            warn(f"{tid}: no reference skill at reference/skills/{name}/SKILL.md "
                 f"— nothing to fall back on if a group gets stuck")
            continue
        text = open(path).read()
        front = text.split("---")[1] if text.startswith("---") else ""
        check(re.search(r"^name:\s*\S+", front, re.M) is not None,
              f"{tid}: reference skill has a name", verbose=verbose)
        desc = re.search(r"^description:\s*(.+)$", front, re.M)
        check(desc is not None, f"{tid}: reference skill has a description", verbose=verbose)
        if desc:
            check(len(desc.group(1)) >= 60,
                  f"{tid}: reference skill description says when to use it",
                  f"only {len(desc.group(1))} chars", verbose=verbose)
        check(re.search(r"^name:\s*" + re.escape(name), front, re.M) is not None,
              f"{tid}: reference skill name matches first_skill", verbose=verbose)

        # the answer key must pass the same gate the participants have to pass
        root = tempfile.mkdtemp(prefix=f"labskill-{tid}-")
        try:
            dst = os.path.join(root, ".claude", "skills", name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copytree(os.path.join(TRACKS, tid, "reference", "skills", name), dst)
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "check_skill.py"),
                 "--root", root, "--name", name, "--json"],
                capture_output=True, text=True)
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: reference skill passes check_skill.py",
                  "; ".join(payload.get("problems") or []), verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_shared_files_are_track_neutral(verbose: bool) -> None:
    """Stage payloads are shared. A track-specific literal in one is the bug we just fixed."""
    print("shared payloads are track-neutral")
    literals = []
    for tid in track_ids():
        meta = load(os.path.join(TRACKS, tid, "track.json"))
        literals.append((tid, meta.get("first_task", "").rstrip("."), meta.get("first_skill")))
    for dirpath, dirs, names in os.walk(STAGES):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in names:
            if not name.endswith(TEXT_EXT):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, PLUGIN_ROOT)
            try:
                text = open(full, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            for tid, task, skill in literals:
                if task and task in text:
                    check(False, f"{rel} contains {tid}'s task verbatim", task)
                if skill and re.search(rf"\b{re.escape(skill)}\b", text):
                    check(False, f"{rel} names {tid}'s skill verbatim", skill)
    check(True, "no track literals in stage payloads", verbose=verbose)


def check_reference_tools(verbose: bool) -> None:
    """The answer-key tools must pass the same gate participants have to pass."""
    print("reference tools")
    for tid in track_ids():
        meta = load(os.path.join(TRACKS, tid, "track.json"))
        name = meta.get("first_tool")
        check(bool(name), f"{tid}: track.json names a first_tool", verbose=verbose)
        if not name:
            continue
        src = os.path.join(TRACKS, tid, "reference", "tools", f"{name}.py")
        if not os.path.exists(src):
            warn(f"{tid}: no reference tool at reference/tools/{name}.py")
            continue
        scaffold = os.path.join(TRACKS, tid, "scaffolds", "tool.py")
        check(os.path.exists(scaffold), f"{tid}: has a tool scaffold", verbose=verbose)

        root = tempfile.mkdtemp(prefix=f"labtool-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            run("workspace.py", "stage", "m1s3-corpus")

            # the scaffold must NOT pass — otherwise the gate is not gating
            run("workspace.py", "stage", "m1s5-tool")
            result = run("check_tool.py", "--json")
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched scaffold fails check_tool.py", verbose=verbose)

            # the reference must pass
            shutil.copy2(src, os.path.join(root, "tools", f"{name}.py"))
            result = run("check_tool.py", "--json")
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: reference tool passes check_tool.py",
                  "; ".join(payload.get("problems") or []), verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_reference_hooks(verbose: bool) -> None:
    """The answer-key hook must pass the same behavioural gate participants must pass."""
    print("reference hooks")
    for tid in track_ids():
        src = os.path.join(TRACKS, tid, "reference", "hooks", "write_boundary.py")
        if not os.path.exists(src):
            warn(f"{tid}: no reference hook at reference/hooks/write_boundary.py")
            continue
        check(os.path.exists(os.path.join(TRACKS, tid, "scaffolds", "hook.py")),
              f"{tid}: has a hook scaffold", verbose=verbose)

        root = tempfile.mkdtemp(prefix=f"labhook-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            run("workspace.py", "stage", "m1s1-harness")
            run("workspace.py", "stage", "m1s6-hook")

            # the untouched scaffold must fail, or the gate is not gating
            result = run("check_hook.py", "--json")
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched hook scaffold fails check_hook.py", verbose=verbose)

            # the reference, once registered, must pass
            shutil.copy2(src, os.path.join(root, ".claude", "hooks", "write_boundary.py"))
            settings_path = os.path.join(root, ".claude", "settings.json")
            with open(settings_path) as fh:
                settings = json.load(fh)
            settings["hooks"]["PreToolUse"].append({
                "matcher": "Write|Edit|MultiEdit|NotebookEdit",
                "hooks": [{"type": "command",
                           "command": 'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/write_boundary.py"'}],
            })
            with open(settings_path, "w") as fh:
                json.dump(settings, fh, indent=2)
            result = run("check_hook.py", "--json")
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: reference hook passes check_hook.py",
                  "; ".join(payload.get("problems") or []), verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_reference_plugins(verbose: bool) -> None:
    """The assembled answer-key plugin must be portable and pass its own gate."""
    print("reference plugins")
    for tid in track_ids():
        meta = load(os.path.join(TRACKS, tid, "track.json"))
        name = meta.get("system_name")
        check(bool(name), f"{tid}: track.json names a system_name", verbose=verbose)
        plug = os.path.join(TRACKS, tid, "reference", "plugin")
        if not os.path.isdir(plug):
            warn(f"{tid}: no reference plugin at reference/plugin")
            continue

        for rel in (".claude-plugin/plugin.json",
                    f"skills/{meta.get('first_skill')}/SKILL.md",
                    f"tools/{meta.get('first_tool')}.py",
                    "hooks/hooks.json", "hooks/write_boundary.py"):
            check(os.path.exists(os.path.join(plug, rel)),
                  f"{tid}: reference plugin has {rel}", verbose=verbose)

        hooks = os.path.join(plug, "hooks", "hooks.json")
        if os.path.exists(hooks):
            text = open(hooks).read()
            check("CLAUDE_PROJECT_DIR" not in text,
                  f"{tid}: plugin hooks.json does not use the project path", verbose=verbose)
            check("CLAUDE_PLUGIN_ROOT" in text,
                  f"{tid}: plugin hooks.json uses CLAUDE_PLUGIN_ROOT", verbose=verbose)

        skill = os.path.join(plug, "skills", meta.get("first_skill") or "", "SKILL.md")
        tool = meta.get("first_tool")
        if os.path.exists(skill) and tool:
            body = open(skill).read()
            check(f"tools/{tool}.py" not in body or "CLAUDE_PLUGIN_ROOT" in body,
                  f"{tid}: plugin skill calls its tool portably", verbose=verbose)

        for name_ in ("CLAUDE.md", "intent.md"):
            path = os.path.join(TRACKS, tid, "reference", "project", name_)
            check(os.path.exists(path), f"{tid}: reference {name_} exists", verbose=verbose)
            if os.path.exists(path):
                check("TODO" not in open(path).read(),
                      f"{tid}: reference {name_} has no TODOs left", verbose=verbose)

        # intent must be structured as the playbook describes, and must be imported
        intent = os.path.join(TRACKS, tid, "reference", "project", "intent.md")
        if os.path.exists(intent):
            body = open(intent).read()
            for section in ("Problem", "Proposed outcome", "Affected users and systems",
                            "Constraints", "Open questions"):
                check(re.search(rf"^##\s*{re.escape(section)}\s*$", body, re.M) is not None,
                      f"{tid}: reference intent has '## {section}'", verbose=verbose)
            check(len(body.splitlines()) <= 60,
                  f"{tid}: reference intent is short enough to import",
                  f"{len(body.splitlines())} lines", verbose=verbose)
        claude_md = os.path.join(TRACKS, tid, "reference", "project", "CLAUDE.md")
        if os.path.exists(claude_md):
            check(re.search(r"^\s*@intent\.md\s*$", open(claude_md).read(), re.M) is not None,
                  f"{tid}: reference CLAUDE.md imports intent.md", verbose=verbose)

        # the scaffold must fail the intent gate, and the reference must pass it
        root2 = tempfile.mkdtemp(prefix=f"labintent-{tid}-")
        try:
            run2 = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root2, *a],
                capture_output=True, text=True)
            run2("state.py", "init")
            run2("state.py", "set-track", tid)
            run2("workspace.py", "stage", "m1s3-corpus")
            result = json.loads(run2("check_intent.py", "--json").stdout or "{}")
            check(result.get("ok") is False,
                  f"{tid}: the untouched intent scaffold fails check_intent.py",
                  verbose=verbose)
            shutil.copy2(intent, os.path.join(root2, "intent.md"))
            result = json.loads(run2("check_intent.py", "--json").stdout or "{}")
            check(result.get("ok") is True,
                  f"{tid}: reference intent passes check_intent.py",
                  "; ".join(result.get("problems") or []), verbose=verbose)
        finally:
            shutil.rmtree(root2, ignore_errors=True)

        # full end-to-end: stage, restore the answer key, install the plugin, run the gate
        root = tempfile.mkdtemp(prefix=f"labplug-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            run("workspace.py", "stage", "m1s1-harness")
            run("workspace.py", "stage", "m1s3-corpus")
            run("workspace.py", "stage", "m1s7-plugin")
            run("workspace.py", "catchup", "--with-reference")
            # A catchup that restores the hook FILE but not its registration hands back a
            # workspace that looks repaired and is not: an unregistered hook never runs.
            with open(os.path.join(root, ".claude", "settings.json")) as fh:
                registered = json.load(fh)
            check("write_boundary" in json.dumps(registered),
                  f"{tid}: catchup registers the reference hook, not just the file",
                  verbose=verbose)
            gate = run("check_hook.py", "--json")
            payload = json.loads(gate.stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the restored hook passes check_hook.py",
                  "; ".join(payload.get("problems") or [])[:200], verbose=verbose)
            shutil.rmtree(os.path.join(root, name), ignore_errors=True)
            shutil.copytree(plug, os.path.join(root, name))
            result = run("check_plugin.py", "--json")
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: reference plugin passes check_plugin.py",
                  "; ".join(payload.get("problems") or []), verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_tutor_facing_text(verbose: bool) -> None:
    """modules/ and references/ are read by the tutor, never substituted.

    A {{PLACEHOLDER}} in one of them renders literally in front of a participant, so it is
    a different rule from the stage payloads: there must be none at all.
    """
    print("tutor-facing text has no placeholders")
    for base in ("modules", "references"):
        directory = os.path.join(PLUGIN_ROOT, base)
        if not os.path.isdir(directory):
            continue
        for dirpath, _dirs, names in os.walk(directory):
            for name in names:
                if not name.endswith(".md"):
                    continue
                full = os.path.join(dirpath, name)
                rel = os.path.relpath(full, PLUGIN_ROOT)
                found = sorted(set(re.findall(r"\{\{[A-Z_]+\}\}",
                                              open(full, encoding="utf-8").read())))
                check(not found, f"{rel} has no unsubstituted placeholders",
                      ", ".join(found), verbose=verbose)


def check_corpora(verbose: bool) -> None:
    """Each track's corpus must be internally consistent, and say so in its own checker.

    Hand-written corpora contradict themselves. Every track carries a fact sheet naming the
    single owner of each fact and a checker that enforces the overlaps, and both run here so
    a corpus edit cannot quietly break a golden answer.
    """
    print("corpora are self-consistent")
    for tid in track_ids():
        design = os.path.join(TRACKS, tid, "corpus-design")
        facts = os.path.join(design, "FACTS.md")
        checker = os.path.join(design, "check_consistency.py")
        check(os.path.exists(facts), f"{tid}: has a corpus fact sheet", verbose=verbose)
        check(os.path.exists(checker), f"{tid}: has a consistency checker", verbose=verbose)
        if not os.path.exists(checker):
            continue
        result = subprocess.run([sys.executable, checker], capture_output=True, text=True)
        failures = [l.strip() for l in result.stdout.splitlines() if l.strip().startswith("x ")]
        check(result.returncode == 0, f"{tid}: corpus is self-consistent",
              "; ".join(failures)[:220], verbose=verbose)


def check_golden_sets(verbose: bool) -> None:
    """The golden set is what Module 2 scores against; an unscoreable query is invisible."""
    print("golden retrieval sets")
    for tid in track_ids():
        golden = os.path.join(TRACKS, tid, "scaffolds", "golden.jsonl")
        check(os.path.exists(golden), f"{tid}: has a golden retrieval set", verbose=verbose)
        if not os.path.exists(golden):
            continue
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, "check_golden.py"),
             "--file", golden, "--corpus", os.path.join(TRACKS, tid, "workspace"), "--json"],
            capture_output=True, text=True)
        payload = json.loads(result.stdout or "{}")
        check(payload.get("ok") is True, f"{tid}: golden set is scoreable",
              "; ".join(payload.get("problems") or [])[:220], verbose=verbose)
        tiers = payload.get("tiers") or {}
        check(tiers.get("unreachable") == 3,
              f"{tid}: three unreachable queries for Module 3",
              str(tiers), verbose=verbose)
        check(payload.get("queries", 0) >= 15,
              f"{tid}: fifteen shipped queries", str(payload.get("queries")),
              verbose=verbose)


# What the lexical baseline answers on the shipped corpus, per track. These exact numbers are
# quoted in lab/facilitator/module-2-measured.md, lab/reference/handbook.html and
# docs/CURRICULUM.md, and Module 2 opens by running this retriever in front of the room. A
# corpus edit that moves them has to move the documents too, so this is an equality check on
# purpose rather than a floor.
BASELINE_ANSWERED = {"support-triage": 11, "vendor-qa": 12, "docgen": 8}
# tokens per answer, the figure the scoreboard prints and the handbook quotes
BASELINE_COST = {"support-triage": 2303, "vendor-qa": 2013, "docgen": 2409}


def check_baseline_floor(verbose: bool) -> None:
    """Module 2 step 2.1 is a measurement taken live. It cannot be allowed to drift."""
    print("Module 2 lexical baseline")
    for tid in track_ids():
        expected = BASELINE_ANSWERED.get(tid)
        if expected is None:
            check(False, f"{tid}: has a recorded baseline score", verbose=verbose)
            continue
        root = tempfile.mkdtemp(prefix=f"labbase-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            run("workspace.py", "stage", "m1s3-corpus")
            staged = json.loads(run("workspace.py", "stage", "m2s1-baseline").stdout or "{}")
            written = staged.get("written") or []
            check("rag/baseline_retrieve.py" in written,
                  f"{tid}: stage m2s1-baseline installs the baseline retriever",
                  str(written), verbose=verbose)
            check("evals/retrieval/golden.jsonl" in written,
                  f"{tid}: stage m2s1-baseline installs the golden set",
                  str(written), verbose=verbose)
            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "eval_retrieval.py"),
                 "--retriever", "rag/baseline_retrieve.py",
                 "--label", "lexical baseline", "--json"],
                capture_output=True, text=True, cwd=root)
            payload = json.loads(result.stdout or "{}")
            head = payload.get("headline") or {}
            answered = head.get("answered")
            check(answered == expected,
                  f"{tid}: baseline answers {expected}/12 as documented",
                  f"scored {answered}; if this is a real corpus change, update "
                  f"BASELINE_ANSWERED, module-2-measured.md, handbook.html and CURRICULUM.md",
                  verbose=verbose)
            check((head.get("mean_tokens") or 0) > 1000,
                  f"{tid}: baseline is expensive enough to make the point",
                  str(head.get("mean_tokens")), verbose=verbose)
            check(head.get("tokens_per_answer") == BASELINE_COST.get(tid),
                  f"{tid}: baseline costs {BASELINE_COST.get(tid):,} tokens per answer",
                  f"scored {head.get('tokens_per_answer')}", verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_module2_artifacts(verbose: bool) -> None:
    """Module 2's scaffolds must fail their gates and its answer keys must pass them.

    Same discipline as the intent gate: a gate that passes an untouched scaffold teaches a
    participant that the work was optional, and one that fails the reference solution makes
    the facilitator's answer key useless.
    """
    print("Module 2 scaffolds, answer keys and gates")
    stages = ("m1s3-corpus", "m2s1-baseline", "m2s2-vectors", "m2s3-mcp", "m2s4-agentic")
    for tid in track_ids():
        root = tempfile.mkdtemp(prefix=f"labm2-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            for stage_id in stages:
                result = run("workspace.py", "stage", stage_id)
                check(result.returncode == 0, f"{tid}: stage {stage_id} applies",
                      result.stderr.strip()[:200], verbose=verbose)

            for rel in ("rag/chunkers.py", "rag/ingest.py", "rag/retrieve.py",
                        "rag/baseline_retrieve.py", "mcp/retrieval_server.py",
                        ".mcp.json", ".claude/skills/retrieve-and-answer/SKILL.md",
                        "evals/retrieval/golden.jsonl"):
                check(os.path.exists(os.path.join(root, rel)),
                      f"{tid}: Module 2 installs {rel}", verbose=verbose)

            # the scaffolds must not pass
            payload = json.loads(run("check_ingest.py", "--json").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched rag scaffolds fail check_ingest.py",
                  verbose=verbose)
            payload = json.loads(run("check_retrieval_tool.py", "--json").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched MCP scaffold fails check_retrieval_tool.py",
                  verbose=verbose)
            check(payload.get("tools") == [],
                  f"{tid}: the MCP scaffold offers no tools until it is written",
                  str(payload.get("tools")), verbose=verbose)
            payload = json.loads(run("check_skill.py", "--json",
                                     "--name", "retrieve-and-answer").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched agentic skill fails check_skill.py",
                  verbose=verbose)

            # the answer keys must pass
            for src, dest in (("reference/rag/chunkers.py", "rag/chunkers.py"),
                              ("reference/rag/ingest.py", "rag/ingest.py"),
                              ("reference/rag/retrieve.py", "rag/retrieve.py"),
                              ("reference/mcp/retrieval_server.py",
                               "mcp/retrieval_server.py")):
                shutil.copy2(os.path.join(PLUGIN_ROOT, src), os.path.join(root, dest))
            payload = json.loads(run("check_ingest.py", "--json").stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the reference chunkers pass check_ingest.py",
                  "; ".join(payload.get("problems") or [])[:220], verbose=verbose)
            for strategy in ("naive", "structural", "parent_child"):
                check((payload.get("chunks") or {}).get(strategy, 0) > 0,
                      f"{tid}: reference {strategy} produces chunks",
                      str(payload.get("chunks")), verbose=verbose)

            # the MCP answer key: protocol level only. tools/call needs an ingested corpus
            # and an embedding model, which does not belong in a selftest.
            payload = json.loads(run("check_retrieval_tool.py", "--json").stdout or "{}")
            offered = payload.get("tools") or []
            for name in ("search_corpus", "search_corpus_filtered", "get_document"):
                check(name in offered,
                      f"{tid}: the reference MCP server offers {name}",
                      str(offered), verbose=verbose)
            design = [p for p in (payload.get("problems") or [])
                      if "leaking" in p or "description is too thin" in p
                      or "inputSchema" in p or "superseded" in p]
            check(not design,
                  f"{tid}: the reference MCP server has no tool-surface problems",
                  "; ".join(design)[:220], verbose=verbose)

            ref_skill = os.path.join(PLUGIN_ROOT, "reference", "skills",
                                     "retrieve-and-answer", "SKILL.md")
            meta_path = os.path.join(TRACKS, tid, "track.json")
            with open(meta_path) as fh:
                output_dir = (json.load(fh) or {}).get("output_dir", "")
            with open(ref_skill) as fh:
                body = fh.read().replace("{{OUTPUT_DIR}}", output_dir)
            dest = os.path.join(root, ".claude", "skills", "retrieve-and-answer",
                                "SKILL.md")
            with open(dest, "w") as fh:
                fh.write(body)
            payload = json.loads(run("check_skill.py", "--json",
                                     "--name", "retrieve-and-answer").stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the reference agentic skill passes check_skill.py",
                  "; ".join(payload.get("problems") or [])[:220], verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_stage_ids_exist(verbose: bool) -> None:
    """A module file naming a stage that does not exist strands the step at runtime."""
    print("stage ids named in module files")
    known = {d for d in os.listdir(os.path.join(PLUGIN_ROOT, "stages"))
             if os.path.isdir(os.path.join(PLUGIN_ROOT, "stages", d))}
    pattern = re.compile(r"\b(m\dfs?\d[a-z0-9-]*|m\ds\d[a-z0-9-]*)\b")
    for area in ("modules", "skills", "facilitator", "references"):
        base = os.path.join(PLUGIN_ROOT, area)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, names in os.walk(base):
            for name in names:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                for match in sorted(set(pattern.findall(text))):
                    check(match in known,
                          f"{os.path.relpath(path, PLUGIN_ROOT)}: stage '{match}' exists",
                          f"known: {', '.join(sorted(known))}", verbose=verbose)


def check_documented_invocations(verbose: bool) -> None:
    """Commands printed for participants have to be the commands that actually work.

    `check_golden.py --corpus data` was written in the module file and reported three
    perfectly good shipped queries as broken, because `expected` paths in the golden set are
    project-relative. A wrong flag in a code block is indistinguishable from a broken lab.
    """
    print("documented command invocations")
    bad = []
    for area in ("modules", "references", "facilitator", "skills", "stages"):
        base = os.path.join(PLUGIN_ROOT, area)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, names in os.walk(base):
            for name in names:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                for line in text.splitlines():
                    if "check_golden.py" in line and "--corpus" in line \
                            and "--corpus ." not in line:
                        bad.append(f"{os.path.relpath(path, PLUGIN_ROOT)}: {line.strip()}")
                    if "eval_retrieval.py" in line and "--retriever" not in line \
                            and "scripts/eval_retrieval.py" in line and "--" in line:
                        bad.append(f"{os.path.relpath(path, PLUGIN_ROOT)}: "
                                   f"eval_retrieval.py without --retriever: {line.strip()}")
    check(not bad, "documented gate invocations use the right flags",
          "; ".join(bad)[:300], verbose=verbose)


def check_graph_questions(verbose: bool) -> None:
    """Module 3's ontology template hands each participant their own three broken questions.

    Runs for EVERY track, unlike the reference-graph checks — the first version of this
    lived inside those and was skipped for the two tracks that have no graph builder yet,
    so a mutated question passed the suite.
    """
    print("Module 3 graph questions match Module 2's unanswered tier")
    for tid in track_ids():
        with open(os.path.join(TRACKS, tid, "track.json")) as fh:
            questions = (json.load(fh) or {}).get("graph_questions") or {}
        check(set(questions) == {"multi_hop", "aggregation", "temporal"},
              f"{tid}: track.json declares the three graph questions",
              str(sorted(questions)), verbose=verbose)
        unreachable = []
        with open(os.path.join(TRACKS, tid, "scaffolds", "golden.jsonl")) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    row = json.loads(line)
                    if row.get("tier") == "unreachable":
                        unreachable.append(row["q"])
        for shape, text in sorted(questions.items()):
            check(text in unreachable,
                  f"{tid}: the {shape} question is one Module 2 leaves unanswered",
                  f"{text!r} is not in the unreachable tier", verbose=verbose)


def check_reference_graphs(verbose: bool) -> None:
    """The verified graph must still describe the corpus it was built from.

    It is an answer key participants compare their own extraction against, so a corpus edit
    that leaves it stale does not break loudly — it just marks correct work as wrong.
    """
    print("reference graphs match their corpora")
    for tid in track_ids():
        builder = os.path.join(TRACKS, tid, "corpus-design", "build_reference_graph.py")
        if not os.path.exists(builder):
            continue                      # not every track has one yet
        result = subprocess.run([sys.executable, builder, "--check"],
                                capture_output=True, text=True)
        check(result.returncode == 0,
              f"{tid}: committed reference graph is current",
              (result.stderr or result.stdout).strip()[:200], verbose=verbose)

        graph_dir = os.path.join(TRACKS, tid, "reference", "graph")
        onto_dir = os.path.join(TRACKS, tid, "reference", "ontology")
        for rel in ("nodes.jsonl", "edges.jsonl"):
            check(os.path.exists(os.path.join(graph_dir, rel)),
                  f"{tid}: reference graph has {rel}", verbose=verbose)
        ontologies = [f for f in os.listdir(onto_dir)
                      if f.endswith((".yaml", ".yml"))] if os.path.isdir(onto_dir) else []
        check(len(ontologies) == 1,
              f"{tid}: exactly one reference ontology", str(ontologies), verbose=verbose)
        if not ontologies:
            continue
        try:
            import yaml                                       # noqa: PLC0415
        except ImportError:
            check(True, f"{tid}: ontology not parsed (no pyyaml here)", verbose=verbose)
            continue
        with open(os.path.join(onto_dir, ontologies[0])) as fh:
            onto = yaml.safe_load(fh) or {}
        types = onto.get("types") or {}
        relations = onto.get("relations") or []
        cqs = onto.get("competency_questions") or []
        # The module tells participants 6-10 types and 8-12 relations. The answer key has
        # to sit inside the range it asks for.
        check(6 <= len(types) <= 10,
              f"{tid}: ontology declares 6-10 types", str(len(types)), verbose=verbose)
        check(8 <= len(relations) <= 12,
              f"{tid}: ontology declares 8-12 relations", str(len(relations)),
              verbose=verbose)
        check(len(cqs) == 3,
              f"{tid}: one competency question per unreachable query", str(len(cqs)),
              verbose=verbose)
        shapes = {c.get("shape") for c in cqs}
        check(shapes == {"multi-hop", "aggregation", "temporal"},
              f"{tid}: the three CQs cover the three failure shapes", str(shapes),
              verbose=verbose)
        # every relation the ontology declares must actually be used by the answer key
        rels_used = set()
        with open(os.path.join(graph_dir, "edges.jsonl")) as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    rels_used.add(json.loads(line).get("rel"))
        declared = {r["name"] for r in relations}
        check(declared == rels_used,
              f"{tid}: every declared relation appears in the verified graph",
              f"declared not used: {sorted(declared - rels_used)}; "
              f"used not declared: {sorted(rels_used - declared)}", verbose=verbose)


def check_graph_answers(verbose: bool) -> None:
    """Every verified graph must answer its own eval set exactly, on every track.

    This is the claim Module 3 rests on and the number the facilitator notes quote, so it is
    pinned rather than trusted. Cheap to run: SQLite and a few hundred edges, no embeddings.
    """
    print("verified graphs answer their eval sets")
    for tid in track_ids():
        onto_dir = os.path.join(TRACKS, tid, "reference", "ontology")
        graph_dir = os.path.join(TRACKS, tid, "reference", "graph")
        queries = os.path.join(TRACKS, tid, "scaffolds", "graph-queries.jsonl")
        if not (os.path.isdir(graph_dir) and os.path.exists(queries)):
            continue
        root = tempfile.mkdtemp(prefix=f"labkg-{tid}-")
        try:
            for sub in ("ontology", "graph", "kg", "evals/graph"):
                os.makedirs(os.path.join(root, sub), exist_ok=True)
            for name in os.listdir(onto_dir):
                shutil.copy2(os.path.join(onto_dir, name),
                             os.path.join(root, "ontology", name))
            for name in ("nodes.jsonl", "edges.jsonl"):
                shutil.copy2(os.path.join(graph_dir, name),
                             os.path.join(root, "graph", name))
            for name in ("compile.py", "kg.py"):
                shutil.copy2(os.path.join(PLUGIN_ROOT, "reference", "kg", name),
                             os.path.join(root, "kg", name))
            shutil.copy2(queries, os.path.join(root, "evals", "graph", "queries.jsonl"))

            result = subprocess.run(
                [sys.executable, os.path.join(root, "kg", "compile.py"),
                 "--root", root, "--json"], capture_output=True, text=True, cwd=root)
            payload = json.loads(result.stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the verified graph compiles against its own ontology",
                  "; ".join((payload.get("errors") or []))[:220], verbose=verbose)
            check(not payload.get("warnings"),
                  f"{tid}: the verified graph compiles with no warnings",
                  "; ".join((payload.get("warnings") or []))[:220], verbose=verbose)
            if not payload.get("ok"):
                continue

            result = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, "eval_graph.py"),
                 "--root", root, "--json", "--no-record"],
                capture_output=True, text=True)
            scored = json.loads(result.stdout or "{}")
            head = scored.get("headline") or {}
            check(head.get("queries", 0) >= 8,
                  f"{tid}: at least eight graph questions", str(head.get("queries")),
                  verbose=verbose)
            check(head.get("exact") == head.get("queries"),
                  f"{tid}: the verified graph answers every question exactly",
                  "; ".join(f"{r['id']} missing {r['missing']} extra {r['extra']}"
                            for r in scored.get("queries", []) if not r["exact"])[:250],
                  verbose=verbose)
            check(head.get("precision") == 1.0 and head.get("recall") == 1.0,
                  f"{tid}: precision and recall are both 1.0",
                  f"precision {head.get('precision')}, recall {head.get('recall')}",
                  verbose=verbose)
            shapes = (scored.get("by_shape") or {})
            check(set(shapes) == {"multi-hop", "aggregation", "temporal"},
                  f"{tid}: the eval set covers all three question shapes",
                  str(sorted(shapes)), verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_module3_artifacts(verbose: bool) -> None:
    """Module 3's scaffolds must fail their gates; its answer keys must pass them."""
    print("Module 3 scaffolds, answer keys and gates")
    stages = ("m1s3-corpus", "m2s1-baseline", "m2s2-vectors", "m2s3-mcp",
              "m3s1-ontology", "m3s2-extract", "m3s3-kg-tool", "m3s4-hybrid")
    for tid in track_ids():
        root = tempfile.mkdtemp(prefix=f"labm3-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            for stage_id in stages:
                result = run("workspace.py", "stage", stage_id)
                check(result.returncode == 0, f"{tid}: stage {stage_id} applies",
                      result.stderr.strip()[:200], verbose=verbose)

            for rel in ("ontology/ontology.yaml", "kg/compile.py", "kg/kg.py",
                        "mcp/kg_server.py", "evals/graph/queries.jsonl",
                        ".claude/skills/extract-graph/SKILL.md",
                        ".claude/skills/answer-with-graph/SKILL.md"):
                check(os.path.exists(os.path.join(root, rel)),
                      f"{tid}: Module 3 installs {rel}", verbose=verbose)

            # the participant's own three questions reach the template
            with open(os.path.join(root, "ontology", "ontology.yaml")) as fh:
                template = fh.read()
            with open(os.path.join(TRACKS, tid, "track.json")) as fh:
                questions = (json.load(fh) or {}).get("graph_questions") or {}
            for shape, text in sorted(questions.items()):
                check(text in template,
                      f"{tid}: the ontology template carries the {shape} question",
                      verbose=verbose)

            # scaffolds must not pass
            payload = json.loads(run("check_ontology.py", "--json").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched ontology template fails check_ontology.py",
                  verbose=verbose)
            payload = json.loads(run("check_graph.py", "--json").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: a workspace with no graph fails check_graph.py",
                  verbose=verbose)
            payload = json.loads(run("check_kg_tool.py", "--json").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched graph server fails check_kg_tool.py",
                  verbose=verbose)
            check(payload.get("tools") == [],
                  f"{tid}: the graph server offers no tools until it is written",
                  str(payload.get("tools")), verbose=verbose)

            # answer keys must pass
            onto_dir = os.path.join(TRACKS, tid, "reference", "ontology")
            for name in os.listdir(onto_dir):
                shutil.copy2(os.path.join(onto_dir, name),
                             os.path.join(root, "ontology", name))
            os.remove(os.path.join(root, "ontology", "ontology.yaml"))
            payload = json.loads(run("check_ontology.py", "--json").stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the reference ontology passes check_ontology.py",
                  "; ".join(payload.get("problems") or [])[:220], verbose=verbose)

            graph_dir = os.path.join(TRACKS, tid, "reference", "graph")
            os.makedirs(os.path.join(root, "graph"), exist_ok=True)
            for name in ("nodes.jsonl", "edges.jsonl"):
                shutil.copy2(os.path.join(graph_dir, name),
                             os.path.join(root, "graph", name))
            payload = json.loads(run("check_graph.py", "--json").stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the verified graph passes check_graph.py",
                  "; ".join(payload.get("problems") or [])[:250], verbose=verbose)

            shutil.copy2(os.path.join(PLUGIN_ROOT, "reference", "mcp", "kg_server.py"),
                         os.path.join(root, "mcp", "kg_server.py"))
            with open(os.path.join(root, ".mcp.json"), "w") as fh:
                json.dump({"mcpServers": {
                    "corpus-retrieval": {"command": "python3",
                                         "args": ["mcp/retrieval_server.py"]},
                    "knowledge-graph": {"command": "python3",
                                        "args": ["mcp/kg_server.py"]}}}, fh)
            payload = json.loads(run("check_kg_tool.py", "--json").stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the reference graph server passes check_kg_tool.py",
                  "; ".join(payload.get("problems") or [])[:220], verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_catchup_restores_module3(verbose: bool) -> None:
    """Module 3 tells a facilitator who is out of time to hand over the verified graph with
    `/lab:catchup --with-reference`. That instruction has to actually produce a graph that
    scores, or the fallback the module promises does not exist.
    """
    print("catchup restores a working Module 3")
    stages = ("m1s3-corpus", "m2s1-baseline", "m2s2-vectors", "m2s3-mcp", "m2s4-agentic",
              "m3s1-ontology", "m3s2-extract", "m3s3-kg-tool", "m3s4-hybrid")
    for tid in track_ids():
        root = tempfile.mkdtemp(prefix=f"labcu-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            for stage_id in stages:
                run("workspace.py", "stage", stage_id)
            result = run("workspace.py", "catchup", "--with-reference")
            payload = json.loads(result.stdout or "{}")
            restored = payload.get("reference_later") or []
            for expected in ("graph/nodes.jsonl", "graph/edges.jsonl",
                             "mcp/kg_server.py",
                             ".claude/skills/answer-with-graph/SKILL.md",
                             ".claude/skills/extract-graph/SKILL.md"):
                check(expected in restored,
                      f"{tid}: catchup restores {expected}", str(restored)[:200],
                      verbose=verbose)
            check(any(r.startswith("ontology/") for r in restored),
                  f"{tid}: catchup restores the reference ontology", str(restored)[:200],
                  verbose=verbose)
            # the unfinished template must go, or the compiler may pick it instead
            check(not os.path.exists(os.path.join(root, "ontology", "ontology.yaml")),
                  f"{tid}: catchup removes the unfinished ontology template",
                  verbose=verbose)

            payload = json.loads(run("check_graph.py", "--json").stdout or "{}")
            check(payload.get("ok") is True,
                  f"{tid}: the restored graph passes check_graph.py straight away",
                  "; ".join(payload.get("problems") or [])[:250], verbose=verbose)
            score = payload.get("score") or {}
            check(score.get("exact") == score.get("queries") and score.get("queries"),
                  f"{tid}: the restored graph answers every question",
                  str(score), verbose=verbose)
            for name in ("retrieve-and-answer", "answer-with-graph", "extract-graph"):
                gate = json.loads(run("check_skill.py", "--json",
                                      "--name", name).stdout or "{}")
                check(gate.get("ok") is True,
                      f"{tid}: the restored {name} skill passes check_skill.py",
                      "; ".join(gate.get("problems") or [])[:200], verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)


def check_module4_artifacts(verbose: bool) -> None:
    """Module 4's gate is a security control, so it is tested as one: it must refuse.

    The scaffold must fail closed (deny until implemented), the reference must allow only an
    approved, unmodified, unused approval, and the apply tool must refuse independently of
    the hook.
    """
    print("Module 4 scaffolds, the gate, and the full suite")
    stages = ("m1s3-corpus", "m4s1-spec", "m4s2-propose", "m4s3-gate", "m4s4-runbook")
    hook_event = json.dumps({"tool_name": "Bash",
                             "tool_input": {"command": "python3 tools/apply.py CASE-X"}})
    for tid in track_ids():
        root = tempfile.mkdtemp(prefix=f"labm4-{tid}-")
        try:
            run = lambda script, *a: subprocess.run(
                [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
                capture_output=True, text=True)
            run("state.py", "init")
            run("state.py", "set-track", tid)
            for stage_id in stages:
                result = run("workspace.py", "stage", stage_id)
                check(result.returncode == 0, f"{tid}: stage {stage_id} applies",
                      result.stderr.strip()[:200], verbose=verbose)
            for rel in ("spec/capability.md", "spec/capability.json", "RUNBOOK.md",
                        "proposals/README.md", "gate/approve.py", "tools/apply.py",
                        ".claude/hooks/approval_gate.py",
                        ".claude/skills/propose/SKILL.md"):
                check(os.path.exists(os.path.join(root, rel)),
                      f"{tid}: Module 4 installs {rel}", verbose=verbose)

            # the scaffolds must not pass
            payload = json.loads(run("check_spec.py", "--json").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched spec fails check_spec.py", verbose=verbose)
            payload = json.loads(run("check_skill.py", "--json",
                                     "--name", "propose").stdout or "{}")
            check(payload.get("ok") is False,
                  f"{tid}: the untouched propose skill fails check_skill.py",
                  verbose=verbose)

            # the gate scaffold must FAIL CLOSED — a security control that defaults to
            # allowing is worse than none, because it reads as protection
            hook = subprocess.run(
                [sys.executable, os.path.join(root, ".claude", "hooks",
                                              "approval_gate.py")],
                input=hook_event, capture_output=True, text=True,
                env={**os.environ, "CLAUDE_PROJECT_DIR": root})
            check("deny" in (hook.stdout or ""),
                  f"{tid}: the gate scaffold denies until it is implemented",
                  (hook.stdout or hook.stderr)[:160], verbose=verbose)
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # --- the reference gate, exercised as a control on one track
    root = tempfile.mkdtemp(prefix="labm4gate-")
    try:
        for sub in ("proposals", "approvals", "spec", "gate", "tools",
                    ".claude/hooks", "triage"):
            os.makedirs(os.path.join(root, sub), exist_ok=True)
        shutil.copy2(os.path.join(PLUGIN_ROOT, "reference", "gate", "approval_gate.py"),
                     os.path.join(root, ".claude", "hooks", "approval_gate.py"))
        shutil.copy2(os.path.join(PLUGIN_ROOT, "reference", "gate", "approve.py"),
                     os.path.join(root, "gate", "approve.py"))
        shutil.copy2(os.path.join(PLUGIN_ROOT, "reference", "tools", "apply.py"),
                     os.path.join(root, "tools", "apply.py"))
        with open(os.path.join(root, "spec", "capability.json"), "w") as fh:
            json.dump({"capability": "triage", "published_to": "triage"}, fh)
        body = os.path.join(root, "proposals", "P1.md")
        with open(body, "w") as fh:
            fh.write("# Proposal P1\n\nEvidence in data/knowledge/x.md.\n")
        with open(os.path.join(root, "proposals", "P1.json"), "w") as fh:
            json.dump({"id": "P1", "body": "proposals/P1.md", "confidence": "high",
                       "risk": "low", "rollback": "delete it", "unresolved": [],
                       "evidence": [{"via": "graph", "source": "data"}],
                       "actions": [{"type": "write", "path": "triage/P1.md",
                                    "from": "proposals/P1.md"}]}, fh)

        def gate() -> str:
            proc = subprocess.run(
                [sys.executable, os.path.join(root, ".claude", "hooks",
                                              "approval_gate.py")],
                input=json.dumps({"tool_name": "Bash",
                                  "tool_input": {"command": "python3 tools/apply.py P1"}}),
                capture_output=True, text=True,
                env={**os.environ, "CLAUDE_PROJECT_DIR": root})
            return proc.stdout or ""

        def approve() -> None:
            subprocess.run([sys.executable, os.path.join(root, "gate", "approve.py"),
                            "P1", "--root", root, "--by", "tester"],
                           capture_output=True, text=True)

        def apply_it():
            return subprocess.run([sys.executable, os.path.join(root, "tools", "apply.py"),
                                   "P1", "--root", root], capture_output=True, text=True)

        check("deny" in gate(), "reference gate: refuses an unapproved apply",
              verbose=verbose)
        hand = subprocess.run(
            [sys.executable, os.path.join(root, ".claude", "hooks", "approval_gate.py")],
            input=json.dumps({"tool_name": "Write",
                              "tool_input": {"file_path": "triage/P1.md"}}),
            capture_output=True, text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": root})
        check("deny" in (hand.stdout or ""),
              "reference gate: refuses a hand-written published file", verbose=verbose)
        proposing = subprocess.run(
            [sys.executable, os.path.join(root, ".claude", "hooks", "approval_gate.py")],
            input=json.dumps({"tool_name": "Write",
                              "tool_input": {"file_path": "proposals/P1.md"}}),
            capture_output=True, text=True,
            env={**os.environ, "CLAUDE_PROJECT_DIR": root})
        check("deny" not in (proposing.stdout or ""),
              "reference gate: allows writing a proposal — proposing has no effect",
              verbose=verbose)

        approve()
        check("deny" not in gate(), "reference gate: allows an approved apply",
              verbose=verbose)
        result = apply_it()
        check(result.returncode == 0, "reference gate: the approved apply succeeds",
              result.stderr[:160], verbose=verbose)
        check(os.path.exists(os.path.join(root, "triage", "P1.md")),
              "reference gate: the artifact is published", verbose=verbose)
        check("deny" in gate(), "reference gate: refuses a replayed approval",
              verbose=verbose)
        check(apply_it().returncode == 1,
              "reference gate: the tool refuses a replay independently of the hook",
              verbose=verbose)

        approve()
        with open(body, "a") as fh:
            fh.write("\nEdited after approval.\n")
        check("deny" in gate(), "reference gate: refuses after the proposal is edited",
              verbose=verbose)
        check(apply_it().returncode == 1,
              "reference gate: the tool refuses an edited proposal on its own",
              verbose=verbose)

        audit = os.path.join(root, "audit.jsonl")
        check(os.path.exists(audit), "reference gate: writes an audit trail",
              verbose=verbose)
        if os.path.exists(audit):
            events = [json.loads(l)["event"] for l in open(audit) if l.strip()]
            check("applied" in events and "apply_refused" in events,
                  "reference gate: the audit trail records applies and refusals",
                  str(events), verbose=verbose)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def check_promised_commands(verbose: bool) -> None:
    """Any /lab:x named in participant-facing text must exist as a skill.

    Promising a command that is not implemented means a participant types it and gets
    "Unknown command" mid-exercise. This is the check that stops that regressing.
    """
    print("promised commands exist")
    skills_dir = os.path.join(PLUGIN_ROOT, "skills")
    existing = {d for d in os.listdir(skills_dir)
                if os.path.exists(os.path.join(skills_dir, d, "SKILL.md"))}
    promised: dict[str, set[str]] = {}
    for base in ("skills", "modules", "references", "stages", "facilitator"):
        for dirpath, _dirs, names in os.walk(os.path.join(PLUGIN_ROOT, base)):
            for name in names:
                if not name.endswith((".md", ".py", ".json")):
                    continue
                full = os.path.join(dirpath, name)
                try:
                    text = open(full, encoding="utf-8").read()
                except (OSError, UnicodeDecodeError):
                    continue
                for cmd in re.findall(r"/lab:([a-z][a-z-]*)", text):
                    promised.setdefault(cmd, set()).add(os.path.relpath(full, PLUGIN_ROOT))
    for cmd in sorted(promised):
        where = ", ".join(sorted(promised[cmd])[:3])
        check(cmd in existing, f"/lab:{cmd} is implemented", f"promised in {where}",
              verbose=verbose)


def check_workspace_lifecycle(verbose: bool) -> None:
    """verify and catchup have to work on a partially-staged workspace, not just a full one."""
    print("workspace lifecycle (verify, catchup)")
    tid = track_ids()[0]
    root = tempfile.mkdtemp(prefix="lablife-")
    try:
        run = lambda script, *a: subprocess.run(
            [sys.executable, os.path.join(SCRIPTS, script), "--root", root, *a],
            capture_output=True, text=True)
        run("state.py", "init")
        run("state.py", "set-track", tid)
        first = stage_ids()[0]
        run("workspace.py", "stage", first)

        result = run("workspace.py", "verify")
        check(result.returncode == 0, "verify passes on a partially-staged workspace",
              result.stdout.strip()[-160:], verbose=verbose)

        installed = json.loads(result.stdout).get("expected", 0)
        check(installed > 0, "verify checks the installed files", verbose=verbose)

        # break it, confirm it is detected, then repair it
        victim = os.path.join(root, ".claude", "settings.json")
        if os.path.exists(victim):
            os.remove(victim)
        result = run("workspace.py", "verify")
        check(result.returncode != 0, "verify detects a damaged workspace", verbose=verbose)

        result = run("workspace.py", "catchup")
        check(result.returncode == 0, "catchup runs", result.stderr.strip()[:160],
              verbose=verbose)
        result = run("workspace.py", "verify")
        check(result.returncode == 0, "catchup repairs the workspace",
              result.stdout.strip()[-160:], verbose=verbose)

        result = run("workspace.py", "catchup", "--with-reference")
        check(result.returncode == 0, "catchup --with-reference runs", verbose=verbose)
        payload = json.loads(result.stdout)
        ref = payload.get("reference_skill") or ""
        check("NOT AVAILABLE" not in ref,
              f"{tid}: catchup --with-reference finds a reference skill", ref,
              verbose=verbose)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def check_version_is_publishable(verbose: bool) -> None:
    """The plugin version must match the marketplace entry, or nobody gets the update.

    Claude Code only re-installs a plugin when its declared version changes. A push that
    leaves the version alone reaches nobody: `plugin install` reports "already installed"
    and the participant keeps the old build, silently. This check will not know whether the
    version was bumped for *this* change, but it does catch the two manifests drifting apart,
    which is the half that is mechanically detectable.
    """
    print("version is publishable")
    plugin = load(os.path.join(PLUGIN_ROOT, ".claude-plugin", "plugin.json"))
    declared = plugin.get("version")
    check(bool(declared), "plugin.json declares a version", verbose=verbose)

    # The plugin sits one level below the repo root locally and two in the marketplace
    # layout (plugins/lab/), so walk up rather than assuming a depth.
    market = None
    here = PLUGIN_ROOT
    for _ in range(4):
        here = os.path.dirname(here)
        if not here or here == os.sep:
            break
        candidate = os.path.join(here, ".claude-plugin", "marketplace.json")
        if os.path.exists(candidate):
            market = candidate
            break
    if not market:
        warn("no marketplace.json found above the plugin — cannot compare declared versions")
        return
    entries = [p for p in load(market).get("plugins", [])
               if p.get("name") == plugin.get("name")]
    check(bool(entries), f"marketplace.json lists a plugin named {plugin.get('name')!r}",
          verbose=verbose)
    if entries:
        check(entries[0].get("version") == declared,
              "marketplace entry version matches plugin.json",
              f"marketplace says {entries[0].get('version')!r}, plugin says {declared!r}",
              verbose=verbose)


def check_scripts_run(verbose: bool) -> None:
    print("scripts")
    for name, args in [("doctor.py", ["--checklist"]),
                       ("state.py", ["tracks"]),
                       ("workspace.py", ["manifest", "--track", track_ids()[0]])]:
        result = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)] + args,
                                capture_output=True, text=True)
        check(result.returncode == 0, f"{name} {' '.join(args)} runs",
              result.stderr.strip()[:160], verbose=verbose)

    # bad input must fail loudly, not silently
    result = subprocess.run([sys.executable, os.path.join(SCRIPTS, "workspace.py"),
                             "manifest", "--track", "nonsense"],
                            capture_output=True, text=True)
    check(result.returncode != 0, "workspace.py rejects an unknown track", verbose=verbose)
    result = subprocess.run([sys.executable, os.path.join(SCRIPTS, "workspace.py"),
                             "--root", tempfile.gettempdir(), "stage", "nonsense"],
                            capture_output=True, text=True)
    check(result.returncode != 0, "workspace.py rejects an unknown stage", verbose=verbose)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    check_tracks(args.verbose)
    check_stages(args.verbose)
    check_shared_files_are_track_neutral(args.verbose)
    check_substitution(args.verbose)
    check_reference_skills(args.verbose)
    check_reference_tools(args.verbose)
    check_reference_hooks(args.verbose)
    check_reference_plugins(args.verbose)
    check_corpora(args.verbose)
    check_golden_sets(args.verbose)
    check_baseline_floor(args.verbose)
    check_module2_artifacts(args.verbose)
    check_graph_questions(args.verbose)
    check_reference_graphs(args.verbose)
    check_graph_answers(args.verbose)
    check_module3_artifacts(args.verbose)
    check_catchup_restores_module3(args.verbose)
    check_module4_artifacts(args.verbose)
    check_stage_ids_exist(args.verbose)
    check_tutor_facing_text(args.verbose)
    check_promised_commands(args.verbose)
    check_documented_invocations(args.verbose)
    check_workspace_lifecycle(args.verbose)
    check_version_is_publishable(args.verbose)
    check_scripts_run(args.verbose)

    print()
    if warnings:
        print(f"{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ! {w}")
        print()
    if failures:
        print(f"FAILED — {len(failures)} problem(s), {passed} checks passed:")
        for f in failures:
            print(f"  x {f}")
        return 1
    print(f"OK — {passed} checks passed"
          + (f", {len(warnings)} warning(s)" if warnings else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
