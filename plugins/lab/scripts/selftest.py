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
    check_tutor_facing_text(args.verbose)
    check_promised_commands(args.verbose)
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
