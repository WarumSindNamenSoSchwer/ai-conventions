#!/usr/bin/env bash
# Run a Python script with the first working Python 3.10+ on PATH.
# Used by the Claude Code hooks. Probing avoids the Windows Store "python3"
# stub; "py -3" is the Windows launcher. Git Bash ships with Git for Windows,
# so this runs on macOS, Linux and Windows. No working Python: exit 0 (allow);
# `mcs check` reports it.
probe="import sys; sys.exit(sys.version_info < (3, 10))"
for p in python3 python; do
    if "$p" -c "$probe" >/dev/null 2>&1; then
        exec "$p" "$@"
    fi
done
if py -3 -c "$probe" >/dev/null 2>&1; then
    exec py -3 "$@"
fi
exit 0
