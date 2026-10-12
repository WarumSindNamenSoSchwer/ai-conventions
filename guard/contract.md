# Guard contract

`guard.py` receives one tool call from an agent adapter, normalizes it into a
`Call`, runs every rule, and answers allow or block.

## Normalized call

| Field | Meaning |
|---|---|
| `kind` | `shell`, `edit`, or `other` |
| `command` | shell command string (`shell` only) |
| `path` | target file, repository-relative with forward slashes (`edit` only) |
| `content` | new text written by the edit, when the agent sends it |
| `cwd` | directory the agent runs in |

## Tool-name mapping

| Normalized | Claude Code `tool_name` | Jcode `JCODE_HOOK_TOOL_NAME` |
|---|---|---|
| shell | `Bash`, `PowerShell` | `bash` |
| edit | `Edit`, `MultiEdit`, `Write`, `NotebookEdit` | `edit`, `write`, `replace`, `apply_patch` |

Any other tool is `other` and always allowed.

Claude Code sends `{"tool_name", "tool_input": {"command" | "file_path",
"content" | "new_string" | "edits"}, "cwd"}` on stdin. Jcode sends the tool
input JSON on stdin and the tool name in `JCODE_HOOK_TOOL_NAME`, the working
directory in `JCODE_HOOK_CWD`. Verified live for Jcode on 2026-10-12:
`bash` with `command`; `write` and `edit` with a relative `file_path`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | allow |
| 2 | block; the reason is on stderr (Jcode) or in the JSON decision (Claude Code) |

For Claude Code, `guard.py --agent claude-code` prints
`{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision":
"deny", "permissionDecisionReason": "..."}}` and exits 0 when blocking, as the
Claude Code hook protocol expects.

## Failure behaviour

Any internal error is caught, written to `.mcs-guard.log` in the project
root, and turned into allow. A guard bug must never stop all work silently;
`mcs check` reports logged errors.

## Limits

The guard stops accidental actions, not deliberate circumvention. Commands
built from variables, aliases or scripts generated at runtime are not seen.
