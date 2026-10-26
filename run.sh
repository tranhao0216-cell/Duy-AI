#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if command -v python3.14 >/dev/null 2>&1; then
    exec python3.14 launcher.py
fi
exec python3 launcher.py
