"""Git rule: no push to main, develop or release/*; no self-merge."""

import re
import shlex
import subprocess

PROTECTED = re.compile(r"^(main|develop|release/.+)$")
PUSH_VALUE_OPTIONS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}


def _git(cwd, *args):
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=2)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def current_branch(cwd):
    return _git(cwd, "symbolic-ref", "--short", "-q", "HEAD")


def _upstream_branch(cwd):
    up = _git(cwd, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    return up.split("/", 1)[1] if "/" in up else ""


def _split_segments(command):
    return [s for s in re.split(r"&&|\|\||;|\n", command) if s.strip()]


def _tokens(segment):
    try:
        return shlex.split(segment.replace("\\", "/"), posix=True)
    except ValueError:
        return segment.split()


def _git_subcommand(tokens):
    """Return (subcommand, args) for 'git [-C x] [-c k=v] sub args...'."""
    if not tokens or not re.search(r"(^|/)git(\.exe)?$", tokens[0]):
        return None, []
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
    if i >= len(tokens):
        return None, []
    return tokens[i], tokens[i + 1:]


def push_targets(args, cwd):
    """Resolve the remote branches a 'git push' would update."""
    if "--all" in args or "--mirror" in args:
        return ["<all branches>"]
    positional = []
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in PUSH_VALUE_OPTIONS:
            skip = True
            continue
        if a.startswith("-"):
            continue
        positional.append(a)
    refspecs = positional[1:]
    if not refspecs:
        branch = current_branch(cwd)
        targets = [branch] if branch else []
        up = _upstream_branch(cwd)
        if up:
            targets.append(up)
        return targets
    targets = []
    for spec in refspecs:
        spec = spec.lstrip("+")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        if dst in ("HEAD", "@"):
            dst = current_branch(cwd)
        targets.append(dst.replace("refs/heads/", "", 1))
    return targets


def check(call):
    if call.kind != "shell" or not call.command:
        return None
    for seg in _split_segments(call.command):
        tokens = _tokens(seg.strip())
        if (len(tokens) >= 3 and re.search(r"(^|/)gh(\.exe)?$", tokens[0], re.I)
                and tokens[1] == "pr" and tokens[2] == "merge"):
            return "git: never merge pull requests yourself. A human reviewer merges."
        sub, args = _git_subcommand(tokens)
        if sub == "push":
            if "--tags" in args and len([a for a in args if not a.startswith("-")]) <= 1:
                continue  # tags only, no branch is updated
            for target in push_targets(args, call.cwd):
                if target == "<all branches>" or PROTECTED.match(target or ""):
                    return (f"git: push to protected branch '{target}' is blocked. Push a "
                            "feature/ or fix/ branch and open a pull request.")
        if sub == "rebase":
            if PROTECTED.match(current_branch(call.cwd) or ""):
                return "git: rebasing a protected branch rewrites shared history and is blocked."
    return None
