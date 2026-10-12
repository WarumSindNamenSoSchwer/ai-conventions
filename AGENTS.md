# MCS Conventions

Binding rules for every MCS repository that includes this repository as the
`.mcs/` submodule. They apply to humans and AI agents alike.

## Hard rules

1. **Plan first.** No code change without a plan in `Docs/Plans/` that a human
   approved with `mcs approve`. Agents never approve plans.
2. **Never push to `main`, `develop` or `release/*`.** Branch, push the branch,
   open a pull request, ask who reviews, never merge your own.
3. **Agents never flash.** No flashing, erasing, resetting or debugging of a
   connected device (J-Link, OpenOCD, project `flash`/`erase` scripts).
4. **No dynamic allocation after init** in firmware. ETL over STL over raw
   arrays.
5. **No recursion. Check every return value. Keep interrupt handlers short.**
6. **Vendored code and submodules are read-only.**
7. **Nothing leaves the project.** No emails, messages, tickets or files in
   external systems.
8. **No AI traces** in commits, pull requests, comments or docs.

Hard rules 1 to 3 are enforced by the guard in `guard/`. Breaking any of them
is a defect, not a style question.

## Rule files

| File | Scope |
|---|---|
| [rules/general.md](rules/general.md) | Plan first, git, pull requests, documentation, external systems |
| [rules/agents.md](rules/agents.md) | Planning flow, mandatory plan sections, model per step, agent behaviour |
| [rules/embedded.md](rules/embedded.md) | Firmware: memory, safety, interrupts, hardware boundary, vendored code |
| [rules/c-cpp.md](rules/c-cpp.md) | C and C++ layout, naming, control flow |

Precedence when rules conflict: the project's own instructions below the
import line, then this file and `rules/`, then tool defaults.
