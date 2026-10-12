#!/usr/bin/env python3
"""Machine-wide Jcode pre_tool dispatcher for MCS projects.

Installed by setup as ~/.jcode/hooks/mcs-dispatch.py and set as
[hooks] pre_tool in ~/.jcode/config.toml. Project-independent: it walks up
from JCODE_HOOK_CWD to the nearest .mcs/guard/guard.py and runs it in-process.
Outside MCS projects it allows everything.

A pre_tool value that existed before setup is kept in mcs-dispatch.json
("previous") and runs first; its block (exit 2) is passed through.
"""

import importlib.util
import io
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

STATE = Path(__file__).with_name("mcs-dispatch.json")


def find_guard(start):
    try:
        p = Path(start).resolve()
    except OSError:
        return None
    for d in (p, *p.parents):
        candidate = d / ".mcs" / "guard" / "guard.py"
        if candidate.is_file():
            return candidate
    return None


def run_previous(raw):
    try:
        previous = json.loads(STATE.read_text(encoding="utf-8")).get("previous") or ""
    except (OSError, ValueError):
        return 0
    if not previous:
        return 0
    try:
        args = shlex.split(previous)
        if args and args[0].startswith("~/"):
            args[0] = str(Path.home() / args[0][2:])
        out = subprocess.run(args, input=raw, text=True, capture_output=True, timeout=4)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0
    if out.returncode == 2:
        sys.stderr.write(out.stderr)
        return 2
    return 0


def main():
    raw = sys.stdin.read()
    if run_previous(raw) == 2:
        return 2
    guard = find_guard(os.environ.get("JCODE_HOOK_CWD") or os.getcwd())
    if guard is None:
        return 0
    try:
        spec = importlib.util.spec_from_file_location("mcs_guard", guard)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.stdin = io.StringIO(raw)
        return module.main(["--agent", "jcode"])
    except Exception:  # noqa: BLE001 - a broken checkout must not stop all work
        return 0


if __name__ == "__main__":
    sys.exit(main())
