#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
echo 'Mở http://127.0.0.1:5000 trong trình duyệt.'
exec .venv/bin/python app.py
