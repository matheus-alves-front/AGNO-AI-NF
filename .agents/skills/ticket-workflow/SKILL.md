---
name: ticket-workflow
description: Workflow for ticket-driven work in existing repositories.
---


Use this skill when the task comes from a ticket, issue, Slack context, or existing codebase.

## Steps
1. Restate the goal and define the exact change surface.
2. Identify touched modules, files, dependencies, and probable risks.
3. Ask Codex to use `architect` for a short plan.
4. Ask Codex to use `developer` for minimal-scope implementation.
5. Ask Codex to use `reviewer` for architecture and scope audit.
6. Ask Codex to use `qa` for acceptance checks.
7. Return: summary, changed files, risks, and validation steps.

## Never do
- Rewrite unrelated code.
- Change architecture without justification.
- Claim success without validation.

