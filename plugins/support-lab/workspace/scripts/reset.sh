#!/usr/bin/env bash
# Resets a participant sandbox to the starting state: removes generated findings, briefs and participant-written skills.
set -e
cd "$(dirname "$0")/.."
rm -rf tickets/JIRA-*/ out/ .claude/skills/issue-analysis .claude/skills/docs-vs-issue .claude/skills/feature-request-brief .claude/skills/known-issue-article
rm -f tickets/*/findings.md
echo "sandbox reset — provided skills (ticket-cluster, feedback-themes) kept"
