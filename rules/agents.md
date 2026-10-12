# Rules for AI Agents

Apply to every coding agent working in an MCS repository (Claude Code, Jcode,
Codex, Cursor).

## Planning flow

Every task that changes code goes through the `mcs-plan` skill and produces a
plan in `Docs/Plans/<name>.md`:

1. `brainstorming` (superpowers): clarify goal and requirements
2. `improve`: survey the existing code, for larger tasks
3. draft the plan
4. `ponytail`: simplify the draft
5. `archify`: architecture diagram `Docs/Plans/<name>.architecture.html`
6. `thermo-nuclear-code-quality-review`: strict review of the design
7. `writing-plans` (superpowers): final plan, `status: proposed`
8. a human approves with `mcs approve <name>`

A plan can only be approved when it contains all mandatory sections:

- `## Brainstorming`
- `## Existing code (improve)`
- `## Simplification (ponytail)`
- `## Architecture (archify)`
- `## Quality review (thermo-nuclear)`

When only one component is affected, the archify section may instead say
`Single component, no diagram: <reason>`.

Agents never approve plans, never run `mcs approve`, and never write
`status: approved` into a plan. The guard blocks all three.

Defensive checks required by `rules/embedded.md` are never simplified away by
`ponytail`.

## Model per step

Cheap models read, strong models judge.

| Step | Model |
|---|---|
| file search, survey, log reading, collecting a diff | Haiku |
| brainstorming, draft, ponytail, archify, writing-plans | session model |
| thermo-nuclear review | Sonnet; Opus for guard, setup or security-relevant changes |
| code-review before a pull request | Sonnet |
| implementation | Sonnet |

Reviewers do not read the repository themselves. A Haiku agent collects the
diff, the touched files and the relevant facts; the reviewer works from that
summary.

## Before editing

- Read `AGENTS.md` and the project's own instructions.
- Name the files you are about to change.
- When the requirement is ambiguous, ask.

## While editing

- Follow the conventions, not surrounding legacy code, when the two differ.
  Do not reformat lines you were not asked to change.
- Keep changes scoped to the task.
- Never edit vendored code or submodules.
- No absolute local paths (`/Users/...`, `C:\Users\...`) in committed files.
  Use repository-relative paths.

## Reporting

- Answer short. No summaries of the obvious.
- Solve problems instead of only reporting them; find the cause.
- Say "I don't know" instead of guessing.
- No emojis, no exclamation rhetoric, no marketing tone.
- Never claim something is tested unless the test actually ran and passed.
- Quote file paths and line numbers for findings.

## Language

Everything is written in English: code, comments, commit messages, pull
requests, documentation and plans.
