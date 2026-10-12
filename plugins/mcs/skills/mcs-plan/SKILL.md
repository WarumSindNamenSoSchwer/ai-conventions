---
name: mcs-plan
description: Use before any task that changes code in an MCS repository. Drives the mandatory planning flow (brainstorming, improve, draft, ponytail, archify, thermo-nuclear, writing-plans) and writes Docs/Plans/<name>.md with every section mcs approve requires. Code edits are blocked by the guard until a human approves the plan.
---

# MCS planning flow

Code changes in MCS repositories need an approved plan in `Docs/Plans/`. The
guard blocks edits to code files until a human runs `mcs approve <name>` on
the current branch. You never approve a plan, never run `mcs approve`, and
never write `status: approved`.

## Before you start

1. Check the branch: `git branch --show-current`. If it is `main`, `develop`
   or `release/*`, propose a `feature/<name>` or `fix/<name>` branch and ask
   before creating it. Approval is bound to the branch.
2. Pick a short kebab-case plan name, for example `uart-dma-rx`. The plan file
   is `Docs/Plans/<name>.md`.
3. Run `.mcs/bin/mcs status` to see existing plans. Reuse a draft for the same
   task instead of starting a second one.

## Steps and model per step

Cheap models read, strong models judge. Reviewers never read the repository
themselves: a Haiku agent collects the diff, the touched files and the facts
first, the reviewer works from that summary.

| # | Step | Skill | Model | Output section |
|---|---|---|---|---|
| 1 | Clarify goal and requirements with the user | `brainstorming` (superpowers) | session model | `## Brainstorming` |
| 2 | Survey existing code (larger tasks) | `improve` | Haiku collects, session model summarizes | `## Existing code (improve)` |
| 3 | Draft the plan | none | session model | `## Goal`, `## Design` |
| 4 | Simplify the draft | `ponytail` | session model | `## Simplification (ponytail)` |
| 5 | Architecture diagram | `archify` | session model | `## Architecture (archify)` |
| 6 | Strict review of the design | `thermo-nuclear-code-quality-review` | Sonnet; Opus for guard, setup or security-relevant work | `## Quality review (thermo-nuclear)` |
| 7 | Final plan with tasks | `writing-plans` (superpowers) | session model | `## Implementation` |
| 8 | Approval | human only | none | front matter, written by `mcs approve` |

Step 2 may be one sentence for small tasks ("No existing code touched besides
`src/uart.c`"), but the section must not be empty. Defensive checks required
by `.mcs/rules/embedded.md` are never removed by step 4.

### Step 5: archify

Write the diagram to `Docs/Plans/<name>.architecture.html` and link it from
the section as `[Architecture](<name>.architecture.html)`. Then open it for
the user, because relative links in the Jcode side panel do not open local
HTML files:

- macOS: `open Docs/Plans/<name>.architecture.html`
- Windows (PowerShell): `Start-Process Docs/Plans/<name>.architecture.html`
- Linux: `xdg-open Docs/Plans/<name>.architecture.html`

When the change touches only one component, skip the diagram and write
`Single component, no diagram: <reason>` in the section instead.

## Plan template

Write the file with LF line endings. Leave the front matter `status: proposed`;
`mcs approve` adds the approval fields.

```markdown
---
title: <one line>
status: proposed
---

# Plan: <title>

## Goal
<what changes for whom, and how we know it worked>

## Brainstorming
<options considered, questions asked, decisions and why>

## Existing code (improve)
<relevant files, current behaviour, constraints found>

## Design
<the approach, files to change, interfaces>

## Simplification (ponytail)
<what was cut or kept on purpose, and why>

## Architecture (archify)
[Architecture](<name>.architecture.html)

## Quality review (thermo-nuclear)
<findings with severity, and how each was resolved>

## Implementation
- [ ] <task> (file, test, expected result)

## Verification
| Requirement | Check | Expected |
|---|---|---|
```

## Hand-off

When the plan is complete:

1. Show the user the plan path and a five-line summary.
2. Ask them to review it and run, in their own terminal:
   `.mcs/bin/mcs approve <name>` (Windows: `py .mcs\bin\mcs approve <name>`).
3. Stop. Do not edit code until the user confirms approval. If an edit is
   blocked with "no approved plan", the approval is missing or the plan was
   changed after approval; ask the user to re-approve.

After approval, any change to the plan body invalidates the approval. Small
corrections during implementation go into a new plan revision that the user
approves again.
