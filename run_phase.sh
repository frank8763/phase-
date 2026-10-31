#!/usr/bin/env bash
set -euo pipefail
PHASE_REPO="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ $# -eq 0 ]]; then
  exec python3 "$PHASE_REPO/tools/verify.py"
fi
if [[ -f "$PHASE_REPO/REVIEW_PENDING" ]]; then
  echo 'PAUSED_PENDING_USER_REVIEW: migration is complete; experiments require the user to continue after review.' >&2
  exit 2
fi
exec python3 "$PHASE_REPO/tools/isolate.py" --run "$@"

