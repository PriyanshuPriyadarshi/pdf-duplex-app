#!/usr/bin/env bash
# ==============================================================================
# PDF Duplex & Booklet Studio - One-Line Uninstaller
# ==============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/uninstall.sh | bash
#   Or locally: ./uninstall.sh
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [ -f "${SCRIPT_DIR}/install.sh" ]; then
    exec bash "${SCRIPT_DIR}/install.sh" --uninstall "$@"
else
    # Running piped through curl
    curl -fsSL "https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/install.sh" | bash -s -- --uninstall "$@"
fi
