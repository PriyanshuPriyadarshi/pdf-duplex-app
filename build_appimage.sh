#!/bin/bash
set -e

WORKDIR=$(pwd)
APPDIR="$WORKDIR/AppDir"
APPIMAGE_NAME="PDFDuplexPrinter"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building AppImage for PDF Duplex/Booklet Printer${NC}"

# Clean previous build
echo -e "${YELLOW}Cleaning previous build...${NC}"
rm -rf "$APPDIR"
rm -f linuxdeploy linuxdeploy-plugin-qt appimagetool *.AppImage

# Create AppDir structure
echo -e "${YELLOW}Creating AppDir structure...${NC}"
mkdir -p "$APPDIR"/{usr/bin,usr/lib,usr/share/{applications,icons/hicolor/256x256/apps,metainfo}}

# Create a virtual environment inside AppDir
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv "$APPDIR/venv"
source "$APPDIR/venv/bin/activate"

# Upgrade pip and install the package with dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install .

# Create .desktop file
echo -e "${YELLOW}Creating .desktop file...${NC}"
cat > "$APPDIR/usr/share/applications/pdf-duplex-app.desktop" <<EOF
[Desktop Entry]
Name=PDF Duplex/Booklet Printer
Comment=A Python/PyQt6 GUI application for manual duplex and booklet printing on Linux
Exec=pdf-duplex-app
Icon=pdf-duplex-app
Terminal=false
Type=Application
Categories=Office;Printing;
StartupNotify=true
MimeType=application/pdf;
EOF

# Create a simple SVG icon (placeholder - replace with actual icon if available)
echo -e "${YELLOW}Creating application icon...${NC}"
cat > "$APPDIR/usr/share/icons/hicolor/256x256/apps/pdf-duplex-app.svg" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="32" fill="#2196F3"/>
  <text x="128" y="170" font-family="Arial, sans-serif" font-size="100" font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="middle">PDF</text>
  <rect x="48" y="180" width="160" height="24" rx="4" fill="rgba(255,255,255,0.3)"/>
  <rect x="48" y="180" width="80" height="24" rx="4" fill="#FF9800"/>
</svg>
EOF

# Also copy as default icon
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/pdf-duplex-app.svg" "$APPDIR/pdf-duplex-app.svg"

# Copy Qt plugins, QML, and translations for PyQt6 (linuxdeploy doesn't do this for Python apps)
echo -e "${YELLOW}Copying Qt plugins and resources...${NC}"
QT_SOURCE="$APPDIR/venv/lib/python3.11/site-packages/PyQt6/Qt6"
if [ -d "$QT_SOURCE/plugins" ]; then
    cp -r "$QT_SOURCE/plugins" "$APPDIR/usr/lib/qt6/plugins"
fi
if [ -d "$QT_SOURCE/qml" ]; then
    cp -r "$QT_SOURCE/qml" "$APPDIR/usr/lib/qt6/qml"
fi
if [ -d "$QT_SOURCE/translations" ]; then
    cp -r "$QT_SOURCE/translations" "$APPDIR/usr/lib/qt6/translations"
fi

# Create AppRun script
echo -e "${YELLOW}Creating AppRun script...${NC}"
cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/bash
# AppRun entry point for the AppImage

SELF=$(readlink -f "$0")
HERE=${SELF%/*}

# Set up environment
export PATH="$HERE/venv/bin:$PATH"
export PYTHONPATH="$HERE/venv/lib/python3.11/site-packages:$PYTHONPATH"
export QT_QPA_PLATFORM=xcb

# Ensure we can find Qt plugins
export QT_PLUGIN_PATH="$HERE/usr/lib/qt6/plugins:$HERE/venv/lib/python3.11/site-packages/PyQt6/Qt6/plugins:$QT_PLUGIN_PATH"
export QML2_IMPORT_PATH="$HERE/usr/lib/qt6/qml:$QML2_IMPORT_PATH"
export QT_TRANSLATIONS_PATH="$HERE/usr/lib/qt6/translations:$QT_TRANSLATIONS_PATH"

# Run the application
exec pdf-duplex-app "$@"
EOF
chmod +x "$APPDIR/AppRun"

# Create a symlink for the icon at the AppDir root (required by linuxdeploy)
ln -sf usr/share/icons/hicolor/256x256/apps/pdf-duplex-app.svg "$APPDIR/pdf-duplex-app.svg"

# Create metainfo file (AppStream)
echo -e "${YELLOW}Creating AppStream metainfo...${NC}"
cat > "$APPDIR/usr/share/metainfo/pdf-duplex-app.metainfo.xml" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>pdf-duplex-app</id>
  <name>PDF Duplex/Booklet Printer</name>
  <summary>A Python/PyQt6 GUI application for manual duplex and booklet printing on Linux</summary>
  <description>
    <p>PDF Duplex/Booklet Printer is a GUI application for printing PDFs in various modes:
    Normal, Manual Duplex (flip and reinsert), and Booklet (2 pages per sheet for folding).</p>
    <p>Features:</p>
    <ul>
      <li>Load and preview PDF files</li>
      <li>Manual duplex printing workflow with flip prompt</li>
      <li>Booklet imposition for folded printing</li>
      <li>CUPS integration via lp command</li>
      <li>High-quality Qt PDF preview</li>
    </ul>
  </description>
  <project_license>MIT</project_license>
  <categories>
    <category>Office</category>
    <category>Printing</category>
  </categories>
  <keywords>
    <keyword>PDF</keyword>
    <keyword>printing</keyword>
    <keyword>duplex</keyword>
    <keyword>booklet</keyword>
  </keywords>
  <url type="homepage">https://github.com/your-username/pdf-duplex-app</url>
  <url type="bugtracker">https://github.com/your-username/pdf-duplex-app/issues</url>
  <icon type="stock">pdf-duplex-app</icon>
  <provides>
    <binary>pdf-duplex-app</binary>
  </provides>
  <screenshots>
  </screenshots>
</component>
EOF

# Download linuxdeploy
echo -e "${YELLOW}Downloading linuxdeploy...${NC}"
wget -q https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage
mv linuxdeploy-x86_64.AppImage linuxdeploy

# Download linuxdeploy-plugin-qt
echo -e "${YELLOW}Downloading linuxdeploy-plugin-qt...${NC}"
wget -q https://github.com/linuxdeploy/linuxdeploy-plugin-qt/releases/download/continuous/linuxdeploy-plugin-qt-x86_64.AppImage
chmod +x linuxdeploy-plugin-qt-x86_64.AppImage
mv linuxdeploy-plugin-qt-x86_64.AppImage linuxdeploy-plugin-qt

# Download appimagetool
echo -e "${YELLOW}Downloading appimagetool...${NC}"
wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
mv appimagetool-x86_64.AppImage appimagetool

# Run linuxdeploy to prepare the AppDir (no output plugin, just prepares the AppDir)
echo -e "${YELLOW}Running linuxdeploy to prepare AppDir...${NC}"
./linuxdeploy --appdir "$APPDIR"

# Run appimagetool explicitly with proper naming
echo -e "${YELLOW}Running appimagetool to create AppImage...${NC}"
VERSION="${VERSION:-0.1.0}"
APPIMAGE_OUTPUT="${APPIMAGE_NAME}-${VERSION}-x86_64.AppImage"
./appimagetool "$APPDIR" "$WORKDIR/$APPIMAGE_OUTPUT"

# Move AppImage to workspace
mv "${APPIMAGE_NAME}-${VERSION:-0.1.0}-x86_64.AppImage" "$WORKDIR/"

echo -e "${GREEN}AppImage created successfully: $WORKDIR/${APPIMAGE_NAME}-${VERSION:-0.1.0}-x86_64.AppImage${NC}"
echo -e "${GREEN}Make it executable and run: chmod +x ${APPIMAGE_NAME}-*.AppImage && ./${APPIMAGE_NAME}-*.AppImage${NC}"