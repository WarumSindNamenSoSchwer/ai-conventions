#!/usr/bin/env bash
# Claude Code PreToolUse hook: run guard.py with the first working Python 3.10+.
# Probing avoids the Windows Store "python3" stub. Git Bash ships with Git for
# Windows, so this script runs on macOS, Linux and Windows.
# No working Python: exit 0 (allow); `mcs check` reports the missing Python.
guard="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/guard/guard.py"
for p in python3 python py; do
    if "$p" -c "import sys; sys.exit(sys.version_info < (3, 10))" >/dev/null 2>&1; then
        exec "$p" "$guard" --agent claude-code
    fi
done
exit 0
