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
2. Copy the workspace payload into the target directory:
   `cp -R "${CLAUDE_PLUGIN_ROOT}/workspace/." "<target>/"`
   The payload includes `CLAUDE.md`, `intent.md`, `README.md`, `.claude/settings.json`,
   and the `reports/`, `summaries/`, `scripts/` and `tasks/` directories.
3. Initialise a git repository in the target directory and make one commit called
   `Starting state`. The lab's reset instructions depend on git being present:
   participants reset with `git checkout . && git clean -fd`.
4. Verify the sandbox is healthy by running `python scripts/check_style.py summaries/2026-08-10-weekly-summary.md`
   from the target directory. It must print `STYLE CHECK: PASS`. If Python is missing or
   the check fails, say so plainly rather than continuing.
5. Tell the participant the directory is ready, that the task cards are in
   `tasks/TASK-CARDS.md`, and that they should `cd` into it and start a new session there
   so the project's `CLAUDE.md` and permission policy load.

Do not solve any task card. This command only prepares the workspace.
