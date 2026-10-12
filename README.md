# ai-conventions

Shared rules, code style, plugins and agent guard rails for MCS projects.
Included as the `.mcs/` git submodule; one setup command connects a project
for Claude Code and Jcode on macOS and Windows.

Status: version 1 implemented and tested on macOS, Windows test pending
([guide](Docs/windows-test.md)). See [the plan](Docs/Plans/ai-conventions.md).

## Use in a project

### 1. Prerequisites (once per machine)

Python 3.10+, git, Node.js, clang-format, and Claude Code and/or Jcode.

```sh
brew install python git node clang-format                                  # macOS
winget install Python.Python.3.12 Git.Git OpenJS.NodeJS.LTS LLVM.LLVM     # Windows
```

On Windows, Git for Windows brings Git Bash, which the Claude Code hooks need.

### 2. Connect the project

Repository URL for now: `https://github.com/WarumSindNamenSoSchwer/ai-conventions.git`
(moves to the `mcs-datalabs` organisation later).

New project, not connected yet (one person does this once):

```sh
git submodule add <repo-url> .mcs
.mcs/setup.sh                                               # macOS, Linux
powershell -ExecutionPolicy Bypass -File .mcs\setup.ps1     # Windows
git add -A && git commit -m "Connect MCS conventions"
```

Project that already has `.mcs` (everyone else, after cloning):

```sh
git submodule update --init
.mcs/setup.sh                                               # or setup.ps1 on Windows
```

Setup takes about a minute (it installs the Claude Code plugins). When
Claude Code first opens the project, accept "trust this folder".

### 3. Daily work

1. Create a branch: `git checkout -b feature/<name>`.
2. Ask the agent: "Use mcs-plan to plan <task>". It writes
   `Docs/Plans/<name>.md` and opens the architecture diagram.
3. Read the plan. When it is good, approve it in **your own terminal**:
   `.mcs/bin/mcs approve <name>` (Windows: `py -3 .mcs\bin\mcs approve <name>`)
   and type the plan name to confirm.
4. Now the agent may edit code on this branch.
5. Push the branch and open a pull request. Never push to `main`, `develop`
   or `release/*`.

If you change the plan after approval, approve it again.

### When the guard blocks

The agent sees a message starting with `[mcs guard]`:

| Message | What to do |
|---|---|
| `git: push to protected branch` | Push a `feature/` or `fix/` branch and open a pull request |
| `flash: ...` | Flash, erase or debug the device yourself |
| `plan: ... has no approved plan` | Plan with `mcs-plan`, then `mcs approve` (step 3) |
| `plan: only a human approves plans` | Run `mcs approve` yourself, not through the agent |

### Commands

| Command | Purpose |
|---|---|
| `.mcs/bin/mcs approve <plan>` | Approve `Docs/Plans/<plan>.md` for the current branch (humans only) |
| `.mcs/bin/mcs status` | List plans, regenerate `Docs/Plans/index.md` |
| `.mcs/bin/mcs check` | Is the setup current, did the guard log errors |

On Windows prefix `py -3`, for example `py -3 .mcs\bin\mcs status`.

### Update or remove

Update: `git submodule update --remote .mcs`, rerun setup, commit.
`mcs check` says when setup is outdated.

Remove: `.mcs/uninstall.sh` (or `uninstall.ps1`) removes exactly what setup
wrote, including the plugins. The `.mcs` submodule itself stays; remove it
with `git rm .mcs`.

### What setup writes

| File | Content |
|---|---|
| `CLAUDE.md` | Import block for `AGENTS.md` and `rules/` (own content stays) |
| `.claude/settings.json` | `mcs` marketplace, team plugins, guard hook, deny rules, autocompact 70 |
| Claude Code plugin cache | The 12 default plugins, installed with `claude plugin install --scope project` |
| `.jcode/prompt-overlay.md` | The rules inlined, because Jcode does not expand `@` imports |
| `.jcode/skills/mcs-plan/` | Planning skill for Jcode |
| `.gitattributes`, `.gitignore` | LF for plans, ignore `.mcs-guard.log` |
| `~/.jcode/config.toml` | `[hooks] pre_tool` dispatcher, once per machine; a previous hook keeps running |

`--no-plugins` skips the plugin install and removal.

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
