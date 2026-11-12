#!/usr/bin/env bash
# One-click wrapper around scripts/setup.py.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$HERE/setup.py" "$@"
