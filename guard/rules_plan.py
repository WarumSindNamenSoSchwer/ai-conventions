"""Plan rule: code edits need an approved plan; agents never approve plans."""

import re

import plans
from rules_git import current_branch

CODE_SUFFIXES = {
    ".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".inc", ".ino",
    ".s", ".asm", ".ld",
    ".py", ".dart", ".go", ".rs", ".js", ".jsx", ".ts", ".tsx", ".svelte",
    ".kt", ".kts", ".swift", ".java", ".m", ".mm",
    ".proto", ".sql", ".sh", ".ps1", ".bat", ".cmd",
}
APPROVE_CMD = re.compile(r"(^|[\s/\\\"'])mcs(\.py|\.cmd|\.ps1)?[\"']?\s+approve\b", re.I)
SHELL_WRITE_TARGETS = [
    re.compile(r">>?\s*([^\s|;&<>]+)"),
    re.compile(r"\btee\s+(?:-a\s+)?([^\s|;&<>]+)"),
    re.compile(r"\bsed\s+(?:-[a-zA-Z]*i[a-zA-Z]*|--in-place)\S*\s+(?:'[^']*'|\"[^\"]*\"|\S+)\s+([^\s|;&<>]+)"),
]
APPROVED_TEXT = re.compile(r"status:\s*approved", re.I)


def is_code_path(path):
    if not path:
        return False
    p = path.lower()
    if p.startswith("/tmp/") or p.startswith("/dev/") or p.startswith("../"):
        return False
    if p.startswith("docs/") or p.startswith(".mcs/"):
        return False
    dot = p.rfind(".")
    return dot >= 0 and p[dot:] in CODE_SUFFIXES


def is_plan_path(path):
    return bool(path) and path.lower().startswith("docs/plans/") and path.lower().endswith(".md")


def _shell_write_targets(command, rel):
    out = []
    for pattern in SHELL_WRITE_TARGETS:
        for m in pattern.finditer(command):
            target = m.group(1).strip("'\"")
            if target in ("/dev/null", "&1", "&2") or target.startswith("&"):
                continue
            out.append(rel(target))
    return out


def check(call):
    if call.kind == "shell" and call.command:
        if APPROVE_CMD.search(call.command):
            return "plan: only a human approves plans. Run 'mcs approve' yourself in a terminal."
        targets = _shell_write_targets(call.command, call.rel)
        if any(is_plan_path(t) for t in targets) and APPROVED_TEXT.search(call.command):
            return "plan: agents never set 'status: approved'. A human runs 'mcs approve'."
        code_targets = [t for t in targets if is_code_path(t)]
        if code_targets:
            return _require_plan(call, code_targets[0])
        return None
    if call.kind == "edit" and call.path:
        if is_plan_path(call.path) and call.content and APPROVED_TEXT.search(call.content):
            return "plan: agents never set 'status: approved'. A human runs 'mcs approve'."
        if is_code_path(call.path):
            return _require_plan(call, call.path)
    return None


def _require_plan(call, target):
    branch = current_branch(call.cwd)
    if plans.approved_plan_for(call.root, branch):
        return None
    return (f"plan: '{target}' is code and branch '{branch or '?'}' has no approved plan in "
            "Docs/Plans/. Write the plan with the mcs-plan skill and ask a human to run "
            "'mcs approve <plan>'.")
