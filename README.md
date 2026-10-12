# ai-conventions

Shared rules, code style, plugins and agent guard rails for MCS projects.
Included as the `.mcs/` git submodule; one setup command connects a project
for Claude Code and Jcode on macOS and Windows.

Status: version 1 implemented and tested on macOS, Windows test pending
([guide](Docs/windows-test.md)). See [the plan](Docs/Plans/ai-conventions.md).

## Use in a project

```sh
git submodule add <url-of-this-repo> .mcs
.mcs/setup.sh                                               # macOS, Linux
powershell -ExecutionPolicy Bypass -File .mcs\setup.ps1     # Windows
```

Setup needs Python 3.10+, git, Node.js and clang-format (Windows: Git for
Windows provides the Git Bash that Claude Code hooks run in). It writes:

| File | Content |
|---|---|
| `CLAUDE.md` | Import block for `AGENTS.md` and `rules/` (own content stays) |
| `.claude/settings.json` | `mcs` marketplace, team plugins, guard hook, deny rules, autocompact 70 |
| `.jcode/prompt-overlay.md` | The rules inlined, because Jcode does not expand `@` imports |
| `.jcode/skills/mcs-plan/` | Planning skill for Jcode |
| `.gitattributes`, `.gitignore` | LF for plans, ignore `.mcs-guard.log` |
| `~/.jcode/config.toml` | `[hooks] pre_tool` dispatcher, once per machine; a previous hook keeps running |

After setup, commit those files. `.mcs/uninstall.sh` (or `.ps1`) removes
exactly what setup wrote.

Daily use:

| Command | Purpose |
|---|---|
| `.mcs/bin/mcs approve <plan>` | Approve `Docs/Plans/<plan>.md` for the current branch (humans only) |
| `.mcs/bin/mcs status` | List plans, regenerate `Docs/Plans/index.md` |
| `.mcs/bin/mcs check` | Is the setup current, did the guard log errors |

On Windows prefix `py -3`, for example `py -3 .mcs\bin\mcs status`.

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
| [config/](config/) | `.clang-format`, `.clang-tidy`, `.editorconfig` and style samples |
| [guard/](guard/) | Guard for flash, git and plan rules; [contract](guard/contract.md) and tests |
| [adapters/](adapters/) | Hook wiring for Claude Code and the Jcode dispatcher |
| [bin/mcs](bin/mcs) | `approve`, `status`, `check`, `setup`, `uninstall` |
| [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) | Team plugins, third-party ones pinned by commit |
| [plugins/mcs/](plugins/mcs/) | `mcs-plan` skill |
| [Docs/Plans/](Docs/Plans/) | Plans, including the approved implementation plan |

## Tests

```sh
python3 -m unittest discover -s guard                  # guard rules, both agents
python3 -m unittest discover -s bin -p 'test_*.py'     # mcs CLI
test/e2e_setup.sh                                      # setup/uninstall, two projects, throwaway HOME
claude plugin validate .
```
