#!/usr/bin/env bash
# Keep the shared bugbounty-intel corpus up to date without vendoring it.
#
# Default location: ~/.apex/intel/bugbounty-intel
# Override with APEX_INTEL_CORPUS=/some/path
# Override the remote with APEX_INTEL_REPO=git@github.com:org/repo.git
set -euo pipefail

REPO="${APEX_INTEL_REPO:-git@github.com:Najnomics/bugbounty-intel.git}"
DEST="${APEX_INTEL_CORPUS:-$HOME/.apex/intel/bugbounty-intel}"

mkdir -p "$(dirname "$DEST")"

if [ -d "$DEST/.git" ]; then
  echo "Updating intel corpus: $DEST"
  git -C "$DEST" fetch --prune origin
  git -C "$DEST" pull --ff-only
else
  echo "Cloning intel corpus: $REPO -> $DEST"
  git clone --depth 1 "$REPO" "$DEST"
fi

echo
echo "Add this to the MCP server environment (or export it):"
echo "APEX_INTEL_CORPUS=$DEST"
