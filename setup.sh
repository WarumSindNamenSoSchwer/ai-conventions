#!/usr/bin/env bash
# Connect this project to the MCS conventions (macOS, Linux).
# Run from the project root: .mcs/setup.sh
# Checks prerequisites, then hands over to `mcs setup` (Python).
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

py=""
for p in python3 python; do
    if "$p" -c "import sys; sys.exit(sys.version_info < (3, 10))" >/dev/null 2>&1; then
        py="$p"; break
    fi
done
if [ -z "$py" ]; then
    echo "setup: Python 3.10 or newer is required (macOS: brew install python)." >&2
    exit 1
fi

missing=0
for tool in git node clang-format; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "setup: '$tool' not found on PATH." >&2
        missing=1
    fi
done
if [ "$missing" -ne 0 ]; then
    echo "setup: install the missing tools (macOS: brew install git node clang-format) and rerun." >&2
    exit 1
fi

exec "$py" "$here/bin/mcs" setup "$@"
