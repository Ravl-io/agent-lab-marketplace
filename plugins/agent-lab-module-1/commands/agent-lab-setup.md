---
description: Create the Module 1 ops-reporting sandbox in the current directory
argument-hint: "[target directory, default: ./agent-lab-sandbox]"
allowed-tools: Bash, Read
---

Set up the Module 1 training sandbox so the participant can start a task card.

Target directory: `$1` if given, otherwise `./agent-lab-sandbox` relative to the current
working directory.

Steps:

1. If the target directory already exists and is not empty, STOP and tell the participant.
   Do not overwrite an in-progress lab. Offer a different directory name instead.
2. Copy the WHOLE workspace payload into the target directory, including hidden files.
   The payload lives at `${CLAUDE_PLUGIN_ROOT}/workspace/` and includes `CLAUDE.md`,
   `intent.md`, `README.md`, the hidden `.claude/` directory holding `settings.json` and
   `skills/summarize-ops/`, and the `reports/`, `summaries/`, `scripts/` and `tasks/`
   directories.
   Use the copy command that suits the shell you are actually running in:
   - POSIX shells: `cp -R "${CLAUDE_PLUGIN_ROOT}/workspace/." "<target>/"`
   - Windows PowerShell: `Copy-Item -Path "$env:CLAUDE_PLUGIN_ROOT\workspace\*" -Destination "<target>" -Recurse -Force`
   Then confirm `.claude/skills/summarize-ops/SKILL.md` exists in the target. If the hidden
   directory did not come across, the lab will not behave correctly and you must fix it
   before continuing.
3. Initialise a git repository in the target directory and make one commit called
   `Starting state`. The lab's reset instructions depend on git being present. Participants
   reset by running `git checkout .` and `git clean -fd` as two separate commands, because
   `&&` is not a valid separator in Windows PowerShell 5.1.
4. Verify the workspace is healthy by running the style checker from the target directory
   on the existing summary: `python scripts/check_style.py summaries/2026-08-10-weekly-summary.md`.
   It must print `STYLE CHECK: PASS`. On Windows, if `python` launches the Microsoft Store
   instead of printing output, try `py` instead. If Python is missing or the check fails, say
   so plainly rather than continuing.
5. Tell the participant the directory is ready, that the task cards are in
   `tasks/TASK-CARDS.md`, and that they should `cd` into it and start a new session there
   so the project's `CLAUDE.md` and permission policy load.

Do not solve any task card. This command only prepares the workspace.
