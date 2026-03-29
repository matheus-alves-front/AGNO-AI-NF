---
name: stack-workflow
description: Workflow for adding or updating a stack, framework, or major version.
---


Use when a new technology enters the project or when a major version changes.

## Sequence
1. Ask `stack-researcher` to inspect official docs and migration guides.
2. Separate latest stable from project-installed version.
3. Extract conventions and anti-patterns.
4. Have `architect` decide how the stack fits the current architecture.
5. Have `reviewer` audit the proposed conventions.

## Deliverables
- version notes
- recommended patterns
- migration risks
- reusable implementation guidance

