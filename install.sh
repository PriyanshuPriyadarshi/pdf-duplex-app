#!/usr/bin/env bash
# ==============================================================================
# PDF Duplex & Booklet Studio - One-Line Installer / Uninstaller
# ==============================================================================
# Usage:
#   Install:   curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/install.sh | bash
#   Uninstall: curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/install.sh | bash -s -- --uninstall
#   Or locally: ./install.sh [--uninstall]
# ==============================================================================

set -eo pipefail

APP_NAME="pdf-duplex-app"
APP_TITLE="PDF Duplex & Booklet Studio"
REPO_URL="https://github.com/PriyanshuPriyadarshi/pdf-duplex-app.git"

INSTALL_ROOT="${HOME}/.local/share/${APP_NAME}"
BIN_DIR="${HOME}/.local/bin"
DESKTOP_DIR="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/scalable/apps"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

# --- UNINSTALL MODE ---
if [[ "$1" == "--uninstall" || "$1" == "-u" || "$1" == "uninstall" ]]; then
    echo -e "${BLUE}==>${NC} ${BOLD}Uninstalling ${APP_TITLE}...${NC}"

    rm -f "${BIN_DIR}/${APP_NAME}"
    rm -f "${DESKTOP_DIR}/${APP_NAME}.desktop"
    rm -f "${ICON_DIR}/${APP_NAME}.svg"
    rm -rf "${INSTALL_ROOT}"

    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
    fi

    echo -e "${GREEN}✓${NC} ${APP_TITLE} has been completely removed from your system."
    exit 0
fi

# --- INSTALL MODE ---
echo -e "${BLUE}================================================================${NC}"
echo -e "${BOLD}       🖨️  Installing ${APP_TITLE}${NC}"
echo -e "${BLUE}================================================================${NC}"

# 1. Check Python
PYTHON_BIN=""
for cmd in python3 python3.12 python3.13 python3.14 python3.11; do
    if command -v "$cmd" >/dev/null 2>&1; then
        if "$cmd" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}Error:${NC} Python 3.10+ is required but was not found."
    exit 1
fi

PY_VER=$("$PYTHON_BIN" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
echo -e "${GREEN}✓${NC} Found Python ${PY_VER} (${PYTHON_BIN})"

# 2. Check Directories
mkdir -p "${INSTALL_ROOT}"
mkdir -p "${BIN_DIR}"
mkdir -p "${DESKTOP_DIR}"
mkdir -p "${ICON_DIR}"

# 3. Obtain Application Source
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
APP_SRC="${INSTALL_ROOT}/app"

if [ -n "$SCRIPT_DIR" ] && [ -f "${SCRIPT_DIR}/pyproject.toml" ]; then
    echo -e "${BLUE}==>${NC} Installing from local workspace..."
    rm -rf "${APP_SRC}"
    mkdir -p "${APP_SRC}"
    # Copy project files excluding large caches and build dirs
    tar --exclude='./.git' \
        --exclude='./.venv' \
        --exclude='./venv' \
        --exclude='./AppDir' \
        --exclude='./build' \
        --exclude='./squashfs-root' \
        --exclude='__pycache__' \
        -cf - -C "${SCRIPT_DIR}" . | tar -xf - -C "${APP_SRC}"
else
    echo -e "${BLUE}==>${NC} Fetching latest release from GitHub..."
    rm -rf "${APP_SRC}"
    if command -v git >/dev/null 2>&1; then
        git clone --depth 1 "${REPO_URL}" "${APP_SRC}"
    else
        mkdir -p "${APP_SRC}"
        curl -fsSL "https://github.com/PriyanshuPriyadarshi/pdf-duplex-app/archive/refs/heads/main.tar.gz" | tar -xz --strip-components=1 -C "${APP_SRC}"
    fi
fi

# 4. Create Virtual Environment & Install Dependencies
echo -e "${BLUE}==>${NC} Setting up isolated environment..."
VENV_DIR="${INSTALL_ROOT}/venv"
rm -rf "${VENV_DIR}"

if command -v uv >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Using Astral uv for ultra-fast installation..."
    uv venv --clear "${VENV_DIR}" --python "$PYTHON_BIN"
    uv pip install --python "${VENV_DIR}/bin/python" -e "${APP_SRC}"
else
    "$PYTHON_BIN" -m venv --clear "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade pip
    "${VENV_DIR}/bin/pip" install "${APP_SRC}"
fi

# 5. Create Executable Launcher
echo -e "${BLUE}==>${NC} Creating command-line launcher at ${BIN_DIR}/${APP_NAME}..."
cat > "${BIN_DIR}/${APP_NAME}" <<EOF
#!/usr/bin/env bash
exec "${VENV_DIR}/bin/python3" -m src.main_window "\$@"
EOF
chmod +x "${BIN_DIR}/${APP_NAME}"

# 6. Install Application Icon
if [ -f "${APP_SRC}/assets/pdf-duplex-app.svg" ]; then
    cp "${APP_SRC}/assets/pdf-duplex-app.svg" "${ICON_DIR}/${APP_NAME}.svg"
elif [ -f "${APP_SRC}/AppDir/pdf-duplex-app.svg" ]; then
    cp "${APP_SRC}/AppDir/pdf-duplex-app.svg" "${ICON_DIR}/${APP_NAME}.svg"
fi

# 7. Create Desktop Entry
echo -e "${BLUE}==>${NC} Registering application in desktop menu..."
cat > "${DESKTOP_DIR}/${APP_NAME}.desktop" <<EOF
[Desktop Entry]
Name=${APP_TITLE}
Comment=Manual duplex and booklet printing workstation with ink-saver inversion
Exec=${BIN_DIR}/${APP_NAME} %f
Icon=${APP_NAME}
Terminal=false
Type=Application
Categories=Office;Printing;Publishing;
MimeType=application/pdf;
StartupNotify=true
Keywords=PDF;printing;duplex;booklet;imposition;
EOF
chmod +x "${DESKTOP_DIR}/${APP_NAME}.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${DESKTOP_DIR}" 2>/dev/null || true
fi

echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}${BOLD}✓ Installation Complete!${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo -e "You can launch the app in two ways:"
echo -e "  1. Launch from your desktop application launcher (search for ${BOLD}${APP_TITLE}${NC})"
echo -e "  2. Type ${BOLD}${APP_NAME}${NC} in any terminal"
echo ""

# Check PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    echo -e "${YELLOW}Notice:${NC} ${BIN_DIR} is not in your current PATH."
    echo -e "Add it to your shell configuration (e.g. ~/.bashrc or ~/.zshrc):"
    echo -e "    ${BOLD}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo ""
fi
echo -e "To uninstall anytime, run:"
echo -e "  ${BOLD}curl -fsSL https://raw.githubusercontent.com/PriyanshuPriyadarshi/pdf-duplex-app/main/install.sh | bash -s -- --uninstall${NC}"
echo ""
