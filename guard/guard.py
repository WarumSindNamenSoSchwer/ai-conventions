#!/usr/bin/env python3
"""MCS guard: one entry point for every agent hook.

Usage:
    guard.py --agent claude-code   (PreToolUse hook, JSON on stdin)
    guard.py --agent jcode         (pre_tool hook, JCODE_HOOK_* env + stdin)

See contract.md. Standard library only, Python 3.10+.
"""

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rules_flash  # noqa: E402
import rules_git  # noqa: E402
import rules_plan  # noqa: E402

RULES = (rules_flash.check, rules_git.check, rules_plan.check)

SHELL_TOOLS = {"bash", "powershell", "shell"}
EDIT_TOOLS = {"edit", "multiedit", "write", "notebookedit", "replace", "apply_patch", "patch"}


@dataclass
class Call:
    kind: str
    cwd: str
    root: str
    command: str = ""
    path: str = ""
    content: str = ""
    extra_paths: list = field(default_factory=list)

    def rel(self, path):
        return to_rel(path, self.cwd, self.root)


def find_root(start):
    """Project root: nearest directory upward with .git or .mcs."""
    p = Path(start).resolve()
    for d in (p, *p.parents):
        if (d / ".git").exists() or (d / ".mcs").exists():
            return str(d)
    return str(p)


def to_rel(path, cwd, root):
    """Normalize to a root-relative POSIX path. Handles Windows separators."""
    if not path:
        return ""
    raw = str(path).strip().strip("'\"")
    if "\\" in raw or (len(raw) > 1 and raw[1] == ":"):
        raw = PureWindowsPath(raw).as_posix()
    pp = PurePosixPath(raw)
    root_p = PurePosixPath(Path(root).resolve().as_posix())
    if not pp.is_absolute() and not (len(raw) > 1 and raw[1] == ":"):
        cwd_p = PurePosixPath(Path(cwd).resolve().as_posix())
        pp = cwd_p / pp
    try:
        parts = []
        for part in pp.parts:
            if part == "..":
                if parts:
                    parts.pop()
            elif part != ".":
                parts.append(part)
        pp = PurePosixPath(*parts) if parts else pp
        if os.name == "nt":
            pp = PurePosixPath(pp.as_posix().lower())
            root_p = PurePosixPath(root_p.as_posix().lower())
        return pp.relative_to(root_p).as_posix()
    except ValueError:
        resolved = Path(raw)
        try:
            return PurePosixPath(resolved.resolve().as_posix()).relative_to(root_p).as_posix()
        except (ValueError, OSError):
            return "../" + pp.as_posix().lstrip("/")


def _edit_content(tool_input):
    if "content" in tool_input:
        return str(tool_input.get("content") or "")
    if "new_string" in tool_input:
        return str(tool_input.get("new_string") or "")
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        return "\n".join(str(e.get("new_string", "")) for e in edits if isinstance(e, dict))
    if "patch" in tool_input or "patch_text" in tool_input:
        return str(tool_input.get("patch") or tool_input.get("patch_text") or "")
    return ""


def _patch_paths(text):
    paths = []
    for line in text.splitlines():
        for prefix in ("*** Update File: ", "*** Add File: ", "+++ b/", "--- a/"):
            if line.startswith(prefix):
                paths.append(line[len(prefix):].strip())
    return paths


def normalize(agent, raw, env):
    data = json.loads(raw) if raw.strip() else {}
    if agent == "claude-code":
        tool = str(data.get("tool_name", ""))
        tool_input = data.get("tool_input") or {}
        cwd = data.get("cwd") or os.getcwd()
    else:
        tool = env.get("JCODE_HOOK_TOOL_NAME", "")
        tool_input = data
        cwd = env.get("JCODE_HOOK_CWD") or os.getcwd()
    root = find_root(cwd)
    name = tool.lower()
    if name in SHELL_TOOLS:
        return Call(kind="shell", cwd=cwd, root=root, command=str(tool_input.get("command", "")))
    if name in EDIT_TOOLS:
        content = _edit_content(tool_input)
        path = tool_input.get("file_path") or tool_input.get("path") or tool_input.get("notebook_path") or ""
        extra = _patch_paths(content) if name in ("apply_patch", "patch") else []
        if not path and extra:
            path, extra = extra[0], extra[1:]
        call = Call(kind="edit", cwd=cwd, root=root, content=content)
        call.path = call.rel(path)
        call.extra_paths = [call.rel(p) for p in extra]
        return call
    return Call(kind="other", cwd=cwd, root=root)


def decide(call):
    calls = [call]
    for extra in call.extra_paths:
        calls.append(Call(kind="edit", cwd=call.cwd, root=call.root, path=extra, content=call.content))
    for c in calls:
        for rule in RULES:
            reason = rule(c)
            if reason:
                return reason
    return None


def _log_error(cwd):
    try:
        root = Path(find_root(cwd or os.getcwd()))
        with open(root / ".mcs-guard.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%S ") + traceback.format_exc().replace("\n", " | ") + "\n")
    except OSError:
        pass


def main(argv):
    agent = "jcode"
    if "--agent" in argv:
        agent = argv[argv.index("--agent") + 1]
    raw = sys.stdin.read()
    cwd = os.environ.get("JCODE_HOOK_CWD", "")
    try:
        call = normalize(agent, raw, os.environ)
        cwd = call.cwd
        reason = decide(call)
    except Exception:  # noqa: BLE001 - never let a guard bug block all work
        _log_error(cwd)
        return 0
    if not reason:
        return 0
    message = f"[mcs guard] {reason}"
    if agent == "claude-code":
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }}))
        return 0
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
