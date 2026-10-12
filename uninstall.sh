#!/usr/bin/env bash
# Remove what setup.sh wrote into this project (macOS, Linux).
# The machine-wide Jcode dispatcher is removed only when no other project uses it.
set -u
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for p in python3 python; do
    if "$p" -c "import sys; sys.exit(sys.version_info < (3, 10))" >/dev/null 2>&1; then
        exec "$p" "$here/bin/mcs" uninstall "$@"
    fi
done
echo "uninstall: Python 3.10 or newer is required." >&2
exit 1
