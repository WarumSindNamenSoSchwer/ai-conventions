# ai-conventions

Shared rules, code style, plugins and agent guard rails for MCS projects.
Included as the `.mcs/` git submodule; one setup command connects a project
for Claude Code and Jcode on macOS and Windows.

Status: implementation plan approved, phase 1 (core rules) done. See
[the plan](Docs/Plans/ai-conventions.md).

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="Docs/Plans/assets/ai-conventions.architecture.dark.png">
  <img alt="ai-conventions architecture: Claude Code and Jcode send every tool call through guard.py, which checks flash, git, plan and approve rules against Docs/Plans; the developer approves plans with the mcs CLI; setup wires the project and installs the Jcode dispatcher; marketplace.json pins all plugins." src="Docs/Plans/assets/ai-conventions.architecture.light.png">
</picture>

Interactive version with search, path tracing, dark/light theme and export:
[`Docs/Plans/ai-conventions.architecture.html`](Docs/Plans/ai-conventions.architecture.html).
GitHub shows HTML files as source, so download the file (or clone the
repository) and open it in a browser. The diagram source is
[`ai-conventions.architecture.json`](Docs/Plans/ai-conventions.architecture.json),
rendered with [archify](https://github.com/tt-a1i/archify).

## What is in here

| Path | Content |
|---|---|
| [AGENTS.md](AGENTS.md) | The hard rules every agent and developer follows |
| [rules/general.md](rules/general.md) | Plan first, git, pull requests, documentation |
| [rules/agents.md](rules/agents.md) | Planning flow, mandatory plan sections, model per step |
| [rules/embedded.md](rules/embedded.md) | Firmware: memory, safety, interrupts, hardware boundary |
| [rules/c-cpp.md](rules/c-cpp.md) | C and C++ layout and naming |
| [Docs/Plans/](Docs/Plans/) | Plans, including the approved implementation plan |

Coming in later phases: clang-format and clang-tidy config, the guard,
the `mcs` CLI, the plugin marketplace, setup and uninstall scripts.
