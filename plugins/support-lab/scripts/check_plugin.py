#!/usr/bin/env python3
"""Validate the plugin a participant asked Claude Code to build in Step 9.

    check_plugin.py [path]          default: ./first-look-plugin

Accepts either layout:

    first-look-plugin/                         (marketplace root — preferred, installable)
      .claude-plugin/marketplace.json
      plugins/first-look/
        .claude-plugin/plugin.json
        skills/first-look/SKILL.md
        scripts/check_findings.py

    first-look-plugin/                         (bare plugin — loads with --plugin-dir only)
      .claude-plugin/plugin.json
      skills/...

Prints JSON: problems (blocking), notes (non-blocking), install commands. Exit 0 = passes.
Stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

REQUIRED_MENTIONS = {
    "deploys.log": r"deploys\.log",
    "config-audit": r"config-audit",
    "evidence": r"evidence",
    "check_findings": r"check_findings",
    "docs quote": r"docs/|documentation",
    "VERIFIED / RULED OUT": r"VERIFIED|RULED OUT",
    "escalation": r"escalat",
    "last known good": r"last known good|yesterday|succeed|previous",
}


def read_json(path: str):
    try:
        with open(path) as fh:
            return json.load(fh), None
    except (OSError, ValueError) as exc:
        return None, str(exc)


def frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, m.group(2)


def main() -> int:
    target = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "first-look-plugin")
    problems, notes = [], []
    result = {"target": target}

    if not os.path.isdir(target):
        print(json.dumps({"target": target, "problems": [f"folder does not exist: {target}"],
                          "notes": [], "passes": False}, indent=2))
        return 1

    # --- locate the plugin root -------------------------------------------------------
    mk_path = os.path.join(target, ".claude-plugin", "marketplace.json")
    pl_path = os.path.join(target, ".claude-plugin", "plugin.json")
    marketplace, plugin_root, mk_name, plugin_name = None, None, None, None

    if os.path.exists(mk_path):
        marketplace, err = read_json(mk_path)
        if err:
            problems.append(f"marketplace.json is not valid JSON: {err}")
        else:
            mk_name = marketplace.get("name")
            if not mk_name:
                problems.append("marketplace.json has no 'name'")
            plugins = marketplace.get("plugins") or []
            if not plugins:
                problems.append("marketplace.json lists no plugins")
            else:
                entry = plugins[0]
                plugin_name = entry.get("name")
                src = entry.get("source")
                if isinstance(src, dict):
                    src = src.get("path")
                if not isinstance(src, str):
                    problems.append("marketplace plugin entry needs a relative 'source' path")
                else:
                    plugin_root = os.path.normpath(os.path.join(target, src))
    if plugin_root is None and os.path.exists(pl_path):
        plugin_root = target
        notes.append("no marketplace.json: the plugin loads with --plugin-dir but cannot be "
                     "installed with /plugin install")
    if plugin_root is None:
        problems.append("no .claude-plugin/plugin.json and no .claude-plugin/marketplace.json "
                        "found under the folder")
        print(json.dumps({**result, "problems": problems, "notes": notes, "passes": False}, indent=2))
        return 1
    result["plugin_root"] = plugin_root

    # --- plugin.json -----------------------------------------------------------------
    manifest_path = os.path.join(plugin_root, ".claude-plugin", "plugin.json")
    if not os.path.exists(manifest_path):
        problems.append(f"missing {os.path.relpath(manifest_path, target)}")
    else:
        manifest, err = read_json(manifest_path)
        if err:
            problems.append(f"plugin.json is not valid JSON: {err}")
        else:
            name = manifest.get("name")
            if not name:
                problems.append("plugin.json has no 'name'")
            elif not re.match(r"^[a-z0-9][a-z0-9-]*$", name):
                problems.append(f"plugin name '{name}' should be lowercase letters, digits and hyphens")
            plugin_name = plugin_name or name
            if marketplace and name and plugin_name != name:
                problems.append(f"marketplace lists plugin '{plugin_name}' but plugin.json says '{name}'")
            if not manifest.get("description"):
                notes.append("plugin.json has no description (not blocking)")
    result["plugin_name"] = plugin_name

    # --- the skill -------------------------------------------------------------------
    skills_dir = os.path.join(plugin_root, "skills")
    skill_files = []
    if os.path.isdir(skills_dir):
        for entry in sorted(os.listdir(skills_dir)):
            f = os.path.join(skills_dir, entry, "SKILL.md")
            if os.path.exists(f):
                skill_files.append(f)
    # legacy commands/ also count
    cmd_dir = os.path.join(plugin_root, "commands")
    if os.path.isdir(cmd_dir):
        for entry in sorted(os.listdir(cmd_dir)):
            if entry.endswith(".md"):
                skill_files.append(os.path.join(cmd_dir, entry))
    if not skill_files:
        problems.append("no skill found: expected skills/<name>/SKILL.md")
    else:
        chosen = None
        for f in skill_files:
            if "first-look" in f or "first_look" in f or "issue" in f:
                chosen = f
                break
        chosen = chosen or skill_files[0]
        result["skill_file"] = os.path.relpath(chosen, target)
        with open(chosen, encoding="utf-8") as fh:
            text = fh.read()
        meta, body = frontmatter(text)
        if not meta:
            problems.append("SKILL.md has no frontmatter (--- name / description ---)")
        desc = (meta.get("description") or "")
        if not desc:
            problems.append("SKILL.md frontmatter has no description — the description is how the "
                            "skill gets picked")
        elif "first look" not in desc.lower():
            problems.append("the description does not contain the words 'first look' — say it the "
                            "way you will ask for it")
        if meta.get("disable-model-invocation", "").lower() in ("true", "yes", "1", "on"):
            problems.append("disable-model-invocation is on: the skill would only run as a slash "
                            "command, never from 'First look on JIRA-4907'")
        for label, pattern in REQUIRED_MENTIONS.items():
            if not re.search(pattern, body, re.I):
                problems.append(f"the skill never mentions {label}")
        if "${CLAUDE_PLUGIN_ROOT}" not in body:
            notes.append("the skill does not use ${CLAUDE_PLUGIN_ROOT} to reach its own script; "
                         "it will only find check_findings.py if the workspace has one")
        result["skill_name"] = meta.get("name") or os.path.basename(os.path.dirname(chosen))

    # --- the script ------------------------------------------------------------------
    script = os.path.join(plugin_root, "scripts", "check_findings.py")
    if not os.path.exists(script):
        problems.append("scripts/check_findings.py is not in the plugin — the done-when depends on it")
    else:
        sample = os.path.join(os.getcwd(), "tickets", "JIRA-4821", "findings.md")
        if os.path.exists(sample):
            try:
                p = subprocess.run([sys.executable, script, sample], capture_output=True,
                                   text=True, timeout=30)
                if p.returncode != 0:
                    problems.append("the plugin's check_findings.py fails on tickets/JIRA-4821/findings.md: "
                                    + (p.stdout + p.stderr).strip()[:300])
                else:
                    notes.append("plugin's check_findings.py passes on the JIRA-4821 findings")
            except (OSError, subprocess.SubprocessError) as exc:
                problems.append(f"could not run the plugin's check_findings.py: {exc}")

    # --- official validator, when available -------------------------------------------
    if shutil.which("claude"):
        try:
            p = subprocess.run(["claude", "plugin", "validate", plugin_root], capture_output=True,
                               text=True, timeout=60)
            out = (p.stdout + p.stderr).strip()
            if p.returncode != 0:
                problems.append("claude plugin validate failed: " + out[:400])
            else:
                notes.append("claude plugin validate: ok")
        except (OSError, subprocess.SubprocessError) as exc:
            notes.append(f"claude plugin validate could not run: {exc}")

    # --- install commands ------------------------------------------------------------
    install = {}
    if marketplace and mk_name and plugin_name:
        install["in_claude_code"] = [
            f"/plugin marketplace add {target}",
            f"/plugin install {plugin_name}@{mk_name}",
        ]
    install["in_a_terminal"] = [f"claude --plugin-dir {plugin_root}"]
    if plugin_name and result.get("skill_name"):
        install["slash_command"] = f"/{plugin_name}:{result['skill_name']}"

    passes = not problems
    print(json.dumps({**result, "problems": problems, "notes": notes,
                      "install": install, "passes": passes}, indent=2))
    return 0 if passes else 1


if __name__ == "__main__":
    sys.exit(main())
