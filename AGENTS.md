# Agent OS for VS Code + Codex

This repository is configured for a disciplined multi-agent workflow in Codex.

## Core operating rules
- Never jump straight to implementation when the request requires discovery, architecture, or acceptance criteria.
- Prefer minimal-scope changes.
- Do not rewrite unrelated code.
- Respect existing architecture and conventions before introducing new patterns.
- When the task is ambiguous, produce a short plan and assumptions first.
- For risky changes, ask Codex to use `reviewer` and `qa` before concluding.

## Roles available
- architect
- developer
- reviewer
- qa
- product-owner
- frontend-specialist
- mobile-specialist
- ai-systems-specialist
- stack-researcher

## Skill invocation
Use skills explicitly with `$skill-name` when you want deterministic behavior.
Examples:
- `$ticket-workflow`
- `$build-workflow`
- `$stack-workflow`
- `$safe-refactor`
- `$code-review`

## Subagent invocation
Ask Codex explicitly in natural language, for example:
- "Spawn the architect agent to create a short implementation plan."
- "Use the reviewer agent to audit this diff against the requirements."
- "Use the mobile-specialist agent to validate this Expo flow."

## Standard workflows
### Existing company code / ticket work
1. Use `$ticket-workflow`
2. Have `architect` map the scope and touched files
3. Have `developer` implement only approved scope
4. Have `reviewer` and `qa` validate before final output

### New project / feature build
1. Use `$build-workflow`
2. Produce scope
3. Produce technical spec with acceptance criteria
4. Produce architecture
5. Produce checklist / phased plan
6. Implement the current phase only
7. Run `reviewer` and `qa`

### New stack / framework / major version
1. Use `$stack-workflow`
2. Have `stack-researcher` check official docs and versions
3. Extract conventions
4. Turn findings into reusable patterns
5. Review impact on project architecture
