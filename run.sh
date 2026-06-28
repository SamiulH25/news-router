#!/usr/bin/env bash
# News Router — start the full site with one command.
set -euo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" == "--docker" ]]; then
  npm run start:prod
else
  npm run start:dev
fi
