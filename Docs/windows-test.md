# Windows test guide (version 1)

For Muri, then Gregor. Goal: confirm on a real Windows PC what was only tested
on macOS. Every step names the expected result. Note anything that differs in
the pull request.

## 0. Prerequisites

Open **PowerShell** (not as administrator):

```powershell
winget install Git.Git Python.Python.3.12 OpenJS.NodeJS.LTS LLVM.LLVM
```

Close and reopen PowerShell, then check:

```powershell
git --version; py -3 --version; node --version; clang-format --version; bash --version
```

Expected: every command prints a version. `bash` comes with Git for Windows;
Claude Code hooks need it. If `py` is missing but `python` works, that is fine.

Claude Code and Jcode must be installed and logged in.

## 1. Unit tests

```powershell
git clone https://github.com/WarumSindNamenSoSchwer/ai-conventions.git
cd ai-conventions
py -3 -m unittest discover -s guard
py -3 -m unittest discover -s bin -p "test_*.py"
```

Expected: `OK` for both (25 and 20 tests).

## 2. Test project

```powershell
cd $env:TEMP
git init -b main mcs-test; cd mcs-test
git commit --allow-empty -m init
git submodule add https://github.com/WarumSindNamenSoSchwer/ai-conventions.git .mcs
git commit -m "add .mcs"
powershell -ExecutionPolicy Bypass -File .mcs\setup.ps1
```

Expected: `mcs setup: done in ...`. Then:

```powershell
git status --short
py -3 .mcs\bin\mcs check
type $env:USERPROFILE\.jcode\config.toml | Select-String pre_tool
```

Expected: new files `CLAUDE.md`, `.claude/settings.json`,
`.jcode/prompt-overlay.md`, `.jcode/skills/mcs-plan/`, `.gitattributes`,
`.gitignore`; `mcs check: ok`; one `pre_tool = "...mcs-dispatch.py"` line.

Commit them: `git add -A; git commit -m "mcs setup"`.

## 3. Jcode guard

Start `jcode` in `mcs-test` and ask, one at a time:

| Ask the agent to | Expected |
|---|---|
| run `git push origin main` | blocked, message starts with `[mcs guard] git:` |
| run `.\Scripts\flash.ps1` | blocked, `[mcs guard] flash:` |
| create `src\a.c` with any content | blocked, `[mcs guard] plan:` (no approved plan) |
| run `py -3 .mcs\bin\mcs approve x` | blocked, `[mcs guard] plan: only a human approves plans` |
| run `git status` | runs normally |

## 4. Claude Code guard

Setup in step 2 already ran `claude plugin install ... --scope project` for
the 12 default plugins (it takes about a minute and prints the commands if
`claude` is not on PATH). Start `claude` in `mcs-test` and trust the folder
when asked. Check `/plugin`: the plugins from the `mcs` marketplace are
installed and enabled, no errors for `archify`, `thermo-nuclear`,
`clangd-lsp`. Then repeat the table from step 3. Expected: same blocks, shown
as a hook denial with the `[mcs guard]` reason.

## 5. Plan approval

In PowerShell (your own terminal, not the agent):

```powershell
git checkout -b feature/x
```

Ask either agent: "Use the mcs-plan skill to plan adding an empty file
src/a.c." Let it write `Docs/Plans/<name>.md`. Then:

```powershell
py -3 .mcs\bin\mcs approve <name>
```

Expected: it asks you to type the plan name; after that `approved: ...`.
Ask the agent again to create `src\a.c`: now allowed.

Also try in **Windows Terminal** and in the **VS Code terminal**: typing the
plan name must work in both.

Edit one character in the plan body, then ask the agent to edit `src\a.c`
again. Expected: blocked again (plan changed after approval).
`py -3 .mcs\bin\mcs status` shows `changed after approval`.

## 6. Line endings

```powershell
git config core.autocrlf
git add -A; git commit -m "plan"; git checkout main; git checkout feature/x
```

Expected: the agent can still edit `src\a.c` after the checkout (the plan
keeps LF, so the approval hash still matches).

## 7. Uninstall

Make a second project `mcs-test2` the same way (step 2), then in `mcs-test`:

```powershell
git checkout main
powershell -ExecutionPolicy Bypass -File .mcs\uninstall.ps1
git status --short
```

Expected: `Jcode dispatcher kept: still used by 1 project(s)`; `git status`
shows the setup files as deleted or reverted (they were committed in step 2).

In `mcs-test2` run uninstall too. Expected: `Jcode dispatcher removed`, and
`%USERPROFILE%\.jcode\config.toml` is exactly as before step 2.

## Report

In the pull request: Windows version, PowerShell version, which steps passed,
and the exact output of any step that did not.
