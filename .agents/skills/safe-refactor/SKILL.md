---
name: safe-refactor
description: Conservative refactor protocol for existing code.
---


Use before any refactor in code that already works.

Checklist:
- Define why the refactor is necessary.
- Define the exact allowed scope.
- Preserve behavior first, improve structure second.
- Prefer incremental commits and easy rollback.
- Always request `reviewer` and `qa` after completion.

