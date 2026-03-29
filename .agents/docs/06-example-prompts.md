# Example Prompts

## Ticket work
Use `$ticket-workflow` for this task.
Read the ticket context and define the exact touched area first.
Spawn the architect agent for the plan.
Then implement with minimal scope.
Then use reviewer and qa before finalizing.

## New feature / product
Use `$build-workflow`.
Start with scope, then technical spec with acceptance criteria, then architecture, then checklist.
Do not jump directly to code.

## Stack addition
Use `$stack-workflow`.
I want to add TanStack Query v5.
Start from official docs and migration notes.
Separate latest stable from the version used in this project.
Then propose reusable conventions.

## Specialist examples
Spawn the frontend-specialist agent to review the component architecture for this screen.
Spawn the mobile-specialist agent to validate this Expo navigation flow.
Spawn the ai-systems-specialist agent to review this LangGraph state design.
